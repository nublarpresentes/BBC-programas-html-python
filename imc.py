peso = float(input("Informe seu peso: "))
altura = float(input("Informe sua altura (metros): "))

imc = peso / (altura*altura)
print(f"Seus imc é: {imc}")

if imc < 18.5:
    print("Faixa: magreza")
elif imc >= 18.5 and imc < 24.9:
    print("Faixa: saudável")
elif imc >= 25 and imc < 29.9:
    print("Faixa: Sobrepeso")
elif imc >= 30 and imc < 34.9:
    print("Faixa: Obesidade I")
elif imc >= 35 and imc < 39.9:
    print("Faixa: Obesidade II")
elif imc >= 40:
    print("Faixa: Obesidade III")