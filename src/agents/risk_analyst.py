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

    # Preferir JSON válido
    try:
        obj = json.loads(payload)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Compatibilidade com retorno antigo: str(dict) com aspas simples
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
        self.mcp = mcp_client # Instância do RealMCPClient

    async def process(self, request_context):
        print(f"   [{self.name}] Solicitando análise via Protocolo MCP Real...")
        
        # 1. Chamada Real via Protocolo
        # O servidor retorna uma string (JSON), precisamos fazer parse
        age = request_context.get('age')
        income = request_context.get('income')
        loan_amount = request_context.get('loan_amount')
        duration = request_context.get('duration')
        score = request_context.get('score')
        purpose = request_context.get('purpose')
        sex = request_context.get('sex')
        housing = request_context.get('housing')
        saving_accounts = request_context.get('saving_accounts')
        checking_account = request_context.get('checking_account')
        job = request_context.get('job')

        try:
            ml_result_str = await self.mcp.call_tool(
                "analyze_risk",
                arguments={
                    "age": age,
                    "income": income,
                    "loan_amount": loan_amount,
                    "duration": duration,
                    "score": score,
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
            print(f"   [{self.name}] MCP indisponível/timeout ({e}). Usando fallback local...")
            try:
                ml_result = predict_credit_risk(
                    int(age),
                    float(income),
                    float(loan_amount),
                    int(duration),
                    int(score),
                    purpose=purpose,
                    sex=sex,
                    housing=housing,
                    saving_accounts=saving_accounts,
                    checking_account=checking_account,
                    job=job,
                )
            except Exception:
                ml_result = {"status": "ERROR", "risk_probability": 0.0, "error_msg": str(e)}

        # 2. Chamada para DTI
        try:
            dti_str = await self.mcp.call_tool(
                "calculate_debt_ratio",
                arguments={"income": income, "loan_amount": loan_amount},
            )
            dti = float(dti_str)
        except Exception:
            print(f"   [{self.name}] Falha/timeout no cálculo DTI via MCP. Usando cálculo local...")
            try:
                dti = float(calculate_dti(float(income), float(loan_amount)))
            except Exception:
                dti = 999.9
        
        # Lógica de Decisão
        # Regra: negar se DTI muito alto OU se a probabilidade de risco ultrapassar um limiar.
        # Isso evita negar automaticamente apenas porque o classificador retornou pred=1.
        RISK_PROB_DENY_THRESHOLD = 0.75

        ml_status = ml_result.get("status")
        risk_prediction = ml_result.get("risk_prediction")
        risk_probability = ml_result.get("risk_probability", 0.0)
        try:
            risk_probability = float(risk_probability)
        except Exception:
            risk_probability = 0.0

        is_high_risk_prob = risk_probability >= RISK_PROB_DENY_THRESHOLD
        is_high_dti = dti > 20.0

        if is_high_risk_prob or is_high_dti:
            triggers = []
            if is_high_risk_prob:
                triggers.append(
                    f"ML={ml_status} (pred={risk_prediction}, prob={risk_probability:.4f} >= {RISK_PROB_DENY_THRESHOLD})"
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
                    "ml_prob": risk_probability,
                    "dti_ratio": dti,
                    "risk_prediction": risk_prediction,
                    "risk_probability": risk_probability,
                    "status": ml_status,
                    "risk_prob_threshold": RISK_PROB_DENY_THRESHOLD,
                },
            }
            
        return {
            "success": True, 
            "details": {
                "ml_prob": risk_probability,
                "dti_ratio": dti,
                "risk_prediction": risk_prediction,
                "risk_probability": risk_probability,
                "status": ml_status,
                "risk_prob_threshold": RISK_PROB_DENY_THRESHOLD,
            }
        }