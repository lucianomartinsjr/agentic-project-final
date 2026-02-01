from __future__ import annotations

from src.agents.orchestrator import CreditSystemOrchestrator
from src.services.client_choice_service import extract_cpf_from_choice
from src.ui.handlers.history import list_applications_rows


async def process_credit_analysis(client_choice, amount, duration, purpose):
    orchestrator = CreditSystemOrchestrator()

    cpf = extract_cpf_from_choice(client_choice)
    request_data = {
        "cpf": cpf,
        "loan_amount": float(amount),
        "duration": int(duration),
        "purpose": str(purpose) if purpose is not None else "radio/TV",
    }

    try:
        result = await orchestrator.handle_request(request_data)

        status_emoji = "✅" if result.get("status") == "APROVADO" else "⛔"
        status_msg = result.get("status", "ERRO")
        reason = result.get("motivo", result.get("mensagem", ""))

        ml_risk = result.get("ml_risk") or {}
        details = result.get("detalhes") or {}

        ml_block = ""
        # Ensure details is a dict before checking/accessing keys
        details_dict = details if isinstance(details, dict) else {}
        
        if ml_risk or any(k in details_dict for k in ("risk_prediction", "risk_probability", "status", "dti_ratio")):
            risk_prediction = ml_risk.get("risk_prediction", details_dict.get("risk_prediction"))
            risk_probability = ml_risk.get("risk_probability", details_dict.get("risk_probability"))
            ml_status = ml_risk.get("status", details_dict.get("status"))
            dti_ratio = details_dict.get("dti_ratio")

            parts = [
                f"risk_prediction={risk_prediction}",
                f"risk_probability={risk_probability}",
                f"status={ml_status}",
            ]
            if dti_ratio is not None:
                try:
                    parts.append(f"dti_ratio={float(dti_ratio):.2f}")
                except Exception:
                    parts.append(f"dti_ratio={dti_ratio}")

            ml_block = f"\n**Detalhes do Risco (ML/DTI):** {' | '.join(parts)}\n"

        compliance_block = ""
        if isinstance(details, dict) and details.get("compliance_rule"):
            rule = details.get("compliance_rule")
            rule_parts = [f"regra={rule}"]
            for k in ("cpf", "age", "score"):
                if k in details:
                    rule_parts.append(f"{k}={details.get(k)}")
            compliance_block = f"\n**Detalhes de Compliance:** {' | '.join(rule_parts)}\n"
        elif isinstance(details, str) and not ml_block:
             # Se for string e não tivermos tratado no bloco ML, mostramos como info genérica
             compliance_block = f"\n**Detalhes Técnicos:** {details}\n"

        friendly_output = f"""
        ### Resultado da Análise
        **Status:** {status_emoji} {status_msg}
        **Detalhe:** {reason}
        {ml_block}
        {compliance_block}

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
