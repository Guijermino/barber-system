import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS barbeiros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    senha TEXT NOT NULL
)
""")

cur.execute("""
INSERT INTO barbeiros (usuario, senha)
VALUES ('mathias', '1234')
""")

con.commit()
con.close()

print("Barbeiro criado com sucesso")
