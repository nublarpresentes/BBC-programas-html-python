vendas = []
for i in range(5)
    cliente= input('digite o nome do cliente:  ')
    produto= input('digite o nome do produto:  ')
    valor= float(input('digite o valor do produto:'))
    qntd= int(input('digite a quantidade de produtos:  '))
    v = valor* qntd
    vendas.append(v)
    print('indice:',i,'cliente:', cliente,'produto:',produto,'quantidade:',qntd,'valor:',valor,'vendas:',v)

media = sum(vendas)/len(vendas)
print('a media das vendas é de', media)
