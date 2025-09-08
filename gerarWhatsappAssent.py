import psycopg2

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
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None


def atualizar_no_whatsapp(cursor, matricula, ddd, celular):
    if celular:  # Verifica se celular não é None
        celular = celular[:10]  # Pega apenas os 10 primeiros caracteres
        if len(celular) == 9:  # Se celular tem apenas 9 caracteres
            celular = '9' + celular  # Adiciona o dígito 9 no início
        no_whatsapp = f"55{ddd}{celular.replace('-', '')}"
        cursor.execute('UPDATE tbassentado SET "noWhatsapp" = %s WHERE "matricula" = %s', (no_whatsapp, matricula))


conn = conectar_bd()
if conn:
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT "matricula", COALESCE("ddd", 0), "celular" FROM tbassentado')
        alunos = cursor.fetchall()
        for matricula, ddd, celular in alunos:
            if celular and (not ddd or ddd == 0):  # Verifica se celular não é vazio ou nulo e se DDD é nulo ou zero
                ddd = 91
            atualizar_no_whatsapp(cursor, matricula, ddd, celular)
        conn.commit()
        print("Atualização concluída com sucesso!")
    except psycopg2.Error as e:
        print(f"Erro ao ler ou atualizar dados: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
else:
    print("Falha na conexão com o banco de dados.")
