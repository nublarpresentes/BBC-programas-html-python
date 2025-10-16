
import psycopg2
import qrcode
from PIL import Image


def conectar_bd():
    try:
        conn = psycopg2.connect(
            dbname="BBC",
            user="postgres",
            password="admin",
            host="localhost"
        )
        print("Conexão com o banco de dados estabelecida com sucesso!")
        return conn
    except psycopg2.Error as e:
        session['mensagem'] = " Erro ao tentar conectar Banco de Dados: !"
        print("Erro ao conectar ao banco de dados:", e)
        return None

def buscar_matricula_assentado():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT 'idAssent' FROM tbassentado ORDER BY nome")
            idAssents = cur.fetchall()
            conn.close()
            return idAssents
        except Exception as e:
            print("Erro ao buscar matrículas dos asentados:", e)
            return None
    else:
        return None

def gerar_qrcode(idAssent):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(idAssent)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"QR{idAssent}.jpg")

def main():
    idAssents = buscar_matricula_assentado()
    if idAssents:
        for idAssent in idAssents:
            idAssent_str = str(idAssent[0])
            gerar_qrcode(idAssent_str)
    else:
        print("Não foi possível buscar as matrículas dos assentados.")


if __name__ == "__main__":
    main()

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=5000, debug=True )