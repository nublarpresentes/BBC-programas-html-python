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
        print("Erro ao conectar ao banco de dados:", e)
        return None

def buscar_matricula_assentado():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT matricula FROM tbassentado ORDER BY nome")
            matriculas = cur.fetchall()
            conn.close()
            return matriculas
        except Exception as e:
            print("Erro ao buscar matrículas dos alunos:", e)
            return None
    else:
        return None

def gerar_qrcode(matricula):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(matricula)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_filename = f"QR{matricula}.jpg"
    img.save(img_filename)
    return img_filename

def atualizar_qrcode_bd(matricula, img_filename):
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("UPDATE tbassentado SET qrcode = %s WHERE matricula = %s", (img_filename, matricula))
            conn.commit()
            conn.close()
            print(f"QRCode atualizado para matrícula {matricula}")
        except Exception as e:
            print("Erro ao atualizar QRCode no banco de dados:", e)
    else:
        print("Não foi possível conectar ao banco de dados para atualizar o QRCode.")

def main():
    matriculas = buscar_matricula_assentado()
    if matriculas:
        for matricula in matriculas:
            matricula_str = str(matricula[0])
            img_filename = gerar_qrcode(matricula_str)
            atualizar_qrcode_bd(matricula_str, img_filename)
    else:
        print("Não foi possível buscar as matrículas dos alunos.")

if __name__ == "__main__":
    main()
