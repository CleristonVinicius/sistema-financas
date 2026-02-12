# ============================
# Ajuste Tabela Usuários
# ============================
import sqlite3

def get_db():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn

def ajusta_tabela_usuarios():
    conn = get_db()
    cur = conn.cursor()

    # email
    try:
        cur.execute("ALTER TABLE usuarios ADD COLUMN email TEXT;")
        print("Coluna 'email' adicionada.")
    except sqlite3.OperationalError:
        print("Coluna 'email' já existe.")

    # foto_url
    try:
        cur.execute("ALTER TABLE usuarios ADD COLUMN foto_url TEXT;")
        print("Coluna 'foto_url' adicionada.")
    except sqlite3.OperationalError:
        print("Coluna 'foto_url' já existe.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    ajusta_tabela_usuarios()
