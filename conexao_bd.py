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
        return conn
    except psycopg2.Error as e:
        print("** Erro ao conectar ao banco de dados:", str(e))
#        print("** Erro ao conectar ao banco de dados:", e.pgerror)
        print("Detalhe:", e)
        return None

# if __name__ == '__main__':  /// está aqui pra ver se esta rodando service ( postgresql-x64-16)
#     conectar_bd()