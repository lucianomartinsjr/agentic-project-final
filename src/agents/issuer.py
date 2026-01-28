from src.tools.utils import format_currency, generate_protocol_id
from src.tools.db_tools import log_application_attempt
import json

class IssuerAgent:
    def __init__(self):
        self.name = "Emissor de Contratos"

    def process(self, request_context):
        print(f"   [{self.name}] Finalizando proposta...")
        
        # Gera protocolo (Tool)
        protocol = generate_protocol_id()
        amount_fmt = format_currency(request_context['loan_amount'])
        
        # Loga no banco (Tool)
        ml_risk = request_context.get("ml_risk") or {}
        ml_risk_log = {
            "risk_prediction": ml_risk.get("risk_prediction"),
            "risk_probability": ml_risk.get("risk_probability"),
            "status": ml_risk.get("status"),
        }
        log_application_attempt(
            cpf=request_context.get("cpf"),
            client_id=request_context.get("id"),
            amount=request_context.get("loan_amount"),
            duration=request_context.get("duration"),
            purpose=request_context.get("purpose"),
            sex=request_context.get("sex"),
            job=request_context.get("job"),
            housing=request_context.get("housing"),
            saving_accounts=request_context.get("saving_accounts"),
            checking_account=request_context.get("checking_account"),
            status="APPROVED",
            reason=json.dumps(ml_risk_log, ensure_ascii=False),
        )
        
        return {
            "success": True,
            "final_response": {
                "status": "APROVADO",
                "protocolo": protocol,
                "valor_liberado": amount_fmt,
                "mensagem": "Parabéns! Seu crédito foi aprovado e o contrato enviado.",
                "ml_risk": ml_risk_log,
            },
        }