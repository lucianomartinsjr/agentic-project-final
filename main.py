import asyncio
from src.agents.orchestrator import CreditSystemOrchestrator

async def main():
    system = CreditSystemOrchestrator()
    
    # CENÁRIO 1: Alice
    request_1 = {"cpf": "111.222.333-44", "loan_amount": 10000.0, "duration": 24}
    
    # Execução Async
    print(">>> CASO 1: Alice")
    resultado1 = await system.handle_request(request_1)
    print(f"RESULTADO FINAL: {resultado1}\n")

if __name__ == "__main__":
    asyncio.run(main())