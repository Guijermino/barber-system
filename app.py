from flask import Flask, render_template, request, redirect, session
import sqlite3
import secrets
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)
app.secret_key = "chave_super_secreta_123"

def gerar_horarios(data, duracao):
    horarios = []
    inicio = 8 * 60   
    fim = 19 * 60     

    atual = inicio
    while atual + duracao <= fim:
        h = atual // 60
        m = atual % 60
        horarios.append(f"{h:02d}:{m:02d}")
        atual += 15   

    return horarios

@app.route("/barbeiro-bloquear", methods=["POST"])
def barbeiro_bloquear():

    if "barbeiro" not in session:
        return redirect("/barbeiro-login")

    data = request.form["data"]
    horario = request.form["horario"]

    conexao = sqlite3.connect("database.db")
    cursor = conexao.cursor()

    cursor.execute("""
        INSERT INTO agendamentos (cliente_id, servicos, data, horario)
        VALUES (?, ?, ?, ?)
    """, (0, "HORÁRIO BLOQUEADO", data, horario))

    conexao.commit()
    conexao.close()

    return redirect("/barbeiro")

@app.route("/barbeiro-login", methods=["GET","POST"])
def barbeiro_login():

    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        con = sqlite3.connect("database.db")
        cur = con.cursor()

        cur.execute("SELECT id FROM barbeiros WHERE usuario = ? AND senha = ?", (usuario, senha))
        b = cur.fetchone()
        con.close()

        if b:
            session["barbeiro"] = True
            return redirect("/barbeiro")
        else:
            return "Login inválido"

    return render_template("barbeiro_login.html")


@app.route("/meus-agendamentos")
def meus_agendamentos():

    if "usuario_id" not in session:
        return redirect("/")

    conexao = sqlite3.connect("database.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, data, horario, servicos
        FROM agendamentos
        WHERE cliente_id = ?
        ORDER BY data, horario
    """, (session["usuario_id"],))

    agendamentos = cursor.fetchall()
    conexao.close()

    return render_template("meus_agendamentos.html", agendamentos=agendamentos)

@app.route("/barbeiro-cancelar/<int:id>")
def barbeiro_cancelar(id):

    if "barbeiro" not in session:
        return redirect("/barbeiro-login")

    conexao = sqlite3.connect("database.db")
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM agendamentos WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()

    return redirect("/barbeiro")


@app.route("/redefinir/<token>", methods=["GET","POST"])
def redefinir(token):

    conexao = sqlite3.connect("database.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT email, expira_em
        FROM reset_senhas
        WHERE token = ?
    """, (token,))

    dados = cursor.fetchone()

    if not dados:
        return "Link inválido"

    email, expira = dados

    if datetime.now() > datetime.fromisoformat(expira):
        return "Link expirado"

    if request.method == "POST":
        nova = request.form["senha"]

        cursor.execute("""
            UPDATE clientes SET senha = ?
            WHERE email = ?
        """, (nova, email))

        cursor.execute("DELETE FROM reset_senhas WHERE token = ?", (token,))

        conexao.commit()
        conexao.close()

        return redirect("/")

    conexao.close()
    return render_template("nova_senha.html")

@app.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():

    if request.method == "POST":
        email = request.form["email"]

        token = str(uuid.uuid4())
        expira = datetime.now() + timedelta(minutes=15)

        conexao = sqlite3.connect("database.db")
        cursor = conexao.cursor()

        cursor.execute("DELETE FROM reset_senhas WHERE email = ?", (email,))
        cursor.execute("""
            INSERT INTO reset_senhas (email, token, expira_em)
            VALUES (?, ?, ?)
        """, (email, token, expira))

        conexao.commit()
        conexao.close()

        link = f"https://barber-system-production-8a5f.up.railway.app/redefinir/{token}"

        return f"""
        <h3>Link para redefinir sua senha:</h3>
        <a href="{link}">{link}</a>
        """

    return render_template("esqueci_senha.html")

@app.route("/sucesso")
def sucesso():

    if "usuario_id" not in session:
        return redirect("/")

    conexao = sqlite3.connect("database.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT servicos, data, horario
        FROM agendamentos
        WHERE cliente_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (session["usuario_id"],))

    agendamento = cursor.fetchone()
    conexao.close()

    return render_template(
        "sucesso.html",
        nome=session["usuario_nome"],
        telefone=session["usuario_telefone"],
        servicos=agendamento[0],
        data=agendamento[1],
        horario=agendamento[2]
    )

from datetime import date

