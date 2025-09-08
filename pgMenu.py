import psycopg2
con = psycopg2.connect(host='localhost', database='Aquilino', user='postgres', password='postgre')
cur = con.cursor()
sql = 'create table cidade (id serial primary key, nome varchar(100), uf varchar(2))'
cur.execute(sql)
sql = "insert into cidade values (default,'São Paulo','SP')"
cur.execute(sql)
con.commit()
cur.execute('select * from cidade')
recset = cur.fetchall()
for rec in recset:
 print ('passou aqui')
 print (rec)
 con.close()