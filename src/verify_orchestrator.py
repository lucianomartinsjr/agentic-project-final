import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.orchestrator import CreditSystemOrchestrator

async def main():
    print("--- 🧪 Verificando LLM Orchestrator ---")
    
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found. Please set it before running.")
        return

    orch = CreditSystemOrchestrator()
    
    request = {
        "id": 1,
        "name": "Alice Silva",
        "cpf": "111.222.333-44", 
        "income": 5000.0,
        "age": 30,
        "score": 750,
        "loan_amount": 10000.0,
        "duration": 24,
        "purpose": "radio/TV",
        "sex": "female",
        "job": 1,
        "housing": "own",
        "saving_accounts": "little",
        "checking_account": "moderate"
    }
    
    try:
        result = await orch.handle_request(request)
        print("\n--- ✅ Resultado Final ---")
        print(result)
    except Exception as e:
        print(f"\n--- ❌ Erro na Execução ---")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
