from src.agents.risk_analyst import RiskAnalystAgent
from src.infrastructure.mcp_client import RealMCPClient
from src.agents.auditor import AuditorAgent
from src.agents.compliance import ComplianceAgent
from src.agents.issuer import IssuerAgent
from src.tools.db_tools import setup_database, log_application_attempt

class CreditSystemOrchestrator:
    def __init__(self):
        # 1. Cria o Cliente MCP
        self.mcp_client = RealMCPClient()
        
        # 2. Inicializa Agentes
        self.auditor = AuditorAgent()
        self.compliance = ComplianceAgent()
        # Passa o cliente para o analista (que vai usar o call_tool)
        self.risk_analyst = RiskAnalystAgent(self.mcp_client)
        self.issuer = IssuerAgent()
        
        setup_database()

    async def handle_request(self, user_request):
        print(f"\n--- 🤖 Iniciando Processo para CPF: {user_request.get('cpf')} ---")
        
        async with self.mcp_client.run_session():
            
            context = user_request.copy()

            # 1. Auditoria (Local)
            audit_res = self.auditor.process(context)
            if not audit_res['success']:
                log_application_attempt(
                    cpf=context.get("cpf"),
                    client_id=None,
                    amount=context.get("loan_amount"),
                    duration=context.get("duration"),
                    status="DENIED",
                    reason=audit_res.get("message"),
                )
                return self._refuse(audit_res['message'])
            context = audit_res['data']

            # 2. Compliance (Local)
            comp_res = self.compliance.process(context)
            if not comp_res['success']:
                log_application_attempt(
                    cpf=context.get("cpf"),
                    client_id=context.get("id"),
                    amount=context.get("loan_amount"),
                    duration=context.get("duration"),
                    status="DENIED",
                    reason=comp_res.get("message"),
                )
                return self._refuse(comp_res['message'])

            # 3. Risco (Remoto via MCP)
            # Como estamos dentro do 'async with', o self.mcp_client.session está ativo!
            risk_res = await self.risk_analyst.process(context)
            if not risk_res['success']:
                log_application_attempt(
                    cpf=context.get("cpf"),
                    client_id=context.get("id"),
                    amount=context.get("loan_amount"),
                    duration=context.get("duration"),
                    status="DENIED",
                    reason=f"Risco: {risk_res.get('reason')}",
                )
                return self._refuse(f"Risco: {risk_res.get('reason')}")

            # 4. Emissão (Local)
            issue_res = self.issuer.process(context)
            return issue_res['final_response']

    def _refuse(self, reason):
        print(f"   ⛔ PEDIDO NEGADO: {reason}")
        return {"status": "NEGADO", "motivo": reason}