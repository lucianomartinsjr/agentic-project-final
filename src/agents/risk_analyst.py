import json
import ast

from src.tools.ml_tools import predict_credit_risk
from src.tools.utils import calculate_dti


def _parse_mcp_payload(payload: str) -> dict:
    if payload is None:
        return {"status": "ERROR", "risk_probability": 0.0}
    payload = str(payload).strip()
    if not payload:
        return {"status": "ERROR", "risk_probability": 0.0}

    try:
        obj = json.loads(payload)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    
    try:
        obj = ast.literal_eval(payload)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    return {"status": "ERROR", "risk_probability": 0.0, "raw": payload}

class RiskAnalystAgent:
    def __init__(self, mcp_client):
        self.name = "Analista de Risco (IA)"
        self.mcp = mcp_client 

    async def process(self, request_context):
        age = request_context.get("age")
        income = request_context.get("income")
        loan_amount = request_context.get("loan_amount")
        duration = request_context.get("duration")
        score = request_context.get("score")
        purpose = request_context.get("purpose")
        sex = request_context.get("sex")
        housing = request_context.get("housing")
        saving_accounts = request_context.get("saving_accounts")
        checking_account = request_context.get("checking_account")
        job = request_context.get("job")

        try:
            age_i = int(age)
            income_f = float(income)
            loan_amount_f = float(loan_amount)
            duration_i = int(duration)
            score_i = int(score)
        except Exception as e:
            return {
                "success": False,
                "reason": "Dados insuficientes/invalidos para análise de risco.",
                "details": {
                    "status": "ERROR",
                    "error_msg": str(e),
                    "age": age,
                    "income": income,
                    "loan_amount": loan_amount,
                    "duration": duration,
                    "score": score,
                },
            }

        ml_result = None
        mcp_error = None
        try:
            ml_result_str = await self.mcp.call_tool(
                "analyze_risk",
                arguments={
                    "age": age_i,
                    "income": income_f,
                    "loan_amount": loan_amount_f,
                    "duration": duration_i,
                    "score": score_i,
                    "purpose": purpose,
                    "sex": sex,
                    "housing": housing,
                    "saving_accounts": saving_accounts,
                    "checking_account": checking_account,
                    "job": job,
                },
            )
            ml_result = _parse_mcp_payload(ml_result_str)
        except Exception as e:
            mcp_error = e

        needs_local_fallback = (
            ml_result is None
            or ml_result.get("status") == "ERROR"
            or ml_result.get("risk_prediction") is None
            or ml_result.get("risk_probability") is None
        )

        if needs_local_fallback:
            try:
                ml_result = predict_credit_risk(
                    age_i,
                    income_f,
                    loan_amount_f,
                    duration_i,
                    score_i,
                    purpose=purpose,
                    sex=sex,
                    housing=housing,
                    saving_accounts=saving_accounts,
                    checking_account=checking_account,
                    job=job,
                )
            except Exception as inner:
                return {
                    "success": False,
                    "reason": "Falha na análise de risco (MCP e fallback local).",
                    "details": {
                        "status": "ERROR",
                        "error_msg": str(inner),
                        "risk_prediction": None,
                        "risk_probability": 0.0,
                    },
                }

        try:
            dti_str = await self.mcp.call_tool(
                "calculate_debt_ratio",
                arguments={"income": income_f, "loan_amount": loan_amount_f},
            )
            dti = float(dti_str)
        except Exception:
            try:
                dti = float(calculate_dti(income_f, loan_amount_f))
            except Exception:
                dti = 999.9
        
        ml_status = (ml_result or {}).get("status")
        is_high_risk = ml_status == "HIGH_RISK"
        is_high_dti = dti > 20.0

        if is_high_risk or is_high_dti:
            triggers = []
            if is_high_risk:
                triggers.append(
                    f"ML={ml_status} (pred={ml_result.get('risk_prediction')}, prob={ml_result.get('risk_probability', 0.0)})"
                )
            if is_high_dti:
                triggers.append(f"DTI={dti:.2f} (> 20.0)")

            reason = "Risco Elevado"
            if triggers:
                reason = f"Risco Elevado ({'; '.join(triggers)})"

            return {
                "success": False,
                "reason": reason,
                "details": {
                    "ml_prob": (ml_result or {}).get("risk_probability", 0.0),
                    "dti_ratio": dti,
                    "risk_prediction": (ml_result or {}).get("risk_prediction"),
                    "risk_probability": (ml_result or {}).get("risk_probability", 0.0),
                    "status": ml_status,
                },
            }
            
        return {
            "success": True, 
            "details": {
                "ml_prob": (ml_result or {}).get("risk_probability", 0.0),
                "dti_ratio": dti,
                "risk_prediction": (ml_result or {}).get("risk_prediction"),
                "risk_probability": (ml_result or {}).get("risk_probability", 0.0),
                "status": (ml_result or {}).get("status"),
            }
        }