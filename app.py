import streamlit as st
import requests
import re

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Fluxo de Rotas - Download",
    initial_sidebar_state="collapsed", 
    layout="centered",
    page_icon="🚚"
)

# Estilização CSS personalizada para um visual moderno e limpo
st.markdown("""
    <style>
        /* Remove menus padrões do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Centralização e container principal */
        .main-container {
            text-align: center;
            padding: 30px;
            border-radius: 20px;
            background: #ffffff;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            margin-top: 20px;
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
            margin-bottom: 25px;
        }
        
        /* Ajuste fino do subtítulo */
        .subtitle {
            color: #5f6368;
            font-size: 16px;
            margin-bottom: 30px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURAÇÕES DO GITHUB ---
# Substitua pelos dados do seu repositório
USUARIO_GITHUB = "SEU_USUARIO_AQUI"
REPOSITORIO_GITHUB = "SEU_REPOSITORIO_AQUI"

# --- 2. FUNÇÃO PARA BUSCAR O APK MAIS RECENTE ---
@st.cache_data(ttl=300)  # Guarda o resultado por 5 minutos para evitar lentidão
def buscar_apk_recente(usuario, repositorio):
    url = f"https://api.github.com/repos/{usuario}/{repositorio}/contents/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            arquivos = response.json()
            
            # Padrão para encontrar: app-release_X.XX.apk
            padrao = re.compile(r"app-release_(\d+\.\d+)\.apk")
            apks_encontrados = []
            
            for arq in arquivos:
                match = padrao.match(arq['name'])
                if match:
                    # Salva uma tupla (versão transformando string em float, nome do arquivo, url_download)
                    versao_str = match.group(1)
                    apks_encontrados.append((float(versao_str), versao_str, arq['name'], arq['download_url']))
            
            if apks_encontrados:
                # Ordena pela versão mais alta
                apks_encontrados.sort(key=lambda x: x[0], reverse=True)
                return apks_encontrados[0] # Retorna o mais recente
    except Exception as e:
        pass
    return None

# --- 3. INTERFACE VISUAL ---

# Container principal em HTML para simular um card de aplicativo
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Centralizando a logo e o título usando colunas do Streamlit
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Exibe a logo vinda do seu repositório (substitua pela sua URL final se necessário)
    url_logo = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{REPOSITORIO_GITHUB}/main/LogoDoApp.png"
    st.image(url_logo, use_container_width=True)

st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>Fluxo de Rotas</h1>", unsafe_allow_html=True)

# Executa a busca do arquivo no GitHub
dados_apk = buscar_apk_recente(USUARIO_GITHUB, REPOSITORIO_GITHUB)

if dados_apk:
    _, versao_texto, nome_arquivo, url_download = dados_apk
    
    # Exibe a versão atualizada dinamicamente
    st.markdown(f'<div style="text-align: center;"><span class="version-tag">Versão Atual: v{versao_texto}</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Otimize suas entregas e gerencie seus condomínios direto do celular.</p>', unsafe_allow_html=True)
    
    # Botão de download nativo do Streamlit direcionando para o link do GitHub
    st.link_button(
        "📥 Baixar Aplicativo (APK)",
        url_download,
        type="primary",
        use_container_width=True
    )
else:
    # Caso o arquivo não seja encontrado ou ocorra erro de credenciais
    st.markdown(f'<div style="text-align: center;"><span class="version-tag" style="background-color: #ffebee; color: #c62828;">⚠️ APK não localizado</span></div>', unsafe_allow_html=True)
    st.info("Verifique se as configurações de usuário e repositório do GitHub estão corretas no código e se o arquivo segue o padrão de nome.")

st.markdown('</div>', unsafe_allow_html=True)

# --- 4. RODAPÉ INFORMATIVO ---
st.markdown("""
    <div style="text-align: center; margin-top: 40px; color: #a0a0a0; font-size: 12px;">
        Desenvolvido para otimização de rotas logísticas.<br>
        Campinas • São Paulo
    </div>
""", unsafe_allow_html=True)
