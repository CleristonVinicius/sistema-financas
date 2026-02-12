# ============================
# IMPORTS
# ============================
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_file, flash
)
import sqlite3
import hashlib 
import os 
import time 
import pandas as pd
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from itsdangerous import URLSafeSerializer
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave-secreta-top"
app.config["UPLOAD_FOLDER"] = "static/uploads"
TOKEN = URLSafeSerializer(app.secret_key)


# ============================
# BANCO
# ============================
def get_db():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn


# ============================
# FUNÇÕES
# ============================
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def formata_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formata_data(dt):
    try:
        return datetime.fromisoformat(dt).strftime("%d/%m/%Y %H:%M")
    except:
        return dt


# ============================
# VERIFICAR LIMITE
# ============================
def verificar_limite(uid):
    with get_db() as conn:
        cur = conn.cursor()

        # Pega limite
        cur.execute("SELECT limite_gastos FROM usuarios WHERE id=?", (uid,))
        limite = cur.fetchone()[0] or 0

        # Soma despesas
        cur.execute("SELECT COALESCE(SUM(valor), 0) FROM despesas WHERE usuario_id=?", (uid,))
        total = cur.fetchone()[0]

    if limite > 0 and total >= limite:
        flash("⚠️ Você ultrapassou o limite de gastos definido!", "erro")


# ============================
# LOGIN
# ============================
@app.route("/", methods=["GET", "POST"])
def login():
    erro = ""
    mostrar_reset = session.get("login_erro", False)

    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        senha = hash_senha(request.form["senha"].strip())

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM usuarios WHERE nome=? AND senha=?",
                (usuario, senha)
            )
            user = cur.fetchone()

        if user:
            session["usuario_id"] = user["id"]
            session["usuario"] = user["nome"]
            session["login_erro"] = False
            return redirect(url_for("dashboard"))
        else:
            erro = "Usuário ou senha inválidos."
            session["login_erro"] = True
            mostrar_reset = True

    return render_template("login.html", erro=erro, mostrar_reset=mostrar_reset)


# ============================
# ESQUECI SENHA
# ============================
@app.route("/esqueci_senha", methods=["POST"])
def esqueci_senha():
    usuario = request.form["usuario"].strip()

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM usuarios WHERE nome=?", (usuario,))
        user = cur.fetchone()

    if not user:
        return redirect(url_for("login"))

    uid = user["id"]
    token = TOKEN.dumps({"uid": uid, "ts": int(time.time())})
    expira = int(time.time()) + 600

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE usuarios SET reset_token=?, reset_expira=? WHERE id=?",
            (token, expira, uid)
        )
        conn.commit()

    reset_link = f"http://127.0.0.1:5000/reset/{token}"
    print("\nLINK PARA RESET:", reset_link, "\n")

    return render_template("aviso_link.html", reset_link=reset_link)