@app.route("/barbeiro")
def barbeiro():

    if "barbeiro" not in session:
        return redirect("/barbeiro-login")

    hoje = date.today().isoformat()  

    conexao = sqlite3.connect("database.db")
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT agendamentos.id, agendamentos.data,
               agendamentos.horario, agendamentos.servicos, clientes.nome, clientes.telefone,
        FROM agendamentos
        JOIN clientes ON agendamentos.cliente_id = clientes.id
        ORDER BY agendamentos.data ASC, agendamentos.horario ASC
    """, (hoje,))

    agendamentos = cursor.fetchall()
    conexao.close()

    return render_template("barbeiro.html", agendamentos=agendamentos, hoje=hoje)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conexao = sqlite3.connect("database.db")
        cursor = conexao.cursor()

        cursor.execute(
            "SELECT id, nome, telefone FROM clientes WHERE email = ? AND senha = ?",
            (email, senha)
        )

        usuario = cursor.fetchone()
        conexao.close()

        if usuario:
            session["usuario_id"] = usuario[0]
            session["usuario_nome"] = usuario[1]
            session["usuario_telefone"] = usuario[2]

            return redirect("/agendamento")
        else:
            return "Email ou senha incorretos"

    return render_template("tela-de-login.html")


@app.route("/agendamento", methods=["GET", "POST"])
def agendamento():

    if "usuario_id" not in session:
        return redirect("/")

    data = request.args.get("data")
    servicos = request.args.getlist("servico")

    horarios_disponiveis = []

    if data and servicos:
        dia = datetime.strptime(data, "%Y-%m-%d").weekday()

        if dia == 6: 
            horarios_disponiveis = []
        else:
            if len(servicos) == 3:
                duracao = 45
            else:
                duracao = 30

            todos = gerar_horarios(data, duracao)

            conexao = sqlite3.connect("database.db")
            cursor = conexao.cursor()

            cursor.execute("""
                SELECT horario, servicos
                FROM agendamentos
                WHERE data = ?
            """, (data,))

            ocupados = cursor.fetchall()
            conexao.close()

            livres = []

            for h in todos:
                h_min = int(h.split(":")[0]) * 60 + int(h.split(":")[1])
                h_fim = h_min + duracao
                conflito = False

                for h2, s2 in ocupados:
                    qtd = len(s2.split(","))
                    dur2 = 45 if qtd == 3 else 30

                    ini2 = int(h2.split(":")[0]) * 60 + int(h2.split(":")[1])
                    fim2 = ini2 + dur2

                    if h_min < fim2 and h_fim > ini2:
                        conflito = True
                        break

                if not conflito:
                    livres.append(h)

            horarios_disponiveis = livres

    if request.method == "POST":
        servicos = request.form.getlist("servico")
        data = request.form.get("data")
        horario = request.form.get("horario")

        if not servicos or not data or not horario:
            return "Preencha tudo"

        servicos_texto = ", ".join(servicos)

        conexao = sqlite3.connect("database.db")
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO agendamentos (cliente_id, servicos, data, horario)
            VALUES (?, ?, ?, ?)
        """, (session["usuario_id"], servicos_texto, data, horario))

        conexao.commit()
        conexao.close()

        return redirect("/sucesso")

    return render_template(
        "agendamento.html",
        nome=session["usuario_nome"],
        telefone=session["usuario_telefone"],
        horarios=horarios_disponiveis,
        data_selecionada=data,
        servicos_selecionados=servicos
    )

    if data:
        dia = datetime.strptime(data, "%Y-%m-%d").weekday()
        if dia != 6: 

            cursor.execute("""
                SELECT horario, servicos
                FROM agendamentos
                WHERE data = ?
            """, (data,))
            agendados = cursor.fetchall()

            hora = datetime.strptime("08:00", "%H:%M")
            fim_expediente = datetime.strptime("19:00", "%H:%M")

            while hora < fim_expediente:
                inicio = hora.hour * 60 + hora.minute
                fim_slot = inicio + 30

                livre = True

                for h_existente, s_existente in agendados:
                    qtd = len(s_existente.split(","))
                    dur = 45 if qtd == 3 else 30

                    h2, m2 = h_existente.split(":")
                    ini2 = int(h2) * 60 + int(m2)
                    fim2 = ini2 + dur

                    if inicio < fim2 and fim_slot > ini2:
                        livre = False

                if livre:
                    horarios.append(hora.strftime("%H:%M"))

                hora += timedelta(minutes=30)

    conexao.close()

    data_selecionada = request.args.get("data")
    servicos_selecionados = request.args.getlist("servico")

    return render_template(
        "agendamento.html",
        nome=session["usuario_nome"],
        telefone=session["usuario_telefone"],
        data_selecionada=data_selecionada,
        servicos_selecionados=servicos_selecionados,
        horarios=horarios if data_selecionada else []
    )


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]
        sexo = request.form["genero"]
        data_nascimento = request.form["data_nascimento"]
        senha = request.form["senha"]

        conexao = sqlite3.connect("database.db")
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO clientes (nome, email, telefone, sexo, data_nascimento, senha)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, email, telefone, sexo, data_nascimento, senha))

        conexao.commit()
        conexao.close()

        return redirect("/") 

    return render_template("formulario-cadastro.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
