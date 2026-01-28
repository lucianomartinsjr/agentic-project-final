from src.agents.risk_analyst import RiskAnalystAgent
from src.infrastructure.mcp_client import RealMCPClient
from src.agents.auditor import AuditorAgent
from src.agents.compliance import ComplianceAgent
from src.agents.issuer import IssuerAgent
from src.tools.db_tools import setup_database

class CreditSystemOrchestrator:
    def __init__(self):
        # Cliente Real Async
        self.mcp_client = RealMCPClient()
        
        self.auditor = AuditorAgent()
        self.compliance = ComplianceAgent()
        # Passamos o cliente real para o analista
        self.risk_analyst = RiskAnalystAgent(self.mcp_client)
        self.issuer = IssuerAgent()
        setup_database()

    async def handle_request(self, user_request):
        print(f"\n--- 🤖 Iniciando Processo (MCP Async) para CPF: {user_request.get('cpf')} ---")
        
        # Conecta o cliente (inicia o servidor subprocesso)
        await self.mcp_client.connect()
        
        try:
            context = user_request.copy()

            # Passos Síncronos (Locais)
            audit_res = self.auditor.process(context)
            if not audit_res['success']: return self._refuse(audit_res['message'])
            context = audit_res['data']

            comp_res = self.compliance.process(context)
            if not comp_res['success']: return self._refuse(comp_res['message'])

            # --- PASSO CRÍTICO: CHAMADA ASSÍNCRONA VIA MCP ---
            risk_res = await self.risk_analyst.process(context)
            if not risk_res['success']:
                return self._refuse(f"Risco: {risk_res.get('reason')}")

            # Passo Final Síncrono
            issue_res = self.issuer.process(context)
            return issue_res['final_response']
            
        finally:
            # Importante: Fechar a conexão com o servidor ao terminar
            await self.mcp_client.close()

    def _refuse(self, reason):
        print(f"   ⛔ PEDIDO NEGADO: {reason}")
        return {"status": "NEGADO", "motivo": reason}