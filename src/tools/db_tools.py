import sqlite3
import os
from datetime import datetime

# Caminho para o banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), '../../database/bank_system.db')

def _get_connection():
    """Helper interno para conectar ao banco."""
    # Garante que a pasta database existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# TOOL 1: Inicializar o banco com dados mockados (para teste)
def setup_database():
    """Cria a tabela e insere clientes fictícios se não existirem."""
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cpf TEXT UNIQUE,
            income REAL,
            age INTEGER,
            credit_history_score INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf TEXT,
            client_id INTEGER,
            amount REAL,
            duration INTEGER,
            status TEXT,
            reason TEXT,
            created_at TEXT
        )
    ''')
    
    # Inserindo dados dummy apenas se a tabela estiver vazia
    cursor.execute('SELECT count(*) FROM clients')
    if cursor.fetchone()[0] == 0:
        data = [
            (1, 'Alice Silva', '111.222.333-44', 5000.0, 30, 750), # Bom perfil
            (2, 'Bob Santos', '555.666.777-88', 2000.0, 20, 400),  # Perfil de risco
            (3, 'Charlie Souza', '999.888.777-66', 12000.0, 45, 800) # Perfil excelente
        ]
        cursor.executemany('INSERT INTO clients VALUES (?,?,?,?,?,?)', data)
        conn.commit()
        print("✅ Banco de dados inicializado com dados de teste.")
    
    conn.close()
    return "Database setup complete."


def add_client(name: str, cpf: str, income: float, age: int, score: int) -> dict:
    """Cadastra um novo cliente (ou retorna erro se CPF já existir)."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO clients (name, cpf, income, age, credit_history_score)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (name, cpf, float(income), int(age), int(score)),
        )
        conn.commit()
        return {"success": True, "message": "Cliente cadastrado com sucesso."}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "CPF já cadastrado."}
    except Exception as e:
        return {"success": False, "message": f"Erro ao cadastrar cliente: {str(e)}"}
    finally:
        conn.close()


def list_clients() -> list[dict]:
    """Lista todos os clientes cadastrados."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, cpf, income, age, credit_history_score FROM clients ORDER BY id ASC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "cpf": r["cpf"],
            "income": r["income"],
            "age": r["age"],
            "score": r["credit_history_score"],
        }
        for r in rows
    ]

# TOOL 2: Buscar cliente pelo CPF
def get_client_data(cpf):
    """Busca dados cadastrais de um cliente pelo CPF."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE cpf = ?', (cpf,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0], "name": row[1], "cpf": row[2],
            "income": row[3], "age": row[4], "score": row[5]
        }
    return None

# TOOL 3: Registrar solicitação de empréstimo (Log)
def log_application_attempt(*args, **kwargs):
    """Registra uma tentativa de solicitação.

    Compatível com assinatura antiga:
      log_application_attempt(client_id, amount, status)

    Nova assinatura (recomendada):
      log_application_attempt(cpf=..., client_id=..., amount=..., duration=..., status=..., reason=...)
    """
    if args and len(args) == 3 and not kwargs:
        client_id, amount, status = args
        cpf = None
        duration = None
        reason = None
    else:
        cpf = kwargs.get("cpf")
        client_id = kwargs.get("client_id")
        amount = kwargs.get("amount")
        duration = kwargs.get("duration")
        status = kwargs.get("status")
        reason = kwargs.get("reason")

    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO applications (cpf, client_id, amount, duration, status, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                cpf,
                client_id,
                float(amount) if amount is not None else None,
                int(duration) if duration is not None else None,
                str(status) if status is not None else None,
                reason,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Mantém o comportamento de log no terminal
    extra = f" | reason={reason}" if reason else ""
    print(
        f"📝 LOG DB: CPF {cpf or '-'} (Cliente {client_id or '-'}) tentou {amount}. Status final: {status}{extra}"
    )
    return True


def list_applications() -> list[dict]:
    """Lista histórico de solicitações (mais recentes primeiro)."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, cpf, client_id, amount, duration, status, reason, created_at
        FROM applications
        ORDER BY id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "cpf": r["cpf"],
            "client_id": r["client_id"],
            "amount": r["amount"],
            "duration": r["duration"],
            "status": r["status"],
            "reason": r["reason"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def update_client(*, old_cpf: str, name: str, cpf: str, income: float, age: int, score: int) -> dict:
    """Edita um cliente existente identificado pelo CPF antigo."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE clients
            SET name = ?, cpf = ?, income = ?, age = ?, credit_history_score = ?
            WHERE cpf = ?
            """,
            (str(name), str(cpf), float(income), int(age), int(score), str(old_cpf)),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return {"success": False, "message": "Cliente não encontrado para edição."}
        return {"success": True, "message": "Cliente atualizado com sucesso."}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "CPF já cadastrado (conflito)."}
    except Exception as e:
        return {"success": False, "message": f"Erro ao atualizar cliente: {str(e)}"}
    finally:
        conn.close()