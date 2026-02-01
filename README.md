# Sistema Agêntico de Crédito (Credit Risk)

Projeto educacional/demonstrativo de um **pipeline de decisão de crédito** com **agentes**, **SQLite** e **modelo de Machine Learning**, exposto via **UI Gradio** e orquestrado por **LLM (Google Gemini)**.

> Objetivo: simular um fluxo completo de análise (auditoria → compliance → risco → emissão) operado por um LLM que coordena ferramentas locais.

## Principais recursos

- **Orquestrador LLM** (Gemini 2.0 Flash) que decide dinamicamente quais agentes chamar.
- **Agentes Locais**:
  - Auditoria (validação cadastral)
  - Compliance (regras/regulatórias)
  - Emissão/contrato (aprovação e protocolo)
- **Análise de Risco ML**: Modelo RandomForest e cálculo de DTI (Debt-to-Income).
- **Persistência em SQLite** com histórico de solicitações.
- **Interface Gradio** para interação amigável.

## Stack

- Python 3.10+
- **Google Generative AI** (Gemini)
- Pandas / NumPy / scikit-learn
- SQLite
- Gradio
- python-dotenv

## Arquitetura (alto nível)

1. **UI (Gradio)** ou **Scripts** coletam CPF/valor/prazo.
2. **CreditSystemOrchestrator** recebe o pedido e usa o LLM para decidir os passos:
   - Chama `check_audit` para validar cliente.
   - Chama `check_compliance` para regras de negócio.
   - Chama `analyze_risk` para ML e cálculo financeiro.
   - Decide entre `issue_contract` (Aprovar) ou `deny_request` (Negar).
3. **Banco SQLite** registra cada tentativa e resultado.

## Pré-requisitos

- Python 3.10 ou superior.
- Uma **API Key do Google Gemini** (Google AI Studio).

## Instalação e Configuração

### 1. Configurar Entorno (Windows/PowerShell)

Recomendamos usar um ambiente virtual (`venv`) para isolar as dependências.

```powershell
# 1. Crie o ambiente virtual (caso não exista)
python -m venv venv

# 2. Ative o ambiente
.\venv\Scripts\Activate.ps1
```

### 2. Instalar Dependências

Com o ambiente ativo:

```powershell
pip install -r requirements.txt
```

### 3. Configurar API Key

Crie um arquivo chamado `.env` na raiz do projeto e adicione sua chave:

```ini
GOOGLE_API_KEY=sua_chave_aqui_sem_aspas
```

### 4. Preparar Modelo e Banco de Dados

Gere o modelo de Machine Learning e o banco de dados inicial:

```powershell
python setup_model.py
```
> Isso criará `models/credit_risk_model.pkl` e `database/bank_system.db`.

---

## Como Executar

### Opção 1: Verificar Orquestração (Terminal)

Para testar o fluxo completo via terminal (sem interface gráfica), rode o script de verificação:

```powershell
python src/verify_orchestrator.py
```
> Este script simula um pedido de crédito e exibe o "raciocínio" do LLM e o resultado final no console.

### Opção 2: Rodar a Interface Web (Gradio)

Para usar a aplicação completa no navegador:

```powershell
python src/app.py
```
> O terminal exibirá uma URL local (ex.: `http://127.0.0.1:7860`). Acesse-a para interagir com o sistema.

---

## Troubleshooting

### Erro: `ModuleNotFoundError`
Certifique-se de estar rodando os comandos **da raiz do projeto** e com o **venv ativo**. 

### Erro: `GoogleGenerativeAI Error` ou `ResourceExhausted`
Verifique se sua **API Key** está correta no arquivo `.env`. Erros de "ResourceExhausted" indicam que você atingiu o limite gratuito de requisições por minuto do Gemini. Aguarde alguns instantes e tente novamente.

### Erro: `UnicodeEncodeError` (Windows)
Se tiver problemas com emojis no terminal do Windows:
```powershell
$env:PYTHONIOENCODING='utf-8'
python src/verify_orchestrator.py
```

## Estrutura de Pastas

- `src/agents/`: Lógica do Orquestrador e Agentes.
- `src/tools/`: Ferramentas de ML, Banco de Dados e Utils.
- `src/ui/`: Código da interface Gradio.
- `models/`: Artefato do modelo ML treinado.
- `database/`: Arquivo SQLite.
