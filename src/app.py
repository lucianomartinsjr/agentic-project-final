import gradio as gr
import sys
import os
import asyncio
import warnings

# --- FIX PARA WINDOWS ---
# Necessário para que subprocessos (MCP) funcionem corretamente no Windows
if sys.platform.startswith("win"):
    # Mantém compatibilidade com subprocessos no Windows, sem poluir o terminal com warnings.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.orchestrator import CreditSystemOrchestrator
from src.tools.db_tools import setup_database, add_client, list_clients, list_applications, get_client_data, update_client
from src.tools.utils import validate_cpf_format

# --- Função de Backend ---
def _extract_cpf_from_choice(choice: str) -> str:
    if not choice:
        return ""
    # Formato: "Nome | XXX.XXX.XXX-XX"
    if "|" in choice:
        return choice.split("|", 1)[1].strip()
    return str(choice).strip()


def _format_cpf_input(value: str) -> str:
    """Máscara simples: mantém só dígitos, limita a 11 e formata como XXX.XXX.XXX-XX."""
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())[:11]
    if not digits:
        return ""
    part1 = digits[:3]
    part2 = digits[3:6]
    part3 = digits[6:9]
    part4 = digits[9:11]

    out = part1
    if len(digits) > 3:
        out += "." + part2
    if len(digits) > 6:
        out += "." + part3
    if len(digits) > 9:
        out += "-" + part4
    return out


def _is_cpf_complete(value: str) -> bool:
    return validate_cpf_format(_format_cpf_input(value))


def _client_choices() -> list[str]:
    setup_database()
    clients = list_clients()
    return [f"{c.get('name', '').strip()} | {c.get('cpf', '').strip()}" for c in clients]


async def process_credit_analysis(client_choice, amount, duration):
    # Instancia o sistema (que agora gerencia a conexão corretamente)
    orchestrator = CreditSystemOrchestrator()

    cpf = _extract_cpf_from_choice(client_choice)
    
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
        
        # Atualiza histórico automaticamente após cada solicitação
        hist_rows = ui_list_applications()
        return friendly_output, result, hist_rows

    except Exception as e:
        import traceback
        traceback.print_exc() # Printa o erro real no terminal
        hist_rows = ui_list_applications()
        return f"❌ Erro Crítico: {str(e)}", {"error": str(e)}, hist_rows


def _clients_to_table(clients: list[dict]):
    rows = [
        [c.get("id"), c.get("name"), c.get("cpf"), c.get("income"), c.get("age"), c.get("score")]
        for c in clients
    ]
    return rows


def _apps_to_table(apps: list[dict]):
    rows = [
        [
            a.get("id"),
            a.get("cpf"),
            a.get("client_id"),
            a.get("amount"),
            a.get("duration"),
            a.get("status"),
            a.get("reason"),
            a.get("created_at"),
        ]
        for a in apps
    ]
    return rows


def ui_create_client(name, cpf, income, age, score):
    setup_database()
    res = add_client(
        name=str(name).strip(),
        cpf=str(cpf).strip(),
        income=float(income),
        age=int(age),
        score=int(score),
    )

    emoji = "✅" if res.get("success") else "⛔"
    msg = res.get("message", "")
    return f"### Cadastro\n**Status:** {emoji} {msg}"


