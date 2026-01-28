from __future__ import annotations

import gradio as gr

from src.services.cpf_service import format_cpf_input
from src.tools.db_tools import setup_database
from src.ui.handlers.analysis import process_credit_analysis
from src.ui.handlers.clients import (
    client_choices,
    create_client_and_refresh,
    list_clients_rows,
    load_client_for_edit,
    update_client_and_refresh,
)
from src.ui.handlers.history import list_applications_rows


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


def create_demo() -> gr.Blocks:
    setup_database()

    with gr.Blocks() as demo:
        gr.Markdown("# 🏦 Sistema Agêntico de Crédito")

        with gr.Tabs():
            with gr.Tab("Nova Solicitação"):
                with gr.Row():
                    with gr.Column():
                        initial_choices = client_choices()
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
                        ["Alice Silva | 111.222.333-44", 10000, 24],
                        ["Bob Santos | 555.666.777-88", 50000, 12],
                    ],
                    inputs=[client_dropdown, inp_amount, inp_duration],
                    label="🧪 Cenários de Teste (Clique para preencher)",
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
                    edit_choices = client_choices()
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
                new_cpf.change(fn=format_cpf_input, inputs=[new_cpf], outputs=[new_cpf])
                edit_cpf.change(fn=format_cpf_input, inputs=[edit_cpf], outputs=[edit_cpf])

                # Carregar dados do cliente selecionado para edição
                edit_dropdown.change(
                    fn=load_client_for_edit,
                    inputs=[edit_dropdown],
                    outputs=[edit_name, edit_cpf, edit_income, edit_age, edit_score],
                )

                demo.load(
                    fn=load_client_for_edit,
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
                    fn=create_client_and_refresh,
                    inputs=[new_name, new_cpf, new_income, new_age, new_score, client_dropdown, edit_dropdown],
                    outputs=[out_create, client_dropdown, edit_dropdown, clients_table, modal_create, modal_edit, clients_list_group],
                )

                btn_update.click(
                    fn=update_client_and_refresh,
                    inputs=[edit_dropdown, edit_name, edit_cpf, edit_income, edit_age, edit_score, client_dropdown, edit_dropdown],
                    outputs=[out_edit, client_dropdown, edit_dropdown, clients_table, modal_create, modal_edit, clients_list_group],
                )

                btn_refresh_clients.click(fn=list_clients_rows, inputs=[], outputs=[clients_table])
                demo.load(fn=list_clients_rows, inputs=[], outputs=[clients_table])

            with gr.Tab("Histórico"):
                btn_refresh_hist = gr.Button("🔄 Atualizar histórico")
                apps_table = gr.Dataframe(
                    headers=["id", "cpf", "client_id", "amount", "duration", "status", "reason", "created_at"],
                    datatype=["number", "str", "number", "number", "number", "str", "str", "str"],
                    interactive=False,
                    wrap=True,
                )

                btn_refresh_hist.click(fn=list_applications_rows, inputs=[], outputs=[apps_table])
                demo.load(fn=list_applications_rows, inputs=[], outputs=[apps_table])

        # Bindings que dependem de componentes criados em outras abas
        btn_submit.click(
            fn=process_credit_analysis,
            inputs=[client_dropdown, inp_amount, inp_duration],
            outputs=[out_message, out_json, apps_table],
        )

    return demo
