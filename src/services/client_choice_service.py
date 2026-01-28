from __future__ import annotations


def extract_cpf_from_choice(choice: str) -> str:
    """Extrai CPF do formato: 'Nome | XXX.XXX.XXX-XX'."""
    if not choice:
        return ""
    if "|" in choice:
        return choice.split("|", 1)[1].strip()
    return str(choice).strip()


def build_choice(name: str, cpf: str) -> str:
    return f"{(name or '').strip()} | {(cpf or '').strip()}".strip()
