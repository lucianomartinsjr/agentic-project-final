from __future__ import annotations


def clients_to_table(clients: list[dict]) -> list[list]:
    return [
        [
            c.get("id"),
            c.get("name"),
            c.get("cpf"),
            c.get("income"),
            c.get("age"),
            c.get("score"),
            c.get("sex"),
            c.get("job"),
            c.get("housing"),
            c.get("saving_accounts"),
            c.get("checking_account"),
        ]
        for c in clients
    ]


def applications_to_table(apps: list[dict]) -> list[list]:
    return [
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
