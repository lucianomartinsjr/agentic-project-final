from __future__ import annotations

from src.tools.utils import validate_cpf_format


def format_cpf_input(value: str) -> str:
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


def is_cpf_complete(value: str) -> bool:
    return validate_cpf_format(format_cpf_input(value))
