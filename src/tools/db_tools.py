import sqlite3
import os

# Caminho para o banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), '../../database/bank_system.db')

def _get_connection():
    """Helper interno para conectar ao banco."""
    # Garante que a pasta database existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

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
def log_application_attempt(client_id, amount, status):
    """Simula o registro de uma tentativa de empréstimo no histórico."""
    # Para simplificar, vamos apenas printar, mas num sistema real gravaria no banco
    print(f"📝 LOG DB: Cliente {client_id} tentou {amount}. Status final: {status}")
    return True