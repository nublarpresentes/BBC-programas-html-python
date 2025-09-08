limite = 0
while limite < 10:
    nome_produto = input("Qual produto você quer: ")
    tipo_produto = input("Qual tipo de produto você quer(A, B ou C): ")
    if tipo_produto.lower() not "a" or "b" or "c":
        continue
    qualidade_produto = input("Qual a qualidade do seu produto(top ou comum): ")
    if qualidade_produto.lower() not "top" or "comum":
        continue
    valor_produto = flo