def ui_create_client_and_refresh(name, cpf, income, age, score, current_selection, edit_selection):
    setup_database()
    name = str(name).strip()
    cpf = _format_cpf_input(cpf)

    if not _is_cpf_complete(cpf):
        markdown = "### Cadastro\n**Status:** ⛔ CPF inválido. Use o formato XXX.XXX.XXX-XX"
        choices = _client_choices()
        clients_rows = ui_list_clients()
        edit_value = edit_selection if edit_selection in choices else (choices[0] if choices else None)
        return (
            markdown,
            gr.update(choices=choices, value=current_selection),
            gr.update(choices=choices, value=edit_value),
            clients_rows,
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )

    res = add_client(
        name=name,
        cpf=cpf,
        income=float(income),
        age=int(age),
        score=int(score),
    )

    emoji = "✅" if res.get("success") else "⛔"
    msg = res.get("message", "")
    markdown = f"### Cadastro\n**Status:** {emoji} {msg}"

    choices = _client_choices()
    preferred = f"{name} | {cpf}" if res.get("success") else current_selection
    if preferred not in choices:
        preferred = choices[0] if choices else None

    # Atualiza também a lista de clientes (tabela)
    clients_rows = ui_list_clients()
    edit_value = preferred if preferred in choices else (choices[0] if choices else None)

    # Fecha modal/backdrop e volta para a lista apenas quando sucesso
    if not res.get("success"):
        return (
            markdown,
            gr.update(choices=choices, value=preferred),
            gr.update(choices=choices, value=edit_value),
            clients_rows,
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )
    return (
        markdown,
        gr.update(choices=choices, value=preferred),
        gr.update(choices=choices, value=edit_value),
        clients_rows,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def ui_load_client_for_edit(client_choice):
    cpf = _extract_cpf_from_choice(client_choice)
    data = get_client_data(cpf)
    if not data:
        return "", "", 0.0, 0, 0
    return data.get("name", ""), data.get("cpf", ""), data.get("income", 0.0), data.get("age", 0), data.get("score", 0)


def ui_update_client_and_refresh(edit_choice, name, cpf, income, age, score, main_selection, edit_selection):
    old_cpf = _extract_cpf_from_choice(edit_choice)
    setup_database()

    cpf = _format_cpf_input(cpf)
    if not _is_cpf_complete(cpf):
        markdown = "### Edição\n**Status:** ⛔ CPF inválido. Use o formato XXX.XXX.XXX-XX"
        choices = _client_choices()
        clients_rows = ui_list_clients()
        return (
            markdown,
            gr.update(choices=choices, value=main_selection),
            gr.update(choices=choices, value=edit_selection),
            clients_rows,
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    res = update_client(
        old_cpf=old_cpf,
        name=str(name).strip(),
        cpf=cpf,
        income=float(income),
        age=int(age),
        score=int(score),
    )

    emoji = "✅" if res.get("success") else "⛔"
    msg = res.get("message", "")
    markdown = f"### Edição\n**Status:** {emoji} {msg}"

    choices = _client_choices()
    preferred = f"{str(name).strip()} | {str(cpf).strip()}" if res.get("success") else edit_choice
    if preferred not in choices:
        preferred = choices[0] if choices else None

    clients_rows = ui_list_clients()

    # Atualiza ambos dropdowns (Nova Solicitação e seletor de edição)
    main_value = preferred if preferred in choices else main_selection
    edit_value = preferred if preferred in choices else edit_selection

    # Fecha modal/backdrop e volta para lista apenas quando sucesso
    if not res.get("success"):
        return (
            markdown,
            gr.update(choices=choices, value=main_value),
            gr.update(choices=choices, value=edit_value),
            clients_rows,
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    return (
        markdown,
        gr.update(choices=choices, value=main_value),
        gr.update(choices=choices, value=edit_value),
        clients_rows,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def ui_list_clients():
    setup_database()
    clients = list_clients()
    return _clients_to_table(clients)


def ui_list_applications():
    setup_database()
    apps = list_applications()
    return _apps_to_table(apps)

# --- Interface Gráfica ---
MODAL_CSS = """
/* Modal simulado (Gradio 6.4 não tem Dialog/Modal nativo) */
#modal_create, #modal_edit {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 2001;
    width: min(720px, 95vw);
    max-height: 90vh;
    overflow: auto;
    background: var(--body-background-fill, white);
    border: 1px solid var(--border-color-primary, rgba(0,0,0,0.12));
    border-radius: 14px;
    padding: 16px;
}
"""

with gr.Blocks() as demo:
    gr.Markdown("# 🏦 Sistema Agêntico de Crédito")

    setup_database()

    with gr.Tabs():
        with gr.Tab("Nova Solicitação"):
            with gr.Row():
                with gr.Column():
                    initial_choices = _client_choices()
                    client_dropdown = gr.Dropdown(
                        label="Cliente (pesquise pelo nome)",
                        choices=initial_choices,
                        value=initial_choices[0] if initial_choices else None,
                        interactive=True,
                    )
                    inp_amount = gr.Number(label="Valor", value=10000)
                    inp_duration = gr.Slider(6, 72, step=6, label="Meses", value=24)
                    btn_submit = gr.Button("🚀 Analisar", variant="primary")

                with gr.Column():
                    out_message = gr.Markdown()
                    out_json = gr.JSON()

            gr.Examples(
                examples=[
                    ["Alice Silva | 111.222.333-44", 10000, 24],  # Alice (Aprova)
                    ["Bob Santos | 555.666.777-88", 50000, 12],  # Bob (Reprova Risco)
                ],
                inputs=[client_dropdown, inp_amount, inp_duration],
                label="🧪 Cenários de Teste (Clique para preencher)"
            )

        with gr.Tab("Clientes"):
            gr.Markdown("Gerencie clientes: cadastre novos, edite existentes e acompanhe a lista.")

            with gr.Row():
                btn_open_create = gr.Button("➕ Cadastrar cliente", variant="primary")
                btn_open_edit = gr.Button("✏️ Editar cliente")

            with gr.Group(visible=True) as clients_list_group:
                btn_refresh_clients = gr.Button("🔄 Atualizar lista")
                clients_table = gr.Dataframe(
                    headers=["id", "name", "cpf", "income", "age", "score"],
                    datatype=["number", "str", "str", "number", "number", "number"],
                    interactive=False,
                    wrap=True,
                )

            def ui_open_create_modal():
                return gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

            def ui_open_edit_modal():
                return gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)

            def ui_close_modals():
                return gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

            # Modal: Cadastro
            with gr.Group(visible=False, elem_id="modal_create") as modal_create:
                gr.Markdown("## Cadastrar cliente")
                new_name = gr.Textbox(label="Nome", value="", placeholder="Ex: Maria Souza")
                new_cpf = gr.Textbox(label="CPF", value="", placeholder="XXX.XXX.XXX-XX")
                new_income = gr.Number(label="Renda", value=5000)
                new_age = gr.Number(label="Idade", value=30, precision=0)
                new_score = gr.Number(label="Score", value=750, precision=0)
                out_create = gr.Markdown()
                with gr.Row():
                    btn_create = gr.Button("💾 Cadastrar", variant="primary")
                    btn_cancel_create = gr.Button("Cancelar")

            # Modal: Edição
            with gr.Group(visible=False, elem_id="modal_edit") as modal_edit:
                gr.Markdown("## Editar cliente")
                edit_choices = _client_choices()
                edit_dropdown = gr.Dropdown(
                    label="Selecione o cliente",
                    choices=edit_choices,
                    value=edit_choices[0] if edit_choices else None,
                    interactive=True,
                )
                edit_name = gr.Textbox(label="Nome", value="")
                edit_cpf = gr.Textbox(label="CPF", value="", placeholder="XXX.XXX.XXX-XX")
                edit_income = gr.Number(label="Renda", value=0)
                edit_age = gr.Number(label="Idade", value=0, precision=0)
                edit_score = gr.Number(label="Score", value=0, precision=0)
                out_edit = gr.Markdown()
                with gr.Row():
                    btn_update = gr.Button("💾 Salvar alterações", variant="primary")
                    btn_cancel_edit = gr.Button("Cancelar")

            # Máscaras CPF
            new_cpf.change(fn=_format_cpf_input, inputs=[new_cpf], outputs=[new_cpf])
            edit_cpf.change(fn=_format_cpf_input, inputs=[edit_cpf], outputs=[edit_cpf])

            # Carregar dados do cliente selecionado para edição
            edit_dropdown.change(
                fn=ui_load_client_for_edit,
                inputs=[edit_dropdown],
                outputs=[edit_name, edit_cpf, edit_income, edit_age, edit_score],
            )

            demo.load(
                fn=ui_load_client_for_edit,
                inputs=[edit_dropdown],
                outputs=[edit_name, edit_cpf, edit_income, edit_age, edit_score],
            )

            # Botões abrir/fechar modais
            btn_open_create.click(fn=ui_open_create_modal, inputs=[], outputs=[modal_create, modal_edit, clients_list_group])
            btn_open_edit.click(fn=ui_open_edit_modal, inputs=[], outputs=[modal_create, modal_edit, clients_list_group])
            btn_cancel_create.click(fn=ui_close_modals, inputs=[], outputs=[modal_create, modal_edit, clients_list_group])
            btn_cancel_edit.click(fn=ui_close_modals, inputs=[], outputs=[modal_create, modal_edit, clients_list_group])

            # Ações de salvar
            btn_create.click(
                fn=ui_create_client_and_refresh,
                inputs=[new_name, new_cpf, new_income, new_age, new_score, client_dropdown, edit_dropdown],
                outputs=[out_create, client_dropdown, edit_dropdown, clients_table, modal_create, modal_edit, clients_list_group],
            )

            btn_update.click(
                fn=ui_update_client_and_refresh,
                inputs=[edit_dropdown, edit_name, edit_cpf, edit_income, edit_age, edit_score, client_dropdown, edit_dropdown],
                outputs=[out_edit, client_dropdown, edit_dropdown, clients_table, modal_create, modal_edit, clients_list_group],
            )

            btn_refresh_clients.click(fn=ui_list_clients, inputs=[], outputs=[clients_table])
            demo.load(fn=ui_list_clients, inputs=[], outputs=[clients_table])

        with gr.Tab("Histórico"):
            btn_refresh_hist = gr.Button("🔄 Atualizar histórico")
            apps_table = gr.Dataframe(
                headers=["id", "cpf", "client_id", "amount", "duration", "status", "reason", "created_at"],
                datatype=["number", "str", "number", "number", "number", "str", "str", "str"],
                interactive=False,
                wrap=True,
            )

            btn_refresh_hist.click(fn=ui_list_applications, inputs=[], outputs=[apps_table])
            demo.load(fn=ui_list_applications, inputs=[], outputs=[apps_table])

    # Bindings que dependem de componentes criados em outras abas
    btn_submit.click(
        fn=process_credit_analysis,
        inputs=[client_dropdown, inp_amount, inp_duration],
        outputs=[out_message, out_json, apps_table],
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=MODAL_CSS)