from __future__ import annotations

from src.agents.orchestrator import CreditSystemOrchestrator
from src.services.client_choice_service import extract_cpf_from_choice
from src.ui.handlers.history import list_applications_rows


async def process_credit_analysis(client_choice, amount, duration):
    orchestrator = CreditSystemOrchestrator()

    cpf = extract_cpf_from_choice(client_choice)
    request_data = {
        "cpf": cpf,
        "loan_amount": float(amount),
        "duration": int(duration),
    }

    try:
        result = await orchestrator.handle_request(request_data)

        status_emoji = "✅" if result.get("status") == "APROVADO" else "⛔"
        status_msg = result.get("status", "ERRO")
        reason = result.get("motivo", result.get("mensagem", ""))

        ml_risk = result.get("ml_risk") or {}
        ml_block = ""
        if ml_risk:
            ml_block = (
                f"\n**ML (predict_credit_risk):** "
                f"risk_prediction={ml_risk.get('risk_prediction')} | "
                f"risk_probability={ml_risk.get('risk_probability')} | "
                f"status={ml_risk.get('status')}\n"
            )

        friendly_output = f"""
        ### Resultado da Análise
        **Status:** {status_emoji} {status_msg}
        **Detalhe:** {reason}
        {ml_block}

        ---
        *Protocolo gerado pelo sistema de agentes.*
        """

        hist_rows = list_applications_rows()
        return friendly_output, result, hist_rows

    except Exception as e:
        import traceback

        traceback.print_exc()
        hist_rows = list_applications_rows()
        return f"❌ Erro Crítico: {str(e)}", {"error": str(e)}, hist_rows
