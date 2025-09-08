import psycopg2

def conectar_bd():
    try:
        conn = psycopg2.connect(
            dbname="BBC",
            user="postgres",
            password="admin",
            host="localhost",
            port=5432
        )
        print("Conexão com o banco de dados estabelecida com sucesso!")
        return conn
    except psycopg2.Error as e:
        print("** Erro ao conectar ao banco de dados:", e.pgerror)
        print("Detalhe:", e)
        return None