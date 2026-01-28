import joblib
import pandas as pd
import os
from typing import Any, Optional
import math

# Caminho para o modelo
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../models/credit_risk_model.pkl')

# Caminho para o dataset usado no notebook (para reconstruir as features do treino)
DATA_PATH = os.path.join(os.path.dirname(__file__), '../../data/credit_data.csv')

# Variável global para carregar o modelo apenas uma vez (cache)
_model = None

# Cache das colunas/features esperadas pelo modelo do notebook
_notebook_feature_columns: Optional[list[str]] = None

def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Modelo não encontrado em {MODEL_PATH}. Rode o setup_model.py primeiro.")
        _model = joblib.load(MODEL_PATH)
    return _model


def _build_simple_features(*, age: int, income: float, loan_amount: float, duration: int, history_score: int) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "age": age,
                "income": income,
                "loan_amount": loan_amount,
                "duration": duration,
                "credit_history_score": history_score,
            }
        ]
    )


def _apply_notebook_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """Replica o pré-processamento do notebook (Age_cat + dummies + drops).

    Espera colunas (padrão German Credit):
      Age, Sex, Job, Housing, Saving accounts, Checking account, Credit amount, Duration, Purpose, Risk
    """
    # Age_cat
    interval = (18, 25, 35, 60, 120)
    cats = ["Student", "Young", "Adult", "Senior"]
    if "Age_cat" not in df.columns:
        df["Age_cat"] = pd.cut(df["Age"], interval, labels=cats)
    df["Age_cat"] = df["Age_cat"].astype("object").fillna("Student")

    # NAs
    df["Saving accounts"] = df["Saving accounts"].fillna("no_inf")
    df["Checking account"] = df["Checking account"].fillna("no_inf")

    # Dummies (iguais ao notebook)
    df = df.merge(pd.get_dummies(df.Purpose, drop_first=True, prefix="Purpose"), left_index=True, right_index=True)
    df = df.merge(pd.get_dummies(df.Sex, drop_first=True, prefix="Sex"), left_index=True, right_index=True)
    df = df.merge(pd.get_dummies(df.Housing, drop_first=True, prefix="Housing"), left_index=True, right_index=True)
    df = df.merge(
        pd.get_dummies(df["Saving accounts"], drop_first=True, prefix="Savings"),
        left_index=True,
        right_index=True,
    )

    # Dummies de Risk: aqui fazemos manual para garantir colunas mesmo em 1 linha
    if "Risk" in df.columns:
        df["Risk_bad"] = (df["Risk"] == "bad").astype(int)
        df["Risk_good"] = (df["Risk"] == "good").astype(int)

    df = df.merge(
        pd.get_dummies(df["Checking account"], drop_first=True, prefix="Check"),
        left_index=True,
        right_index=True,
    )
    df = df.merge(pd.get_dummies(df["Age_cat"], drop_first=True, prefix="Age_cat"), left_index=True, right_index=True)

    # Drops (iguais ao notebook)
    for col in [
        "Saving accounts",
        "Checking account",
        "Purpose",
        "Sex",
        "Housing",
        "Age_cat",
        "Risk",
        "Risk_good",
    ]:
        if col in df.columns:
            del df[col]

    return df


def _get_notebook_feature_columns() -> list[str]:
    """Descobre a lista de features do modelo do notebook a partir do dataset e do pipeline do notebook."""
    global _notebook_feature_columns
    if _notebook_feature_columns is not None:
        return _notebook_feature_columns

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset não encontrado em {DATA_PATH}. Necessário para reconstruir as features do modelo do notebook."
        )

    # O notebook usa index_col=0
    df = pd.read_csv(DATA_PATH, index_col=0)
    df = _apply_notebook_preprocessing(df)

    if "Risk_bad" not in df.columns:
        raise RuntimeError("Pré-processamento do notebook não gerou a coluna 'Risk_bad'.")

    _notebook_feature_columns = df.drop("Risk_bad", axis=1).columns.tolist()
    return _notebook_feature_columns


