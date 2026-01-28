import gradio as gr
import sys
import os
import asyncio

# --- FIX PARA WINDOWS ---
# Necessário para que subprocessos (MCP) funcionem corretamente no Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.orchestrator import CreditSystemOrchestrator

# --- Função de Backend ---
async def process_credit_analysis(cpf, amount, duration):
    # Instancia o sistema (que agora gerencia a conexão corretamente)
    orchestrator = CreditSystemOrchestrator()
    
    request_data = {
        "cpf": cpf,
        "loan_amount": float(amount),
        "duration": int(duration)
    }
    
    try:
        # O Orchestrator agora usa 'async with' internamente
        result = await orchestrator.handle_request(request_data)
        
        status_emoji = "✅" if result.get("status") == "APROVADO" else "⛔"
        status_msg = result.get("status", "ERRO")
        reason = result.get("motivo", result.get("mensagem", ""))
        
        friendly_output = f"""
        ### Resultado da Análise
        **Status:** {status_emoji} {status_msg}
        **Detalhe:** {reason}
        
        ---
        *Protocolo gerado pelo sistema de agentes.*
        """
        
        return friendly_output, result

    except Exception as e:
        import traceback
        traceback.print_exc() # Printa o erro real no terminal
        return f"❌ Erro Crítico: {str(e)}", {"error": str(e)}

# --- Interface Gráfica ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🏦 Sistema Agêntico de Crédito (MCP Real)")
    
    with gr.Row():
        with gr.Column():
            inp_cpf = gr.Textbox(label="CPF", value="111.222.333-44")
            inp_amount = gr.Number(label="Valor", value=10000)
            inp_duration = gr.Slider(6, 72, step=6, label="Meses", value=24)
            btn_submit = gr.Button("🚀 Analisar", variant="primary")
        
        with gr.Column():
            out_message = gr.Markdown()
            out_json = gr.JSON()
            
    gr.Examples(
        examples=[
            ["111.222.333-44", 10000, 24],  # Alice (Aprova)
            ["555.666.777-88", 50000, 12],  # Bob (Reprova Risco)
            ["000.000.000-00", 5000, 12],   # Fake (Reprova Auditoria)
        ],
        inputs=[inp_cpf, inp_amount, inp_duration],
        label="🧪 Cenários de Teste (Clique para preencher)"
    )

    btn_submit.click(
        fn=process_credit_analysis,
        inputs=[inp_cpf, inp_amount, inp_duration],
        outputs=[out_message, out_json]
    )

if __name__ == "__main__":
    demo.launch()