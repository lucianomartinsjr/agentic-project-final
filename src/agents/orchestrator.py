import os
import asyncio
import json
import logging
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai
from google.generativeai.types import content_types
from collections.abc import Iterable

from src.agents.auditor import AuditorAgent
from src.agents.compliance import ComplianceAgent
from src.agents.issuer import IssuerAgent

from src.tools.ml_tools import predict_credit_risk
from src.tools.utils import calculate_dti
from src.tools.db_tools import setup_database, log_application_attempt

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class CreditSystemOrchestrator:
    def __init__(self):
        self.auditor = AuditorAgent()
        self.compliance = ComplianceAgent()
        self.issuer = IssuerAgent()
        
        setup_database()
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            pass
        else:
            genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel('models/gemini-2.0-flash')

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

        tools_map = {
            "check_audit": check_audit,
            "check_compliance": check_compliance,
            "analyze_risk": analyze_risk,
            "issue_contract": issue_contract,
            "deny_request": deny_request
        }
        
        tools_list = [check_audit, check_compliance, analyze_risk, issue_contract, deny_request]
        
        system_instruction = """
        You are the CreditSystemOrchestrator. Your job is to strictly evaluate a credit request by coordinating with specialized agents.
        
        Process Flow:
        1. `check_audit`: Verify if the customer exists. If invalid or not found -> `deny_request`.
        2. `check_compliance`: Check regulatory rules. If violation -> `deny_request`.
        3. `analyze_risk`: Check credit risk. If HIGH_RISK or ERROR -> `deny_request`.
        4. If ALL previous checks are OK -> `issue_contract`.
        
        Inputs: You will receive the credit request data in JSON.
        Outputs: You MUST call either `issue_contract` or `deny_request` to finalize the process.
        """
        
        try:
            chat = self.model.start_chat(history=[])
            
            prompt_parts = [
                system_instruction, 
                f"Request Data: {json.dumps(user_request, default=str)}"
            ]
            
            try:
                response = await chat.send_message_async(
                    prompt_parts,
                    tools=tools_list
                )
            except Exception as e:
                return {"status": "ERRO", "mensagem": "Failure", "detalhes": str(e)}

            for _ in range(15): 
                if not response.parts:
                     return {"status": "ERRO", "mensagem": "Empty Response"}

                part = response.parts[0]
                
                if part.function_call:
                    fc = part.function_call
                    name = fc.name
                    args = {k: v for k, v in fc.args.items()}
                    
                    if name in tools_map:
                        func = tools_map[name]
                        
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
                                    parts=[genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=name,
                                            response={"result": result}
                                        )
                                    )]
                                )
                            )
                        except Exception as e:
                             return {"status": "ERRO", "mensagem": "Return Failed", "detalhes": str(e)}
                    else:
                        return {"status": "ERRO", "mensagem": f"Tool {name} not found"}
                else:
                    if "deny" in response.text.lower() or "negado" in response.text.lower():
                        return {"status": "NEGADO", "motivo": response.text}
                    
                    try:
                        response = await chat.send_message_async("Proceed next step.")
                    except Exception as e:
                        return {"status": "ERRO", "mensagem": "Loop Failed", "detalhes": str(e)}
                        
        except Exception as e:
            return {"status": "ERRO", "mensagem": "Error", "detalhes": str(e)}

        return {"status": "ERRO", "mensagem": "Max loops exceeded."}