# ============================
# RESETAR SENHA
# ============================
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_senha(token):

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE reset_token=?", (token,))
        user = cur.fetchone()

    if not user:
        return "Token inválido."

    if user["reset_expira"] < int(time.time()):
        return "Token expirado."

    if request.method == "POST":
        nova = hash_senha(request.form["senha"])

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE usuarios
                SET senha=?, reset_token=NULL, reset_expira=NULL
                WHERE id=?
            """, (nova, user["id"]))
            conn.commit()

        return redirect(url_for("login"))

    return render_template("resetar.html")


# ============================
# REGISTRO
# ============================
@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""

    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        senha = hash_senha(request.form["senha"].strip())

        try:
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (nome, senha) VALUES (?, ?)",
                    (usuario, senha)
                )
                conn.commit()

            return redirect(url_for("login"))
        except:
            msg = "Usuário já existe."

    return render_template("register.html", msg=msg)


# ============================
# DASHBOARD
# ============================
@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    uid = session["usuario_id"]
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    where = ""
    params = [uid]

    if inicio and fim:
        where = " AND date(created_at) BETWEEN ? AND ? "
        params += [inicio, fim]

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
        user = cur.fetchone()

        cur.execute(
            "SELECT * FROM entradas WHERE usuario_id=? " + where + " ORDER BY created_at DESC",
            params
        )
        entradas = cur.fetchall()

        cur.execute(
            "SELECT * FROM despesas WHERE usuario_id=? " + where + " ORDER BY created_at DESC",
            params
        )
        despesas = cur.fetchall()

    total_entradas = sum(i["valor"] for i in entradas)
    total_despesas = sum(i["valor"] for i in despesas)
    saldo = total_entradas - total_despesas

    entradas_fmt = [{
        "id": e["id"],
        "origem": e["origem"],
        "valor": formata_moeda(e["valor"]),
        "valor_raw": e["valor"],
        "data": formata_data(e["created_at"])
    } for e in entradas]

    despesas_fmt = [{
        "id": d["id"],
        "descricao": d["descricao"],
        "valor": formata_moeda(d["valor"]),
        "valor_raw": d["valor"],
        "data": formata_data(d["created_at"])
    } for d in despesas]

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT date(created_at) AS dia, SUM(valor) AS total
            FROM entradas
            WHERE usuario_id=?
            GROUP BY date(created_at)
            ORDER BY dia
        """, (uid,))
        dados_e = cur.fetchall()

        cur.execute("""
            SELECT date(created_at) AS dia, SUM(valor) AS total
            FROM despesas
            WHERE usuario_id=?
            GROUP BY date(created_at)
            ORDER BY dia
        """, (uid,))
        dados_d = cur.fetchall()

    labels = sorted(list(set(
        [d["dia"] for d in dados_e] +
        [d["dia"] for d in dados_d]
    )))

    entradas_linha = [
        float(next((x["total"] for x in dados_e if x["dia"] == dia), 0))
        for dia in labels
    ]

    despesas_linha = [
        float(next((x["total"] for x in dados_d if x["dia"] == dia), 0))
        for dia in labels
    ]

    return render_template(
        "dashboard.html",
        usuario=user["nome"],
        foto_url=user["foto_url"],
        entradas=entradas_fmt,
        despesas=despesas_fmt,
        total_entradas=formata_moeda(total_entradas),
        total_despesas=formata_moeda(total_despesas),
        saldo_total=formata_moeda(saldo),
        limite=user["limite_gastos"],
        labels_linha=labels,
        entradas_linha=entradas_linha,
        despesas_linha=despesas_linha
    )


# ============================
# ADD ENTRADA
# ============================
@app.route("/add_entrada", methods=["POST"])
def add_entrada():
    uid = session["usuario_id"]
    origem = request.form["origem"]
    valor = float(request.form["valor"])

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO entradas (usuario_id, origem, valor, created_at)
            VALUES (?, ?, ?, datetime('now','localtime'))
        """, (uid, origem, valor))
        conn.commit()

    return redirect(url_for("dashboard"))


# ============================
# ADD DESPESA
# ============================
@app.route("/add_despesa", methods=["POST"])
def add_despesa():
    uid = session["usuario_id"]
    desc = request.form["descricao"]
    valor = float(request.form["valor"])

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO despesas (usuario_id, descricao, valor, created_at)
            VALUES (?, ?, ?, datetime('now','localtime'))
        """, (uid, desc, valor))
        conn.commit()

    # CHAMA VERIFICAÇÃO DO LIMITE
    verificar_limite(uid)

    return redirect(url_for("dashboard"))


# ============================
# EDITAR
# ============================
@app.route("/editar", methods=["POST"])
def editar():
    uid = session["usuario_id"]
    tipo = request.form["tipo"]
    item = request.form["id"]
    valor = float(request.form["valor"])
    descr = request.form["descricao"]
    nova_data = request.form.get("data")

    tabela = "entradas" if tipo == "entrada" else "despesas"
    campo = "origem" if tipo == "entrada" else "descricao"

    if nova_data:
        nova_data = nova_data.replace("T", " ") + ":00"

    with get_db() as conn:
        cur = conn.cursor()

        if nova_data:
            cur.execute(
                f"UPDATE {tabela} SET {campo}=?, valor=?, created_at=? WHERE id=? AND usuario_id=?",
                (descr, valor, nova_data, item, uid)
            )
        else:
            cur.execute(
                f"UPDATE {tabela} SET {campo}=?, valor=? WHERE id=? AND usuario_id=?",
                (descr, valor, item, uid)
            )

        conn.commit()

    return redirect(url_for("dashboard"))


