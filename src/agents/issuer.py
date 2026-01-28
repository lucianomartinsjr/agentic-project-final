from src.tools.utils import format_currency, generate_protocol_id
from src.tools.db_tools import log_application_attempt

class IssuerAgent:
    def __init__(self):
        self.name = "Emissor de Contratos"

    def process(self, request_context):
        print(f"   [{self.name}] Finalizando proposta...")
        
        # Gera protocolo (Tool)
        protocol = generate_protocol_id()
        amount_fmt = format_currency(request_context['loan_amount'])
        
        # Loga no banco (Tool)
        log_application_attempt(
            cpf=request_context.get("cpf"),
            client_id=request_context.get("id"),
            amount=request_context.get("loan_amount"),
            duration=request_context.get("duration"),
            status="APPROVED",
            reason=None,
        )
        
        return {
            "success": True,
            "final_response": {
                "status": "APROVADO",
                "protocolo": protocol,
                "valor_liberado": amount_fmt,
                "mensagem": "Parabéns! Seu crédito foi aprovado e o contrato enviado."
            }
        }