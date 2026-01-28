import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# 1. Garantir que as pastas existem
os.makedirs('data', exist_ok=True)
os.makedirs('models', exist_ok=True)

print("⏳ Gerando dataset sintético baseado no German Credit Data...")

# Criando um dataset simples para fins didáticos (simulando o kaggle)
# Variáveis: Idade, Renda, Valor Empréstimo, Duração (meses), Histórico (0=Ruim, 1=Bom)
data = {
    'age': np.random.randint(18, 70, 1000),
    'income': np.random.randint(1500, 15000, 1000),
    'loan_amount': np.random.randint(1000, 50000, 1000),
    'duration': np.random.randint(6, 60, 1000),
    'credit_history_score': np.random.randint(300, 850, 1000) # Score tipo Serasa
}
df = pd.DataFrame(data)

# Criar uma target "Risk" (0 = Bom Pagador, 1 = Risco de Calote)
# Regra lógica simples apenas para o modelo aprender algo correlacionado
df['risk'] = np.where(
    (df['credit_history_score'] < 500) | (df['loan_amount'] > df['income'] * 10), 
    1, 0
)

# Salvar CSV para referência
df.to_csv('data/credit_data.csv', index=False)

# 2. Treinamento
X = df.drop('risk', axis=1)
y = df['risk']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("🧠 Treinando Random Forest...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

accuracy = model.score(X_test, y_test)
print(f"✅ Modelo treinado com Acurácia: {accuracy:.2f}")

# 3. Salvar o modelo (Serialização)
model_path = 'models/credit_risk_model.pkl'
joblib.dump(model, model_path)
print(f"💾 Modelo salvo em: {model_path}")