from src.tools.db_tools import get_client_data

class AuditorAgent:
    def __init__(self):
        self.name = "Auditor de Dados"

    def process(self, request_context):
        print(f"   [{self.name}] Verificando cadastro no Banco de Dados...")
        cpf = request_context.get('cpf')
        
        # Usa a Tool de DB
        client_data = get_client_data(cpf)
        
        if not client_data:
            return {
                "success": False, 
                "message": f"Cliente com CPF {cpf} não encontrado."
            }
        
        # Enriquece o contexto com os dados vindos do banco
        request_context.update(client_data)
        return {"success": True, "data": request_context}