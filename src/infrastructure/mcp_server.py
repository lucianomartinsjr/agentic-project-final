import sys
import os
import io
import builtins

original_stdout = sys.stdout

def print(*args, **kwargs):
    if kwargs.get("file") is None or kwargs.get("file") == sys.stdout:
        kwargs["file"] = sys.stderr
    
    f = kwargs.get("file", sys.stderr)
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    try:
        f.write(sep.join(map(str, args)) + end)
    except Exception:
        pass 

builtins.print = print


import json
import concurrent.futures
import traceback

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

class StderrPrinter:
    def write(self, message):
        sys.stderr.write(message)
    def flush(self):
        sys.stderr.flush()

try:
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass




from mcp.server.fastmcp import FastMCP
from src.tools.db_tools import get_client_data, log_application_attempt
from src.tools.ml_tools import predict_credit_risk
from src.tools.utils import calculate_dti

mcp = FastMCP("CreditRiskTools")

_PREDICT_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1)

try:
    predict_credit_risk(30, 5000.0, 10000.0, 24, 750)
except Exception:
    pass

@mcp.tool()
def get_client_cpf(cpf: str) -> str:
    try:
        result = get_client_data(cpf)
        return str(result) if result else "Not Found"
    except Exception as e:
        return f"ERROR in get_client_cpf: {str(e)}"

@mcp.tool()
def calculate_debt_ratio(income: float, loan_amount: float) -> float:
    try:
        return calculate_dti(income, loan_amount)
    except Exception as e:
        return -1.0

@mcp.tool()
def analyze_risk(
    age: int,
    income: float,
    loan_amount: float,
    duration: int,
    score: int,
    purpose: str = "radio/TV",
    sex: str = "male",
    housing: str = "own",
    saving_accounts: str = "no_inf",
    checking_account: str = "no_inf",
    job: int = 1,
) -> str:
    try:
        future = _PREDICT_EXECUTOR.submit(
            predict_credit_risk,
            int(age),
            float(income),
            float(loan_amount),
            int(duration),
            int(score),
            purpose=purpose,
            sex=sex,
            housing=housing,
            saving_accounts=saving_accounts,
            checking_account=checking_account,
            job=job,
        )

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
    mcp.run()