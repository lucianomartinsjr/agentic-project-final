import datetime
import uuid

# TOOL 5: Validar formato de CPF
def validate_cpf_format(cpf):
    """Verifica se o CPF tem o formato XXX.XXX.XXX-XX."""
    import re
    pattern = r'\d{3}\.\d{3}\.\d{3}-\d{2}'
    return bool(re.match(pattern, cpf))

# TOOL 6: Calcular Razão Dívida/Renda (Debt-to-Income Ratio)
def calculate_dti(income, loan_amount):
    """Calcula o comprometimento da renda."""
    if income == 0: return 999.9 # Evita divisão por zero
    return round(loan_amount / income, 2)

# TOOL 7: Verificar Regra de Idade Mínima
def check_legal_age(age):
    """Verifica se é maior de 18 anos."""
    return age >= 18

# TOOL 8: Formatar Moeda (Para exibição final)
def format_currency(amount):
    """Formata float para string de moeda BRL."""
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# TOOL 9: Gerar ID de Protocolo Único
def generate_protocol_id():
    """Gera um ID único para o atendimento."""
    return str(uuid.uuid4())[:8].upper()

# TOOL 10: Verificar Score (Blacklist imediata)
def check_blacklist_score(score):
    """Se o score for muito baixo, reprova imediatamente sem gastar ML."""
    MINIMUM_SCORE = 300
    return score >= MINIMUM_SCORE