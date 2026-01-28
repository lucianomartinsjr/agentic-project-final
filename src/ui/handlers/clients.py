from __future__ import annotations

import gradio as gr

from src.services.client_choice_service import build_choice
from src.services.cpf_service import format_cpf_input, is_cpf_complete
from src.services.table_formatters import clients_to_table
from src.tools.db_tools import add_client, get_client_data, list_clients, setup_database, update_client


def client_choices() -> list[str]:
    setup_database()
    clients = list_clients()
    return [build_choice(c.get("name", ""), c.get("cpf", "")) for c in clients]


def list_clients_rows() -> list[list]:
    setup_database()
    clients = list_clients()
    return clients_to_table(clients)


def load_client_for_edit(client_choice: str):
    from src.services.client_choice_service import extract_cpf_from_choice

    cpf = extract_cpf_from_choice(client_choice)
    data = get_client_data(cpf)
    if not data:
        return "", "", 0.0, 0, 0, "male", 1, "own", "no_inf", "no_inf"
    return (
        data.get("name", ""),
        data.get("cpf", ""),
        data.get("income", 0.0),
        data.get("age", 0),
        data.get("score", 0),
        data.get("sex") or "male",
        data.get("job") if data.get("job") is not None else 1,
        data.get("housing") or "own",
        data.get("saving_accounts") or "no_inf",
        data.get("checking_account") or "no_inf",
    )


def create_client_and_refresh(
    name,
    cpf,
    income,
    age,
    score,
    sex,
    job,
    housing,
    saving_accounts,
    checking_account,
    current_selection,
    edit_selection,
):
    setup_database()
    name = str(name).strip()
    cpf = format_cpf_input(cpf)

    if not is_cpf_complete(cpf):
        markdown = "### Cadastro\n**Status:** ⛔ CPF inválido. Use o formato XXX.XXX.XXX-XX"
        choices = client_choices()
        clients_rows = list_clients_rows()
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
        sex=str(sex) if sex is not None else None,
        job=int(job) if job is not None else None,
        housing=str(housing) if housing is not None else None,
        saving_accounts=str(saving_accounts) if saving_accounts is not None else None,
        checking_account=str(checking_account) if checking_account is not None else None,
    )

    emoji = "✅" if res.get("success") else "⛔"
    msg = res.get("message", "")
    markdown = f"### Cadastro\n**Status:** {emoji} {msg}"

    choices = client_choices()
    preferred = build_choice(name, cpf) if res.get("success") else current_selection
    if preferred not in choices:
        preferred = choices[0] if choices else None

    clients_rows = list_clients_rows()
    edit_value = preferred if preferred in choices else (choices[0] if choices else None)

    # Sucesso: fecha modal e volta para lista. Falha: mantém modal para correção.
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


def update_client_and_refresh(
    edit_choice,
    name,
    cpf,
    income,
    age,
    score,
    sex,
    job,
    housing,
    saving_accounts,
    checking_account,
    main_selection,
    edit_selection,
):
    from src.services.client_choice_service import extract_cpf_from_choice

    old_cpf = extract_cpf_from_choice(edit_choice)
    setup_database()

    cpf = format_cpf_input(cpf)
    if not is_cpf_complete(cpf):
        markdown = "### Edição\n**Status:** ⛔ CPF inválido. Use o formato XXX.XXX.XXX-XX"
        choices = client_choices()
        clients_rows = list_clients_rows()
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
        sex=str(sex) if sex is not None else None,
        job=int(job) if job is not None else None,
        housing=str(housing) if housing is not None else None,
        saving_accounts=str(saving_accounts) if saving_accounts is not None else None,
        checking_account=str(checking_account) if checking_account is not None else None,
    )

    emoji = "✅" if res.get("success") else "⛔"
    msg = res.get("message", "")
    markdown = f"### Edição\n**Status:** {emoji} {msg}"

    choices = client_choices()
    preferred = build_choice(str(name).strip(), str(cpf).strip()) if res.get("success") else edit_choice
    if preferred not in choices:
        preferred = choices[0] if choices else None

    clients_rows = list_clients_rows()

    main_value = preferred if preferred in choices else main_selection
    edit_value = preferred if preferred in choices else edit_selection

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
