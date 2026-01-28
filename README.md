# Sistema Agêntico de Crédito (Credit Risk)

Projeto educacional/demonstrativo de um **pipeline de decisão de crédito** com **agentes**, **SQLite** e **modelo de Machine Learning**, exposto via **UI Gradio** e com integração a ferramentas via **MCP (Model Context Protocol)**.

> Objetivo: simular um fluxo completo de análise (auditoria → compliance → risco → emissão) com rastreabilidade (logs em banco) e resultado final amigável.

## Principais recursos

- **Fluxo agêntico** com agentes dedicados:
  - Auditoria (validação cadastral)
  - Compliance (regras/regulatórias)
  - Analista de risco (via MCP com fallback local)
  - Emissão/contrato (aprovação e protocolo)
- **Modelo ML** (RandomForest) para prever risco e probabilidade.
- **Persistência em SQLite** com histórico de solicitações.
- **Interface Gradio** com:
  - Nova solicitação
  - Cadastro/edição de clientes
  - Histórico de aplicações
- **MCP server/client** (stdio) para executar tools (risco/DTI/etc.) com timeout.

## Stack

- Python
- Pandas / NumPy / scikit-learn / joblib
- SQLite
- Gradio
- MCP (`mcp[cli]`)

## Arquitetura (alto nível)

1. **UI (Gradio)** coleta CPF/valor/prazo.
2. **Orchestrator** coordena os agentes:
   - `AuditorAgent` → valida cliente
   - `ComplianceAgent` → regras
   - `RiskAnalystAgent` → chama tool remota via MCP (`analyze_risk`) e calcula DTI
   - `IssuerAgent` → registra aprovação e retorna protocolo
3. **Banco SQLite** registra cada tentativa em `applications`.

Fluxo simplificado:

```
Gradio UI
  -> CreditSystemOrchestrator
      -> AuditorAgent
      -> ComplianceAgent
      -> RiskAnalystAgent
           -> RealMCPClient -> mcp_server.py -> tools (ML/DTI)
           -> fallback local (predict_credit_risk) em caso de falha
      -> IssuerAgent
  -> SQLite (applications)
```

## Estrutura do projeto

- `src/app.py`: entrypoint da UI Gradio
- `src/ui/gradio_app.py`: layout e callbacks
- `src/agents/`: agentes (auditoria, compliance, risco, emissor, orquestrador)
- `src/tools/`: ferramentas locais (DB, ML, utils)
- `src/infrastructure/`: cliente/servidor MCP
- `setup_model.py`: gera dataset sintético e treina o modelo
- `data/credit_data.csv`: dataset sintético gerado
- `models/credit_risk_model.pkl`: artefato do modelo (necessário para inferência)
- `database/bank_system.db`: SQLite criado automaticamente

## Pré-requisitos

- Python 3.10+ (recomendado)
- Windows, macOS ou Linux

> No Windows, o projeto aplica um ajuste de event loop para evitar problemas com subprocessos.

## Instalação

1) (Opcional) Crie e ative um virtualenv

Windows (PowerShell):

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2) Instale dependências

```bash
pip install -r requirements.txt
```

3) Gere/treine o modelo (obrigatório na primeira execução)

```bash
python setup_model.py
```

Isso irá criar:

- `data/credit_data.csv`
- `models/credit_risk_model.pkl`

## Como executar

### 1) Rodar a UI (Gradio)

```bash
python src/app.py
```

O terminal exibirá a URL local (ex.: `http://127.0.0.1:7860`).

### 2) Rodar um fluxo de exemplo via script

O arquivo `main.py` contém um exemplo simples chamando o orquestrador:

```bash
python main.py
```

### 3) Rodar testes de integração (tools)

```bash
python test_tools_integration.py
```

## Variáveis de ambiente (MCP)

Você pode ajustar timeouts do MCP sem alterar código:

- `MCP_INIT_TIMEOUT_S` (default: 10)
- `MCP_TOOL_TIMEOUT_S` (default: 10)

Exemplo (Windows PowerShell):

```powershell
$env:MCP_TOOL_TIMEOUT_S = "20"
python src/app.py
```

## Modelo de risco (ML)

A inferência local acontece em `src/tools/ml_tools.py` via `predict_credit_risk(...)`, retornando:

- `risk_prediction`: `0` (baixo risco) ou `1` (alto risco)
- `risk_probability`: probabilidade da classe de risco (classe `1`)
- `status`: `LOW_RISK` ou `HIGH_RISK`

Se o arquivo `models/credit_risk_model.pkl` não existir, a tool lança:

- `FileNotFoundError`: rode `python setup_model.py`

## Banco de dados (SQLite)

O SQLite fica em:

- `database/bank_system.db`

Tabelas:

- `clients`: cadastro do cliente
- `applications`: histórico de solicitações

Cada solicitação registra campos como `cpf`, `amount`, `duration`, `status` e `reason`.

> Em aprovações, `reason` armazena um JSON com `risk_prediction`, `risk_probability` e `status` do ML.

## Troubleshooting

### Modelo não encontrado

Erro típico:

- `Modelo não encontrado em .../models/credit_risk_model.pkl. Rode o setup_model.py primeiro.`

Solução:

```bash
python setup_model.py
```

### Travamento/timeout na análise via MCP

Se o MCP falhar/timeout, o `RiskAnalystAgent` faz fallback para inferência local.

Você pode aumentar o timeout:

```powershell
$env:MCP_TOOL_TIMEOUT_S = "20"
```

### ImportError / `src.*` não encontrado

A UI (`src/app.py`) já garante que o project root esteja no `sys.path`. Se você executar módulos diretamente, prefira rodar pela raiz do repo:

```bash
python src/app.py
```

## Observações importantes

- Este projeto é **didático**: dados e CPFs são fictícios e o modelo é treinado em dataset sintético.
- Não use em produção sem revisão completa de segurança, privacidade e governança de modelos.