def _build_notebook_features(
    *,
    age: int,
    loan_amount: float,
    duration: int,
    purpose: str = "radio/TV",
    sex: str = "male",
    housing: str = "own",
    saving_accounts: str = "no_inf",
    checking_account: str = "no_inf",
    job: int = 1,
) -> pd.DataFrame:
    feature_columns = _get_notebook_feature_columns()

    # No notebook, "Credit amount" foi transformado com np.log
    loan_amount = float(loan_amount)
    credit_amount_log = math.log(loan_amount) if loan_amount > 0 else 0.0

    raw = pd.DataFrame(
        [
            {
                "Age": int(age),
                "Sex": str(sex),
                "Job": int(job),
                "Housing": str(housing),
                "Saving accounts": None if saving_accounts is None else str(saving_accounts),
                "Checking account": None if checking_account is None else str(checking_account),
                "Credit amount": float(credit_amount_log),
                "Duration": int(duration),
                "Purpose": str(purpose),
                # Dummy: usado apenas para criar Risk_bad/Risk_good e depois removido
                "Risk": "good",
            }
        ]
    )

    processed = _apply_notebook_preprocessing(raw)

    # Garante que Risk_bad exista para ser descartado como no treino
    if "Risk_bad" not in processed.columns:
        processed["Risk_bad"] = 0

    X_df = processed.drop("Risk_bad", axis=1)
    # Alinha exatamente com as colunas do treino (ordem e presença)
    X_df = X_df.reindex(columns=feature_columns, fill_value=0)
    return X_df

# TOOL 4: Prever Risco de Crédito
def predict_credit_risk(
    age,
    income,
    loan_amount,
    duration,
    history_score,
    *,
    purpose: str = "radio/TV",
    sex: str = "male",
    housing: str = "own",
    saving_accounts: str = "no_inf",
    checking_account: str = "no_inf",
    job: int = 1,
):
    """
    Usa o modelo ML para prever risco.
    Retorna: 0 (Aprovado/Baixo Risco) ou 1 (Reprovado/Alto Risco)
    """
    model = _load_model()

    # Normaliza entradas opcionais (evita categorias "None")
    if purpose is None:
        purpose = "radio/TV"
    if sex is None:
        sex = "male"
    if housing is None:
        housing = "own"
    if saving_accounts is None:
        saving_accounts = "no_inf"
    if checking_account is None:
        checking_account = "no_inf"
    if job is None:
        job = 1

    # Compatibilidade:
    # - Modelo antigo (setup_model.py): 5 features com DataFrame
    # - Modelo do notebook: 24 features com dummies e Age_cat
    expected_features = getattr(model, "n_features_in_", None)
    feature_names_in = getattr(model, "feature_names_in_", None)

    if expected_features == 5 or (isinstance(feature_names_in, (list, tuple)) and len(feature_names_in) == 5):
        input_data: Any = _build_simple_features(
            age=int(age),
            income=float(income),
            loan_amount=float(loan_amount),
            duration=int(duration),
            history_score=int(history_score),
        )
    else:
        # Defaults para campos que existem no dataset do notebook mas não são coletados pela UI/DB atual
        input_data = _build_notebook_features(
            age=int(age),
            loan_amount=float(loan_amount),
            duration=int(duration),
            purpose=purpose,
            sex=sex,
            housing=housing,
            saving_accounts=saving_accounts,
            checking_account=checking_account,
            job=int(job) if job is not None else 1,
        )

        if expected_features is not None and expected_features != input_data.shape[1]:
            raise ValueError(
                f"Modelo espera {expected_features} features, mas o pré-processamento gerou {input_data.shape[1]}. "
                "Verifique se o models/credit_risk_model.pkl corresponde ao pipeline do notebook e se data/credit_data.csv é o mesmo usado no treino."
            )

    # Se o modelo foi treinado com X como ndarray (ex.: notebook usa .values), evitar warning passando ndarray.
    X = input_data
    if expected_features is not None and expected_features != 5 and isinstance(input_data, pd.DataFrame):
        X = input_data.values

    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0][1]  # Chance de ser risco (classe 1)
    
    return {
        "risk_prediction": int(prediction),
        "risk_probability": float(probability),
        "status": "HIGH_RISK" if prediction == 1 else "LOW_RISK"
    }