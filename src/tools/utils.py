import datetime
import uuid

def validate_cpf_format(cpf):
    import re
    pattern = r'\d{3}\.\d{3}\.\d{3}-\d{2}'
    return bool(re.match(pattern, cpf))

def calculate_dti(income, loan_amount):
    if income == 0: return 999.9
    return round(loan_amount / income, 2)

def check_legal_age(age):
    return age >= 18

def format_currency(amount):
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generate_protocol_id():
    return str(uuid.uuid4())[:8].upper()

def check_blacklist_score(score):
    MINIMUM_SCORE = 300
    return score >= MINIMUM_SCORE