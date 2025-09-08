from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# Função de conexão
def conectar_bd():
    return psycopg2.connect(
        user="postgres",
        password="admin",
        host="localhost",
        database="BBC"
    )

@app.route('/sitass')
def listar_sitass():
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute('SELECT "idSitAss", nome FROM "tbSitAss" ORDER BY "idSitAss"')
    registros = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('sitass.html', registros=registros)

@app.route('/sitass/adicionar', methods=['POST'])
def adicionar_sitass():
    idSitAss = request.form['idSitAss']
    nome = request.form['nome']
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute('INSERT INTO "tbSitAss" ("idSitAss", nome) VALUES (%s, %s)', (idSitAss, nome))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('listar_sitass'))

@app.route('/sitass/deletar/<int:idSitAss>')
def deletar_sitass(idSitAss):
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute('DELETE FROM "tbSitAss" WHERE "idSitAss" = %s', (idSitAss,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('listar_sitass'))

@app.route('/sitass/editar/<int:idSitAss>', methods=['POST'])
def editar_sitass(idSitAss):
    nome = request.form['nome']
    conn = conectar_bd()
    cur = conn.cursor()
    cur.execute('UPDATE "tbSitAss" SET nome = %s WHERE "idSitAss" = %s', (nome, idSitAss))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('listar_sitass'))

if __name__ == '__main__':
    app.run(debug=True)
