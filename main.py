import asyncio
from src.agents.orchestrator import CreditSystemOrchestrator
from src.tools.db_tools import get_client_data

# --- FIX PARA WINDOWS ---
# Necessário para que subprocessos (MCP) funcionem corretamente no Windows
import sys
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    system = CreditSystemOrchestrator()
    
    # CENÁRIO 1: Alice
    cpf = "111.222.333-44"
    client_data = get_client_data(cpf)
    if not client_data:
        print(f"❌ Cliente com CPF {cpf} não encontrado. Cadastre antes de testar.")
        return

    request_1 = {
        **client_data,
        "cpf": cpf,
        "loan_amount": 10000.0,
        "duration": 24,
        "purpose": "radio/TV",
    }
    
    # Execução Async
    print(">>> CASO 1: Alice")
    resultado1 = await system.handle_request(request_1)
    print(f"RESULTADO FINAL: {resultado1}\n")

if __name__ == "__main__":
    asyncio.run(main())