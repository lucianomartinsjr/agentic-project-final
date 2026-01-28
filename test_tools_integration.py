from src.tools.db_tools import setup_database, get_client_data
from src.tools.ml_tools import predict_credit_risk
from src.tools.utils import calculate_dti, format_currency

def run_tests():
    print("🔬 Iniciando Testes de Integração das Tools...\n")

    # 1. Teste DB
    print("1. Testando DB Setup...")
    print(setup_database())
    
    print("2. Buscando Cliente 'Alice'...")
    alice = get_client_data('111.222.333-44')
    if alice:
        print(f"   ✅ Cliente encontrado: {alice['name']}")
    else:
        print("   ❌ Erro: Cliente não encontrado.")

    # 2. Teste ML
    print("\n3. Testando Modelo de ML...")
    # Simulando um empréstimo para Alice
    risk = predict_credit_risk(
        age=alice['age'],
        income=alice['income'],
        loan_amount=50000, # Valor alto para tentar forçar risco
        duration=24,
        history_score=alice['score']
    )
    print(f"   ✅ Resultado ML: {risk}")

    # 3. Teste Utils
    print("\n4. Testando Utils...")
    dti = calculate_dti(alice['income'], 50000)
    fmt = format_currency(50000)
    print(f"   ✅ DTI: {dti}")
    print(f"   ✅ Formatação: {fmt}")

if __name__ == "__main__":
    run_tests()