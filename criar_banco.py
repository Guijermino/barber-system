import sqlite3

conexao = sqlite3.connect("database.db")
cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    telefone TEXT NOT NULL,
    sexo TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    senha TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    servicos TEXT NOT NULL,
    data TEXT NOT NULL,
    horario TEXT NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reset_senhas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    token TEXT,
    expira_em TEXT
)
""")



conexao.commit()
conexao.close()

print("Banco de dados criado com sucesso!")