from src.agents.auditor import AuditorAgent
from src.agents.compliance import ComplianceAgent
from src.agents.risk_analyst import RiskAnalystAgent
from src.agents.issuer import IssuerAgent
from src.tools.db_tools import setup_database

class CreditSystemOrchestrator:
    def __init__(self):
        # Inicializa a equipe
        self.auditor = AuditorAgent()
        self.compliance = ComplianceAgent()
        self.risk_analyst = RiskAnalystAgent()
        self.issuer = IssuerAgent()
        
        # Garante que o banco existe
        setup_database()

    def handle_request(self, user_request):
        print(f"\n--- 🤖 Iniciando Processo para CPF: {user_request.get('cpf')} ---")
        
        # Contexto compartilhado (a memória do processo)
        context = user_request.copy()

        # PASSO 1: Auditoria (Quem é você?)
        audit_res = self.auditor.process(context)
        if not audit_res['success']:
            return self._refuse(audit_res['message'])
        
        # Atualiza contexto com dados do banco retornados pelo auditor
        context = audit_res['data']

        # PASSO 2: Compliance (Você cumpre as regras?)
        comp_res = self.compliance.process(context)
        if not comp_res['success']:
            return self._refuse(comp_res['message'])

        # PASSO 3: Análise de Risco (Vai pagar?)
        risk_res = self.risk_analyst.process(context)
        if not risk_res['success']:
            reason = risk_res.get('reason', 'Critérios de risco não atendidos')
            return self._refuse(f"Reprovado na análise de risco: {reason}")

        # PASSO 4: Emissão (Toma aqui o dinheiro)
        issue_res = self.issuer.process(context)
        return issue_res['final_response']

    def _refuse(self, reason):
        print(f"   ⛔ PEDIDO NEGADO: {reason}")
        return {
            "status": "NEGADO",
            "motivo": reason
        }