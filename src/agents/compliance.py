from src.tools.utils import validate_cpf_format, check_legal_age, check_blacklist_score

class ComplianceAgent:
    def __init__(self):
        self.name = "Officer de Compliance"

    def process(self, request_context):
        print(f"   [{self.name}] Validando regras regulatórias...")
        
        cpf = request_context.get('cpf')
        age = request_context.get('age')
        score = request_context.get('score')

        # Regra 1: Validação de CPF (Tool)
        if not validate_cpf_format(cpf):
            return {
                "success": False,
                "message": "Formato de CPF inválido.",
                "details": {
                    "compliance_rule": "CPF_FORMAT",
                    "cpf": cpf,
                },
            }

        # Regra 2: Maioridade Penal (Tool)
        if not check_legal_age(age):
            return {
                "success": False,
                "message": f"Cliente menor de idade ({age} anos).",
                "details": {
                    "compliance_rule": "LEGAL_AGE",
                    "age": age,
                },
            }

        # Regra 3: Blacklist/Score Mínimo (Tool)
        if not check_blacklist_score(score):
            return {
                "success": False,
                "message": f"Score abaixo do mínimo permitido ({score}).",
                "details": {
                    "compliance_rule": "MIN_SCORE",
                    "score": score,
                },
            }

        return {"success": True, "message": "Compliance OK."}