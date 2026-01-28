import joblib
import pandas as pd
import os

# Caminho para o modelo
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../models/credit_risk_model.pkl')

# Variável global para carregar o modelo apenas uma vez (cache)
_model = None

def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Modelo não encontrado em {MODEL_PATH}. Rode o setup_model.py primeiro.")
        _model = joblib.load(MODEL_PATH)
    return _model

# TOOL 4: Prever Risco de Crédito
def predict_credit_risk(age, income, loan_amount, duration, history_score):
    """
    Usa o modelo ML para prever risco.
    Retorna: 0 (Aprovado/Baixo Risco) ou 1 (Reprovado/Alto Risco)
    """
    model = _load_model()
    
    # Criar DataFrame com as mesmas colunas usadas no treino
    input_data = pd.DataFrame([{
        'age': age,
        'income': income,
        'loan_amount': loan_amount,
        'duration': duration,
        'credit_history_score': history_score
    }])
    
    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1] # Chance de ser risco (classe 1)
    
    return {
        "risk_prediction": int(prediction),
        "risk_probability": float(probability),
        "status": "HIGH_RISK" if prediction == 1 else "LOW_RISK"
    }