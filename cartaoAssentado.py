import psycopg2
import qrcode
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle


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

def buscar_assentados():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "matricula", "nome", "turno" FROM tbassentado ORDER BY nome LIMIT 5')
            assentados = cur.fetchall()
            conn.close()
            return assentados
        except Exception as e:
            print("Erro ao buscar assentados:", e)
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


def criar_etiqueta(assentados):
    doc = SimpleDocTemplate("etiqueta_assentados.pdf", pagesize=A4)
    story = []

    # Estilo para os textos
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.alignment = 1

    # Tamanho da etiqueta
    largura_etiqueta = 9 * cm
    altura_etiqueta = 6 * cm

    # Configuração da tabela
    data = []
    for assentado in assentados:
        matricula = assentado[0]
        nome = assentado[1]
        turno = assentado[2]
        qr_code = gerar_qrcode(matricula)
        row = [
            f'<img src="{qr_code}" width="72" height="72" />',
            f"Matr: {matricula} - {nome} - Turno: {turno}",
            "", "", "", "", "", "", "", ""
        ]
        data.append(row)

    # Adiciona as linhas de cabeçalho
    headers = ["", "", "", "", "", "", "", "", "", ""]
    data.insert(0, headers)

    # Cria a tabela
    table = Table(data, colWidths=[3 * cm, 2 * cm, 1.2 * cm] * 10, rowHeights=[3 * cm] + [0.5 * cm] * 5)
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
    ]))

    story.append(table)
    doc.build(story)


def main():
    assentados = buscar_assentados()
    if assentados:
        criar_etiqueta(assentados)
        print("Etiqueta de assentados criada com sucesso!")
    else:
        print("Não foi possível buscar os assentados.")


if __name__ == "__main__":
    main()
