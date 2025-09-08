import math
import matplotlib.pyplot as plt
import numpy as np
import re

def menu1():
    print("\nMENU\n1. Calcular equação.\n2. Encerar programa.")

def menu2():
    print("\nMENU\n1. Mostrar gráfico da equação.\n2. Voltar para o início\n3. Encerrar programa.")

def equacao():

    equacao = input("Escreva a equação quadrática: ")
    equacao_mostrar = equacao
    equacao = equacao.replace(" ", "")
    equacao = equacao.replace("²", "^2")

    if "=" in equacao:
        equacao = equacao.split("=")[0]

    termos = re.findall(r"[+-]?\d*x\^2|[+-]?\d+[*x]|[+-]?\d+", equacao)

    a, b, c = 0, 0, 0

    for termo in termos:
        if "x^2" in termo:
            coef = termo.replace("x^2", "")
            a = int(coef) if coef not in ["", "+", "-"] else int(coef + "1")
        elif "x" in termo:
            coef = termo.replace("x", "")
            b = int(coef) if coef not in ["", "+", "-"] else int(coef + "1")
        else:
            c = int(termo)

    d = (b ** 2) - (4 * a * c)

    if d < 0:
        print("\nNão existe raíz real.")
        print("Voltando ao menu inicial.")
        input("Pressione ENTER para continuar...")
        return
    elif d == 0:
        print("\nAs raízes reais são iguais.")
        input("Pressione ENTER para continuar...")
    elif d > 0:
        print("\nAs raízes reais são diferentes.")
        input("Pressione ENTER para continuar...")

    x1 = (-b + math.sqrt(d)) / (2 * a)
    x2 = (-b - math.sqrt(d)) / (2 * a)

    yv = -d / (4*a)
    xv = -b / (2*a)

    print(f"\n==RESULTADO==\nA equação é: {equacao_mostrar}\nOs valores dos coeficientes são: a = {a}, b = {b} e c = {c}.\nO valor de delta é: {d:.2f}.\nAs raízes da equação são: {x1:.2f} e {x2:.2f}.")
    input("Pressione ENTER para continuar...")

    while True:
        menu2()
        escolha2 = input("O que você quer fazer? ")
        if escolha2 == "1":
            x = np.linspace(-5, 5, 400)
            y = a * x ** 2 + b * x + c

            plt.axhline(0, color="black", linewidth=1)
            plt.axvline(0, color="black", linewidth=1)

            plt.xlim(-abs(b) * 2 - 10, abs(b) * 2 + 10)
            plt.ylim(-abs(c) * 2 - 10, abs(c) * 2 + 10)

            plt.scatter([x1, x2], [0, 0], color="red", zorder=5, label="Raízes")
            plt.scatter([0], [c], color="orange", zorder=5, label="Coeficiente c")
            plt.scatter([xv], [yv], color="blue", zorder=5, label="Vértice")
            plt.scatter([xv], [0], color="cyan", zorder=5, label="x do vértice")
            plt.scatter([0], [yv], color="lightblue", zorder=5, label="y do vértice")

            plt.plot(x, y, label=f"{a}x² + {b}x + {c}")
            plt.title("Gráfico da equação do segundo grau")
            plt.xlabel("x")
            plt.ylabel("y")
            plt.legend()
            plt.grid(True)

            plt.show()
            input("Pressione ENTER para continuar...")
            continue
        elif escolha2 == "2":
            break
        elif escolha2 == "3":
            exit()

while True:
    menu1()
    escolha = input("O que você quer fazer?")
    if escolha == "1":
        equacao()
    elif escolha == "2":
        break