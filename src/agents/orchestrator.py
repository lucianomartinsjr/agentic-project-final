import asyncio
import json
import logging
import os
from dotenv import load_dotenv

import google.generativeai as genai

from src.agents.auditor import AuditorAgent
from src.agents.compliance import ComplianceAgent
from src.agents.issuer import IssuerAgent

from src.tools.ml_tools import predict_credit_risk
from src.tools.utils import calculate_dti
from src.tools.db_tools import setup_database, log_application_attempt

load_dotenv()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class CreditSystemOrchestrator:
    def __init__(self):
        self.auditor = AuditorAgent()
        self.compliance = ComplianceAgent()
        self.issuer = IssuerAgent()
        
        setup_database()
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        self.genai_enabled = bool(api_key)
        if self.genai_enabled:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        else:
            self.model = None

    async def _run_genai_orchestration(self, user_request, tools_list, tools_map, system_instruction):
        if not self.model:
            return None

        try:
            chat = self.model.start_chat(history=[])

            prompt_parts = [
                system_instruction,
                f"Request Data: {json.dumps(user_request, default=str)}",
            ]

            try:
                response = await chat.send_message_async(prompt_parts, tools=tools_list)
            except Exception as e:
                logger.warning(f"Initial GenAI call failed: {e}")
                return None

            for _ in range(12):
                if not response.parts:
                    break

                part = response.parts[0]
                if not part.function_call:
                    break

                fc = part.function_call
                name = fc.name
                args = {k: v for k, v in fc.args.items()}

                func = tools_map.get(name)
                if not func:
                    return {"status": "ERRO", "mensagem": f"Tool {name} not found"}

                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(**args)
                    else:
                        result = func(**args)
                except Exception as e:
                    result = {"status": "ERROR", "message": str(e)}

                if name == "issue_contract":
                    if "final_response" in result:
                        return result["final_response"]
                    return result

                if name == "deny_request":
                    return result

                try:
                    response = await chat.send_message_async(
                        genai.protos.Content(
                            parts=[
                                genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=name,
                                        response={"result": result},
                                    )
                                )
                            ]
                        )
                    )
                except Exception as e:
                    logger.warning(f"GenAI function response failed: {e}")
                    return None

        except Exception:
            logger.exception("GenAI orchestration failed")

        return None
        
    async def handle_request(self, user_request):
        current_context = user_request.copy()
        
        def check_audit(cpf: str):
            current_context['cpf'] = cpf
            res = self.auditor.process(current_context)
            if res['success']:
                current_context.update(res['data'])
                return {"status": "OK", "data": res['data']}
            else:
                return {"status": "ERROR", "message": res['message'], "details": res.get("details")}

        def check_compliance(cpf: str, age: int, score: int):
            current_context.update({"cpf": cpf, "age": age, "score": score})
            res = self.compliance.process(current_context)
            if res['success']:
                return {"status": "OK", "message": res['message']}
            else:
                return {"status": "ERROR", "message": res['message'], "details": res.get("details")}
        
        def analyze_risk(age: int, income: float, loan_amount: float, duration: int, score: int, purpose: str, sex: str, housing: str, saving_accounts: str, checking_account: str, job: int):
            current_context.update({
                "age": age, "income": income, "loan_amount": loan_amount, 
                "duration": duration, "score": score, "purpose": purpose,
                "sex": sex, "housing": housing, "saving_accounts": saving_accounts,
                "checking_account": checking_account, "job": job
            })
            
            try:
                ml_res = predict_credit_risk(
                    age=age, income=income, loan_amount=loan_amount, duration=duration, history_score=score,
                    purpose=purpose, sex=sex, housing=housing, saving_accounts=saving_accounts, 
                    checking_account=checking_account, job=job
                )
                
                dti = calculate_dti(income, loan_amount)
                
                ml_status = ml_res.get("status")
                risk_prediction = ml_res.get("risk_prediction")
                risk_probability = ml_res.get("risk_probability")
                
                is_high_risk = ml_status == "HIGH_RISK"
                is_high_dti = dti > 20.0 
                
                current_context["ml_risk"] = {
                    "risk_prediction": risk_prediction,
                    "risk_probability": risk_probability,
                    "status": ml_status,
                }
                
                details = {
                    "ml_prob": risk_probability,
                    "dti_ratio": dti,
                    "risk_prediction": risk_prediction,
                    "risk_probability": risk_probability,
                    "status": ml_status
                }
                
                if is_high_risk or is_high_dti:
                    triggers = []
                    if is_high_risk: triggers.append(f"ML={ml_status}")
                    if is_high_dti: triggers.append(f"DTI={dti:.2f}")
                    reason = f"Risco ({'; '.join(triggers)})"
                    
                    return {"status": "HIGH_RISK", "reason": reason, "details": details}
                
                return {"status": "OK", "details": details}
                
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}

        def issue_contract(loan_amount: float, duration: int):
            current_context.update({"loan_amount": loan_amount, "duration": duration})
            res = self.issuer.process(current_context)
            return res 
            
        def deny_request(reason: str, details: dict = None):
            ml_risk = current_context.get("ml_risk")
            
            log_application_attempt(
                 cpf=current_context.get("cpf"),
                 client_id=current_context.get("id"),
                 amount=current_context.get("loan_amount"),
                 duration=current_context.get("duration"),
                 purpose=current_context.get("purpose"),
                 sex=current_context.get('sex'),
                 job=current_context.get('job'),
                 housing=current_context.get('housing'),
                 saving_accounts=current_context.get('saving_accounts'),
                 checking_account=current_context.get('checking_account'),
                 status="DENIED",
                 reason=reason
            )
            
            payload = {"status": "NEGADO", "motivo": reason}
            if details:
                payload["detalhes"] = details
            if ml_risk:
                payload["ml_risk"] = ml_risk
            
            return payload

        def validate_required_fields(data: dict):
            required = [
                "cpf",
                "age",
                "score",
                "income",
                "loan_amount",
                "duration",
                "purpose",
                "sex",
                "housing",
                "saving_accounts",
                "checking_account",
                "job",
            ]
            missing = [field for field in required if field not in data]
            if missing:
                return {
                    "status": "ERRO",
                    "mensagem": "Dados incompletos para análise",
                    "campos_faltando": missing,
                }
            return None

        tools_map = {
            "check_audit": check_audit,
            "check_compliance": check_compliance,
            "analyze_risk": analyze_risk,
            "issue_contract": issue_contract,
            "deny_request": deny_request,
        }
        
        tools_list = [check_audit, check_compliance, analyze_risk, issue_contract, deny_request]
        
        system_instruction = """
        You are the CreditSystemOrchestrator. You MUST call tools to complete the flow.
        Always follow this order:
        1) check_audit
        2) check_compliance
        3) analyze_risk
        4) issue_contract or deny_request
        
        If required data is missing, call deny_request with reason "Dados incompletos para análise" and include missing fields in details.
        Do NOT ask the user for tool results. Do NOT answer with plain text.
        """

        validation_error = validate_required_fields(user_request)
        if validation_error:
            return validation_error

        genai_result = await self._run_genai_orchestration(
            user_request=user_request,
            tools_list=tools_list,
            tools_map=tools_map,
            system_instruction=system_instruction,
        )
        if genai_result is not None:
            return genai_result

        try:
            audit_result = check_audit(user_request["cpf"])
            if audit_result["status"] != "OK":
                return deny_request(
                    reason=audit_result.get("message", "Falha na auditoria"),
                    details=audit_result.get("details"),
                )

            compliance_result = check_compliance(
                cpf=user_request["cpf"],
                age=int(user_request["age"]),
                score=int(user_request["score"]),
            )
            if compliance_result["status"] != "OK":
                return deny_request(
                    reason=compliance_result.get("message", "Falha de compliance"),
                    details=compliance_result.get("details"),
                )

            risk_result = analyze_risk(
                age=int(user_request["age"]),
                income=float(user_request["income"]),
                loan_amount=float(user_request["loan_amount"]),
                duration=int(user_request["duration"]),
                score=int(user_request["score"]),
                purpose=user_request["purpose"],
                sex=user_request["sex"],
                housing=user_request["housing"],
                saving_accounts=user_request["saving_accounts"],
                checking_account=user_request["checking_account"],
                job=int(user_request["job"]),
            )
            if risk_result["status"] != "OK":
                return deny_request(
                    reason=risk_result.get("reason", risk_result.get("message", "Falha na análise de risco")),
                    details=risk_result.get("details"),
                )

            contract_result = issue_contract(
                loan_amount=float(user_request["loan_amount"]),
                duration=int(user_request["duration"]),
            )
            if "final_response" in contract_result:
                return contract_result["final_response"]
            return contract_result

        except Exception as e:
            return {"status": "ERRO", "mensagem": "Error", "detalhes": str(e)}

        
