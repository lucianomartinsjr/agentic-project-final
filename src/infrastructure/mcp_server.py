from mcp.server.fastmcp import FastMCP
from src.tools.db_tools import get_client_data, log_application_attempt
from src.tools.ml_tools import predict_credit_risk
from src.tools.utils import calculate_dti

# Inicializa o servidor MCP com nome "CreditRiskTools"
mcp = FastMCP("CreditRiskTools")

# --- REGISTRO DE FERRAMENTAS ---
# Decoramos as funções existentes para expô-las via protocolo

@mcp.tool()
def get_client_cpf(cpf: str) -> str:
    """Busca dados do cliente no DB via CPF."""
    # Wrapper para converter o retorno em string/json compatível
    result = get_client_data(cpf)
    return str(result) if result else "Not Found"

@mcp.tool()
def calculate_debt_ratio(income: float, loan_amount: float) -> float:
    """Calcula DTI."""
    return calculate_dti(income, loan_amount)

@mcp.tool()
def analyze_risk(age: int, income: float, loan_amount: float, duration: int, score: int) -> str:
    """Executa o modelo de ML para prever risco."""
    result = predict_credit_risk(age, income, loan_amount, duration, score)
    return str(result)

# Se rodarmos esse arquivo diretamente, ele inicia o servidor
if __name__ == "__main__":
    # Isso inicia o servidor em modo Stdio (Standard IO) esperando conexão
    mcp.run()