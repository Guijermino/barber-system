import sqlite3
con = sqlite3.connect("database.db")
cur = con.cursor()
cur.execute("DELETE FROM reset_senha")
con.commit()
con.close()
print("Tokens antigos apagados")