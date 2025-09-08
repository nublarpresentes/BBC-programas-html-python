import psycopg2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from flask import url_for


def conectar_bd():
    try:
        conn = psycopg2.connect(
            dbname="Intranet",
            user="postgres",
            password="admin",
            host="localhost"
        )
        print("Conexão com o banco de dados estabelecida com sucesso!")
        return conn
    except psycopg2.Error as e:
        print("Erro ao conectar ao banco de dados:", e)
        return None


def buscar_alunos():
    conn = conectar_bd()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute('SELECT "matricula", "nome", "turno", "qrcode" FROM tbassentado ORDER BY nome LIMIT 5')
            alunos = cur.fetchall()
            conn.close()
            return alunos
        except Exception as e:
            print("Erro ao buscar alunos:", e)
            return None
    else:
        return None

def criar_relatorio(alunos):
    doc = SimpleDocTemplate("HTML-Back-Exemplos/cartaoLanche.pdf", pagesize=A4)
    story = []

    # Estilo para os textos
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.alignment = 1

    # Configuração da tabela
    data = []
    row_heights = []  # Altura da primeira linha (QRCode e texto)
    for aluno in alunos:
        matricula = aluno[0]
        nome = aluno[1]
        turno = aluno[2]
        qr_code_path = f"C:\\Users\\USER\\PycharmProjects\\intranet\\static\\img\\{aluno[3]}"

        row1 = [
            Image(qr_code_path, width=3*cm, height=3*cm),
            Paragraph("CONTROLE DOS LANCHES - IFPA", style_normal)
        ]
        row2 = [
            Paragraph(f"Matrícula: {matricula} - {nome} - Turno: {turno}", style_normal),
            "", "", "", "", ""
        ]
        row3 = ["2024", "SEG", "TER", "QUA", "QUI", "SEX"]
        row4 = ["Semana 1", "", "", "", "", ""]
        row5 = ["Semana 2", "", "", "", "", ""]
        row6 = ["Semana 3", "", "", "", "", ""]
        row7 = ["Semana 4", "", "", "", "", ""]
        row8 = ["Semana 5", "", "", "", "", ""]
        data.extend([row1, row2, row3, row4, row5, row6, row7, row8])
        # Adiciona 0.5 cm de altura para cada linha de dados
        row_heights.extend([3*cm, 0.5*cm] * 5)

    # Cria a tabela
    table = Table(data, colWidths=[3*cm, 6*cm], rowHeights=row_heights[:len(data)])
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
    alunos = buscar_alunos()
    if alunos:
        criar_relatorio(alunos)
        print("Relatório de alunos criado com sucesso!")
    else:
        print("Não foi possível buscar os alunos.")


if __name__ == "__main__":
    main()