# ============================
# DELETE
# ============================
@app.route("/delete", methods=["POST"])
def delete():
    uid = session["usuario_id"]
    item = request.form["id"]
    tipo = request.form["tipo"]

    tabela = "entradas" if tipo == "entrada" else "despesas"

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            f"DELETE FROM {tabela} WHERE id=? AND usuario_id=?",
            (item, uid)
        )
        conn.commit()

    return redirect(url_for("dashboard"))


# ============================
# PERFIL
# ============================
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    uid = session["usuario_id"]
    msg = ""

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
        user = cur.fetchone()

        if request.method == "POST":
            nome = request.form["nome"]
            email = request.form["email"]
            foto = request.files.get("foto")

            foto_url = user["foto_url"]
            if foto:
                filename = secure_filename(foto.filename)
                path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                foto.save(path)
                foto_url = f"/static/uploads/{filename}"

            cur.execute("""
                UPDATE usuarios
                SET nome=?, email=?, foto_url=?
                WHERE id=?
            """, (nome, email, foto_url, uid))
            conn.commit()

            session["usuario"] = nome
            msg = "Perfil atualizado!"

            cur.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
            user = cur.fetchone()

    return render_template("perfil.html", dados=user, msg=msg)


# ============================
# LIMITE DE GASTOS
# ============================
@app.route("/definir_limite", methods=["POST"])
def definir_limite():
    uid = session["usuario_id"]
    limite = float(request.form["limite"])

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE usuarios SET limite_gastos=? WHERE id=?",
            (limite, uid)
        )
        conn.commit()

    flash("Limite definido com sucesso!", "ok")
    return redirect(url_for("dashboard"))


# ============================
# RELATÓRIO EXCEL
# ============================
@app.route("/relatorio_excel")
def relatorio_excel():
    uid = session["usuario_id"]

    with get_db() as conn:
        cur = conn.cursor()

        cur.execute("SELECT origem, valor FROM entradas WHERE usuario_id=?", (uid,))
        ent = cur.fetchall()

        cur.execute("SELECT descricao, valor FROM despesas WHERE usuario_id=?", (uid,))
        des = cur.fetchall()

    df1 = pd.DataFrame(ent, columns=["Origem", "Valor"])
    df2 = pd.DataFrame(des, columns=["Descrição", "Valor"])

    writer = pd.ExcelWriter("relatorio.xlsx")
    df1.to_excel(writer, index=False, sheet_name="Entradas")
    df2.to_excel(writer, index=False, sheet_name="Despesas")
    writer.close()

    return send_file("relatorio.xlsx", as_attachment=True)


# ============================
# RELATÓRIO PDF
# ============================
@app.route("/relatorio_pdf")
def relatorio_pdf():
    uid = session["usuario_id"]

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT origem, valor FROM entradas WHERE usuario_id=?", (uid,))
        ent = cur.fetchall()

        cur.execute("SELECT descricao, valor FROM despesas WHERE usuario_id=?", (uid,))
        des = cur.fetchall()

    total_e = sum(i["valor"] for i in ent)
    total_d = sum(i["valor"] for i in des)
    saldo = total_e - total_d

    pdf = "relatorio.pdf"
    c = canvas.Canvas(pdf, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "Relatório Financeiro")

    y = 760
    c.setFont("Helvetica", 10)

    c.drawString(50, y, "Entradas:")
    y -= 20
    for x in ent:
        c.drawString(50, y, f"{x['origem']}: R$ {x['valor']:.2f}")
        y -= 12

    y -= 20
    c.drawString(50, y, "Despesas:")
    y -= 20
    for x in des:
        c.drawString(50, y, f"{x['descricao']}: R$ {x['valor']:.2f}")
        y -= 12

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Total Entradas: R$ {total_e:.2f}")
    y -= 20
    c.drawString(50, y, f"Total Despesas: R$ {total_d:.2f}")
    y -= 20
    c.drawString(50, y, f"Saldo Final: R$ {saldo:.2f}")

    c.save()

    return send_file(pdf, as_attachment=True)


# ============================
# LOGOUT
# ============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ============================
# RUN
# ============================
if __name__ == "__main__":
    app.run(debug=True)
