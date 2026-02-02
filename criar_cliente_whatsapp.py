import sqlite3

con = sqlite3.connect("database.db")
cur = con.cursor()

cur.execute("SELECT id FROM clientes WHERE email = 'whatsapp@barber'")
existe = cur.fetchone()

if not existe:
    cur.execute("""
        INSERT INTO clientes (nome, email, telefone, sexo, data_nascimento, senha)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "Cliente WhatsApp",
        "whatsapp@barber",
        "000000000",
        "N",
        "1900-01-01",
        "BLOQUEADO"
    ))

    con.commit()
    print("Cliente WhatsApp criado")
else:
    print("Cliente WhatsApp já existe")

con.close()
