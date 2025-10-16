from flask import Flask, url_for

app = Flask(__name__)

# Restante do seu código...

def obter_dados_assentQR():
    with app.app_context():
        conn = conectar_bd()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT idAssent, nome FROM tbassentado ORDER BY nome LIMIT 5")
                assentados = cur.fetchall()
                assentados_formatados = []
                for assentado in assentados:
                    idAssent, nome = assentado  # Desempacotando os dados do aluno
                    linha1 = "!_______________!________________________________!_____________________!"
                    linha2 = f" !   BBC    ! {idAssent} - {nome:<20}!"
                    linha3 = f"!_______________!________________________________!_____________________!"
                    caminho_qrcode = url_for('static', filename=f'img/QR{idAssent}.jpg')
                    assentados_formatados.extend([linha1, linha2, linha3])
                conn.close()
                return assentados_formatados
            except Exception as e:
                app.logger.error("Erro ao obter dados dos assentados: %s", e)
                return []
        else:
            return []

if __name__ == "__main__":
    app.run(debug=True)
