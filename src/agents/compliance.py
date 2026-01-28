from src.tools.utils import validate_cpf_format, check_legal_age, check_blacklist_score

class ComplianceAgent:
    def __init__(self):
        self.name = "Officer de Compliance"

    def process(self, request_context):
        print(f"   [{self.name}] Validando regras regulatórias...")
        
        cpf = request_context.get("cpf")
        age = request_context.get("age")
        score = request_context.get("score")

        if cpf is None or str(cpf).strip() == "":
            return {
                "success": False,
                "message": "CPF não informado.",
                "details": {"compliance_rule": "MISSING_DATA", "field": "cpf"},
            }

        # Regra 1: Validação de CPF (Tool)
        if not validate_cpf_format(str(cpf)):
            return {
                "success": False,
                "message": "Formato de CPF inválido.",
                "details": {
                    "compliance_rule": "CPF_FORMAT",
                    "cpf": cpf,
                },
            }

        if age is None:
            return {
                "success": False,
                "message": "Idade não informada no cadastro.",
                "details": {"compliance_rule": "MISSING_DATA", "field": "age"},
            }
        try:
            age_int = int(age)
        except Exception:
            return {
                "success": False,
                "message": f"Idade inválida ({age}).",
                "details": {"compliance_rule": "INVALID_DATA", "field": "age", "age": age},
            }

        if score is None:
            return {
                "success": False,
                "message": "Score não informado no cadastro.",
                "details": {"compliance_rule": "MISSING_DATA", "field": "score"},
            }
        try:
            score_int = int(score)
        except Exception:
            return {
                "success": False,
                "message": f"Score inválido ({score}).",
                "details": {"compliance_rule": "INVALID_DATA", "field": "score", "score": score},
            }

        # Regra 2: Maioridade Penal (Tool)
        if not check_legal_age(age_int):
            return {
                "success": False,
                "message": f"Cliente menor de idade ({age_int} anos).",
                "details": {
                    "compliance_rule": "LEGAL_AGE",
                    "age": age_int,
                },
            }

        # Regra 3: Blacklist/Score Mínimo (Tool)
        if not check_blacklist_score(score_int):
            return {
                "success": False,
                "message": f"Score abaixo do mínimo permitido ({score_int}).",
                "details": {
                    "compliance_rule": "MIN_SCORE",
                    "score": score_int,
                },
            }

        return {"success": True, "message": "Compliance OK."}