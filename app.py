import streamlit as st
import os
import re
import requests
import tornado.web

# --- 1. CONFIGURAÇÃO DA API INTERNA (TORNADO) PARA EVITAR HIBERNAÇÃO ---
class CronHandler(tornado.web.RequestHandler):
    def get(self):
        # Ação executada quando o cron-job faz a requisição GET
        print("Cron executado com sucesso via API!")
        self.set_status(200)
        self.write({"status": "sucesso", "mensagem": "App mantido acordado"})

def iniciar_rota_cron():
    try:
        server = st.runtime.get_instance()._server
        # Cria a rota acessível em: https://fluxoderotas.streamlit.app/executar-cron
        server._tornado_app.add_handlers(r".*", [(r"/executar-cron", CronHandler)])
    except Exception:
        pass

iniciar_rota_cron()

# --- CONFIGURAÇÃO DO REPOSITÓRIO DO GITHUB ---
GITHUB_REPO = "cgandrey-afk/fluxoderotas"
RELEASE_TAG = "appdownload" # Tag que você está usando nas suas releases

# Estilização CSS personalizada para mover todo o conteúdo para o topo
st.markdown("""
    <style>
        /* Remove menus e elementos padrões do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Força todo o conteúdo do Streamlit a começar no topo absoluto da página */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* 1. BARRA DE MENU SUPERIOR */
        .navbar-placeholder {
            background-color: #ffffff;
            width: 100%;
            height: 50px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-top: 0px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .navbar-text {
            color: #888888;
            font-size: 13px;
            font-family: sans-serif;
        }
        
        /* 2. CONTAINER PRINCIPAL DO APP */
        .main-container {
            text-align: center;
            padding: 5px;
            margin-top: 0px;
        }
        
        /* Estilo do texto de versão */
        .version-tag {
            background-color: #e3f2fd;
            color: #0d47a1;
            padding: 6px 16px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: bold;
            display: inline-block;
            margin-bottom: 12px; 
        }
        
        /* Ajuste fino do subtítulo */
        .subtitle {
            color: #9aa0a6;
            font-size: 16px;
            margin-bottom: 20px;
        }

        /* Botão estilizado para redirecionar para o link do GitHub */
        .stLinkButton > a {
            background-color: #ff4b4b !important;
            color: white !important;
            border-radius: 8px;
            font-weight: bold;
            width: 100%;
            text-align: center;
        }

        /* =======================================================
            REGRAS EXCLUSIVAS PARA CELULAR (Telas de até 768px)
            ======================================================= */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 0.5rem !important;
            }
            .navbar-placeholder {
                margin-bottom: 10px;
                height: 42px;
            }
            .main-container {
                padding: 0px;
            }
            .version-tag {
                margin-bottom: 8px;
            }
            .subtitle {
                margin-bottom: 12px;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÃO PARA BUSCAR O APK NA RELEASE ESPECÍFICA DO GITHUB ---
def buscar_apk_github_recente(repo_full_name, tag):
    url = f"https://api.github.com/repos/{repo_full_name}/releases/tags/{tag}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        assets = data.get("assets", [])
        padrao = re.compile(r"app-release_(\d+\.\d+)\.apk")
        
        apks_encontrados = []
        for asset in assets:
            nome_arquivo = asset.get("name")
            download_url = asset.get("browser_download_url")
            
            match = padrao.match(nome_arquivo)
            if match:
                versao_str = match.group(1)
                try:
                    apks_encontrados.append((float(versao_str), versao_str, nome_arquivo, download_url))
                except ValueError:
                    continue
                
        if apks_encontrados:
            apks_encontrados.sort(key=lambda x: x[0], reverse=True)
            return apks_encontrados[0]
            
    except Exception:
        pass
        
    return None

# --- 3. INTERFACE VISUAL ---

st.markdown('<div class="navbar-placeholder"><span class="navbar-text">[ Espaço reservado para o futuro Menu ]</span></div>', unsafe_allow_html=True)

st.markdown('<div class="main-container">', unsafe_allow_html=True)

nome_logo = "LogoDoApp.png"
if os.path.exists(nome_logo):
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.image(nome_logo, use_container_width=True)

st.markdown("<h1 style='text-align: center; margin-top: 15px; margin-bottom: 5px; color: white;'>Fluxo de Rotas</h1>", unsafe_allow_html=True)

# Busca o APK usando o repositório e a tag correta
dados_apk = buscar_apk_github_recente(GITHUB_REPO, RELEASE_TAG)

if dados_apk:
    _, versao_texto, nome_arquivo, download_url = dados_apk
    
    st.markdown(f'<div style="text-align: center;"><span class="version-tag">Versão Atual: v{versao_texto}</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Otimize suas entregas e gerencie suas rotas direto do celular.</p>', unsafe_allow_html=True)
    
    st.link_button(
        label="📥 Baixar Aplicativo (APK)",
        url=download_url,
        type="primary"
    )
else:
    st.markdown(f"<div style=\"text-align: center;\"><span class=\"version-tag\" style=\"background-color: #ffebee; color: #c62828;\">⚠️ Nenhum APK encontrado na tag '{RELEASE_TAG}'</span></div>", unsafe_allow_html=True)
    st.info(f"Certifique-se de que há um APK no formato `app-release_1.66.apk` anexado na Release com a tag `{RELEASE_TAG}` no repositório `{GITHUB_REPO}`.")

st.markdown('</div>', unsafe_allow_html=True)

# --- 4. RODAPÉ ---
st.markdown("""
    <div style="text-align: center; margin-top: 60px; color: #70757a; font-size: 12px;">
        Desenvolvido para otimização de rotas logísticas.<br>
        Campinas • São Paulo
    </div>
""", unsafe_allow_html=True)
