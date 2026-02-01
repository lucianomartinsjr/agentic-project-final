import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '../../database/bank_system.db')


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    for col_name, col_type in columns.items():
        if col_name in existing:
            continue
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
    conn.commit()

def _get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cpf TEXT UNIQUE,
            income REAL,
            age INTEGER,
            credit_history_score INTEGER,
            sex TEXT,
            job INTEGER,
            housing TEXT,
            saving_accounts TEXT,
            checking_account TEXT
        )
    '''
    )

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpf TEXT,
            client_id INTEGER,
            amount REAL,
            duration INTEGER,
            purpose TEXT,
            sex TEXT,
            job INTEGER,
            housing TEXT,
            saving_accounts TEXT,
            checking_account TEXT,
            status TEXT,
            reason TEXT,
            created_at TEXT
        )
    '''
    )

    _ensure_columns(
        conn,
        "clients",
        {
            "sex": "TEXT",
            "job": "INTEGER",
            "housing": "TEXT",
            "saving_accounts": "TEXT",
            "checking_account": "TEXT",
        },
    )
    _ensure_columns(
        conn,
        "applications",
        {
            "purpose": "TEXT",
            "sex": "TEXT",
            "job": "INTEGER",
            "housing": "TEXT",
            "saving_accounts": "TEXT",
            "checking_account": "TEXT",
        },
    )

    cursor.execute(
        """
        UPDATE clients
        SET
            sex = COALESCE(sex, 'male'),
            job = COALESCE(job, 1),
            housing = COALESCE(housing, 'own'),
            saving_accounts = COALESCE(saving_accounts, 'no_inf'),
            checking_account = COALESCE(checking_account, 'no_inf')
        WHERE sex IS NULL OR job IS NULL OR housing IS NULL OR saving_accounts IS NULL OR checking_account IS NULL
        """
    )
    conn.commit()

    cursor.execute(
        """
        UPDATE clients
        SET age = 30
        WHERE (age IS NULL OR age < 0 OR age > 120)
        """
    )

    cursor.execute(
        """
        UPDATE clients
        SET
            age = 30,
            sex = COALESCE(sex, 'male'),
            job = 3,
            housing = 'free',
            saving_accounts = 'little',
            checking_account = 'little'
                WHERE cpf = '555.666.777-88'
                    AND (
                        age IS NULL OR age < 18 OR age > 120
                        OR job IS NULL OR job != 3
                        OR housing IS NULL OR housing != 'free'
                        OR saving_accounts IS NULL OR saving_accounts != 'little'
                        OR checking_account IS NULL OR checking_account != 'little'
                    )
        """
    )
    conn.commit()
    
    cursor.execute('SELECT count(*) FROM clients')
    if cursor.fetchone()[0] == 0:
        data = [
            (1, 'Alice Silva', '111.222.333-44', 5000.0, 30, 750, 'female', 1, 'own', 'moderate', 'little'),
            (2, 'Bob Santos', '555.666.777-88', 2000.0, 20, 400, 'male', 0, 'rent', 'little', 'no_inf'),
            (3, 'Charlie Souza', '999.888.777-66', 12000.0, 45, 800, 'male', 2, 'own', 'rich', 'moderate'),
        ]
        cursor.executemany('INSERT INTO clients VALUES (?,?,?,?,?,?,?,?,?,?,?)', data)
        conn.commit()
    
    conn.close()
    return "Database setup complete."


def add_client(
    name: str,
    cpf: str,
    income: float,
    age: int,
    score: int,
    sex: str | None = None,
    job: int | None = None,
    housing: str | None = None,
    saving_accounts: str | None = None,
    checking_account: str | None = None,
) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO clients (name, cpf, income, age, credit_history_score, sex, job, housing, saving_accounts, checking_account)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                str(name),
                str(cpf),
                float(income),
                int(age),
                int(score),
                (str(sex) if sex is not None else None),
                (int(job) if job is not None else None),
                (str(housing) if housing is not None else None),
                (str(saving_accounts) if saving_accounts is not None else None),
                (str(checking_account) if checking_account is not None else None),
            ),
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
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, cpf, income, age, credit_history_score, sex, job, housing, saving_accounts, checking_account FROM clients ORDER BY id ASC"
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
            "sex": r["sex"],
            "job": r["job"],
            "housing": r["housing"],
            "saving_accounts": r["saving_accounts"],
            "checking_account": r["checking_account"],
        }
        for r in rows
    ]


def get_client_data(cpf):
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE cpf = ?', (cpf,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "cpf": row[2],
            "income": row[3],
            "age": row[4],
            "score": row[5],
            "sex": row[6] if len(row) > 6 else None,
            "job": row[7] if len(row) > 7 else None,
            "housing": row[8] if len(row) > 8 else None,
            "saving_accounts": row[9] if len(row) > 9 else None,
            "checking_account": row[10] if len(row) > 10 else None,
        }
    return None


def log_application_attempt(*args, **kwargs):
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
        purpose = kwargs.get("purpose")
        sex = kwargs.get("sex")
        job = kwargs.get("job")
        housing = kwargs.get("housing")
        saving_accounts = kwargs.get("saving_accounts")
        checking_account = kwargs.get("checking_account")
        status = kwargs.get("status")
        reason = kwargs.get("reason")

    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            INSERT INTO applications (
                cpf,
                client_id,
                amount,
                duration,
                purpose,
                sex,
                job,
                housing,
                saving_accounts,
                checking_account,
                status,
                reason,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                cpf,
                client_id,
                float(amount) if amount is not None else None,
                int(duration) if duration is not None else None,
                str(purpose) if purpose is not None else None,
                str(sex) if sex is not None else None,
                int(job) if job is not None else None,
                str(housing) if housing is not None else None,
                str(saving_accounts) if saving_accounts is not None else None,
                str(checking_account) if checking_account is not None else None,
                str(status) if status is not None else None,
                reason,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    extra = f" | reason={reason}" if reason else ""
    return True


def list_applications() -> list[dict]:
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


def update_client(
    *,
    old_cpf: str,
    name: str,
    cpf: str,
    income: float,
    age: int,
    score: int,
    sex: str | None = None,
    job: int | None = None,
    housing: str | None = None,
    saving_accounts: str | None = None,
    checking_account: str | None = None,
) -> dict:
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE clients
            SET name = ?,
                cpf = ?,
                income = ?,
                age = ?,
                credit_history_score = ?,
                sex = ?,
                job = ?,
                housing = ?,
                saving_accounts = ?,
                checking_account = ?
            WHERE cpf = ?
            """,
            (
                str(name),
                str(cpf),
                float(income),
                int(age),
                int(score),
                (str(sex) if sex is not None else None),
                (int(job) if job is not None else None),
                (str(housing) if housing is not None else None),
                (str(saving_accounts) if saving_accounts is not None else None),
                (str(checking_account) if checking_account is not None else None),
                str(old_cpf),
            ),
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