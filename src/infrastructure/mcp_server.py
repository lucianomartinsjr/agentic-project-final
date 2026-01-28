import sys
import os
import json
import concurrent.futures

# Garante que `import src.*` funcione quando este arquivo é executado como script
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

sys.stdout.reconfigure(encoding='utf-8')
original_stdout = sys.stdout

class StderrPrinter:
    def write(self, message):
        sys.stderr.write(message)
    def flush(self):
        sys.stderr.flush()


from mcp.server.fastmcp import FastMCP
from src.tools.db_tools import get_client_data, log_application_attempt
from src.tools.ml_tools import predict_credit_risk
from src.tools.utils import calculate_dti

# Inicializa o servidor
mcp = FastMCP("CreditRiskTools")

_PREDICT_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# Warm-up: carrega o modelo uma vez no startup para evitar travas/latência alta no primeiro call.
try:
    predict_credit_risk(30, 5000.0, 10000.0, 24, 750)
except Exception:
    # Se o modelo não existir ainda, a tool retornará erro quando chamada.
    pass

@mcp.tool()
def get_client_cpf(cpf: str) -> str:
    """Busca dados do cliente no DB via CPF."""
    try:
        result = get_client_data(cpf)
        return str(result) if result else "Not Found"
    except Exception as e:
        return f"ERROR in get_client_cpf: {str(e)}"

@mcp.tool()
def calculate_debt_ratio(income: float, loan_amount: float) -> float:
    """Calcula DTI."""
    try:
        return calculate_dti(income, loan_amount)
    except Exception as e:
        return -1.0

@mcp.tool()
def analyze_risk(age: int, income: float, loan_amount: float, duration: int, score: int) -> str:
    """Executa o modelo de ML para prever risco."""
    try:
        future = _PREDICT_EXECUTOR.submit(
            predict_credit_risk,
            int(age),
            float(income),
            float(loan_amount),
            int(duration),
            int(score),
        )

        # Timeout no lado do servidor para evitar travamento infinito
        result = future.result(timeout=20.0)
        return json.dumps(result, ensure_ascii=False)
    except concurrent.futures.TimeoutError:
        return json.dumps(
            {
                "status": "ERROR",
                "risk_probability": 0.0,
                "error_msg": "Timeout interno na inferência do modelo (20s)",
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({
            "status": "ERROR", 
            "risk_probability": 0.0, 
            "error_msg": str(e)
        }, ensure_ascii=False)

if __name__ == "__main__":
    sys.stdout = original_stdout
    mcp.run()