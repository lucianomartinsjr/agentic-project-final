from src.tools.db_tools import get_client_data
from src.tools.utils import validate_cpf_format

class AuditorAgent:
    def __init__(self):
        self.name = "Auditor de Dados"

    def process(self, request_context):
        print(f"   [{self.name}] Verificando cadastro no Banco de Dados...")
        cpf = request_context.get("cpf")

        if not cpf or not validate_cpf_format(str(cpf)):
            return {
                "success": False,
                "message": "CPF ausente ou com formato inválido.",
                "details": {
                    "audit_rule": "CPF_FORMAT",
                    "cpf": cpf,
                },
            }
        
        # Usa a Tool de DB
        try:
            client_data = get_client_data(str(cpf))
        except Exception as e:
            return {
                "success": False,
                "message": "Falha ao consultar cadastro no banco de dados.",
                "details": {"audit_rule": "DB_LOOKUP_ERROR", "error": str(e)},
            }
        
        if not client_data:
            return {
                "success": False, 
                "message": f"Cliente com CPF {cpf} não encontrado."
            }
        
        # Enriquece o contexto com os dados vindos do banco
        request_context.update(client_data)
        return {"success": True, "data": request_context}