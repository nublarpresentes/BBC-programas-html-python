### ----------------------------------------------  parte do mobile
# BBCMOBILE/BBCM.py
import flet as ft
import requests

# === AJUSTE AQUI: IP/porta do seu Flask (BBC clássico) ===
# Exemplo: "http://192.168.0.120:5000"
SERVER_BASE = "http://192.168.0.120:5000"

# API de autenticação
API_BASE = f"{SERVER_BASE}/api/auth"

# =========================
# TELA DE LOGIN (MOBILE)
# =========================

def login_view(page: ft.Page):
    page.title = "TPP - Mobile"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.controls.clear()

    # ---------- TÍTULOS ----------
    titulo = ft.Text("TPP - Mobile", size=22, weight=ft.FontWeight.BOLD)
    subtit = ft.Text(
        "TPP - Tecnologia dos Painéis da Partilha",
        size=16,
        weight=ft.FontWeight.W_600
    )

    atencao_titulo = ft.Text("ATENÇÃO!", size=14, weight=ft.FontWeight.W_700, color="red")
    atencao_msg = ft.Text(
        "O sistema diferencia letras maiúsculas APENAS na senha; "
        "digite exatamente como foi cadastrada.",
        size=12
    )

    # ---------- CAMPOS ----------
    usuario = ft.TextField(label="Usuário", autofocus=True, width=350)
    senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=350)

    msg = ft.Text("", size=12)

    # ---------- BOTÃO LOGIN ----------
    def entrar(e):
        msg.value = ""
        page.update()
        try:
            r = requests.post(
                f"{API_BASE}/login",
                json={
                    "usuario": (usuario.value or "").strip(),
                    "senha": (senha.value or "").strip()
                },
                timeout=10
            )

            js = r.json()
            if r.status_code == 200 and js.get("ok"):
                # guarda dados do usuário
                page.client_storage.set("usuario", js.get("usuario"))
                page.client_storage.set("nome", js.get("nome"))

                # Vai direto para o menu mobile (sem rotas)
                page.controls.clear()
                menu_view(page)
                page.update()
            else:
                msg.value = js.get("message", f"Falha no login ({r.status_code})")
                page.update()



        except Exception as ex:
            msg.value = f"Erro ao conectar: {ex}"
            page.update()

    btn_entrar = ft.ElevatedButton("ENTRAR", width=200, on_click=entrar)

    # ---------- LINKS RODAPÉ ----------
    def ir_classico(e):
        # Abra o modo clássico no navegador do celular
        page.launch_url(f"{SERVER_BASE}/menu")

    def ir_mobile(e):
        page.snack_bar = ft.SnackBar(ft.Text("Você já está no Modo Mobile."))
        page.snack_bar.open = True
        page.update()

    links = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.TextButton("modo Clássico", on_click=ir_classico),
            ft.Text("|"),
            ft.TextButton("modo Mobile", on_click=ir_mobile),
        ],
    )

    # ---------- LAYOUT ----------
    conteudo = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            titulo,
            subtit,
            ft.Container(height=10),
            atencao_titulo,
            atencao_msg,
            ft.Container(height=10),
            usuario,
            senha,
            ft.Container(height=10),
            btn_entrar,
            ft.Container(height=10),
            links,
            ft.Container(height=10),
            msg,
        ],
    )

    page.add(
        ft.Container(
            content=conteudo,
            padding=20,
            alignment=ft.alignment.center
        )
    )


# =========================
# TELA DE MENU (MOBILE)
# =========================

def menu_view(page: ft.Page):
    page.title = "TPP - Mobile — Menu"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.controls.clear()

    nome_usuario = (
        page.client_storage.get("nome")
        or page.client_storage.get("usuario")
        or "Usuário"
    )

    titulo = ft.Text("TPP - Mobile", size=22, weight=ft.FontWeight.BOLD)
    subtit = ft.Text("Escolha uma opção abaixo:", size=14)
    usuario_txt = ft.Text(f"Bem-vindo, {nome_usuario}!", size=12, italic=True)

    # ---- handlers dos botões ----
    def abrir_assentado(e):
        page.launch_url(f"{SERVER_BASE}/conGeralAssent")

    def abrir_saldo(e):
        page.launch_url(f"{SERVER_BASE}/conGeralSaldo")

    def abrir_eventos(e):
        page.launch_url(f"{SERVER_BASE}/evtCon")

    def sair(e):
        page.client_storage.clear()
        page.controls.clear()
        login_view(page)
        page.update()

    btn_assentado = ft.ElevatedButton(
        text="Assentado - Consulta",
        width=260,
        on_click=abrir_assentado,
    )

    btn_saldo = ft.ElevatedButton(
        text="Saldo - Consulta",
        width=260,
        on_click=abrir_saldo,
    )

    btn_eventos = ft.ElevatedButton(
        text="Eventos",
        width=260,
        on_click=abrir_eventos,
    )

    btn_sair = ft.OutlinedButton(
        text="Sair",
        width=160,
        on_click=sair,
    )

    conteudo = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        controls=[
            titulo,
            subtit,
            usuario_txt,
            ft.Divider(),
            btn_assentado,
            btn_saldo,
            btn_eventos,
            ft.Divider(),
            btn_sair,
        ],
    )

    page.add(
        ft.Container(
            content=conteudo,
            padding=20,
            alignment=ft.alignment.center,
        )
    )


# =========================
# APP (ROTAS)
# =========================
def main(page: ft.Page):
    page.title = "TPP - Mobile"
    page.scroll = ft.ScrollMode.ADAPTIVE

    # sempre começa no login
    page.controls.clear()
    login_view(page)
    page.update()



if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.WEB_BROWSER,   # abre no navegador (PWA)
        port=8550,             # porta fixa para acessar do celular
        host="192.168.0.120"         # acessível na rede local
    )

