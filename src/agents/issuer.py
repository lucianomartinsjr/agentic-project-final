from src.tools.utils import format_currency, generate_protocol_id
from src.tools.db_tools import log_application_attempt
import json

class IssuerAgent:
    def __init__(self):
        self.name = "Emissor de Contratos"

    def process(self, request_context):
        loan_amount = request_context.get("loan_amount")
        duration = request_context.get("duration")
        cpf = request_context.get("cpf")
        client_id = request_context.get("id")

        try:
            loan_amount_f = float(loan_amount)
            duration_i = int(duration) if duration is not None else None
        except Exception as e:
            try:
                log_application_attempt(
                    cpf=cpf,
                    client_id=client_id,
                    amount=loan_amount,
                    duration=duration,
                    purpose=request_context.get("purpose"),
                    sex=request_context.get("sex"),
                    job=request_context.get("job"),
                    housing=request_context.get("housing"),
                    saving_accounts=request_context.get("saving_accounts"),
                    checking_account=request_context.get("checking_account"),
                    status="ERROR",
                    reason=f"Issuer: dados inválidos ({str(e)})",
                )
            except Exception:
                pass
            return {
                "success": False,
                "final_response": {
                    "status": "ERRO",
                    "mensagem": "Não foi possível emitir o contrato por dados inválidos.",
                    "detalhes": {"error": str(e), "loan_amount": loan_amount, "duration": duration},
                },
            }

        if loan_amount_f <= 0:
            try:
                log_application_attempt(
                    cpf=cpf,
                    client_id=client_id,
                    amount=loan_amount_f,
                    duration=duration_i,
                    purpose=request_context.get("purpose"),
                    sex=request_context.get("sex"),
                    job=request_context.get("job"),
                    housing=request_context.get("housing"),
                    saving_accounts=request_context.get("saving_accounts"),
                    checking_account=request_context.get("checking_account"),
                    status="ERROR",
                    reason="Issuer: loan_amount <= 0",
                )
            except Exception:
                pass
            return {
                "success": False,
                "final_response": {
                    "status": "ERRO",
                    "mensagem": "Valor do empréstimo inválido.",
                    "detalhes": {"loan_amount": loan_amount_f},
                },
            }
        
        protocol = generate_protocol_id()
        amount_fmt = format_currency(loan_amount_f)
        
        ml_risk = request_context.get("ml_risk") or {}
        ml_risk_log = {
            "risk_prediction": ml_risk.get("risk_prediction"),
            "risk_probability": ml_risk.get("risk_probability"),
            "status": ml_risk.get("status"),
        }
        log_application_attempt(
            cpf=cpf,
            client_id=client_id,
            amount=loan_amount_f,
            duration=duration_i,
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