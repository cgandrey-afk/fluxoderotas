import streamlit as st
import os
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

# --- 2. FUNÇÃO LOCAL PARA BUSCAR O APK MAIS RECENTE ---
def buscar_apk_local_recente():
    # Lista todos os arquivos da pasta atual (onde o app.py está)
    arquivos = os.listdir('.')
    
    # Padrão para encontrar: app-release_X.XX.apk
    padrao = re.compile(r"app-release_(\d+\.\d+)\.apk")
    apks_encontrados = []
    
    for arquivo in arquivos:
        match = padrao.match(arquivo)
        if match:
            versao_str = match.group(1)
            try:
                # Transforma a versão em float para ordenar corretamente (ex: 1.10)
                apks_encontrados.append((float(versao_str), versao_str, arquivo))
            except ValueError:
                continue
                
    if apks_encontrados:
        # Ordena da maior versão para a menor
        apks_encontrados.sort(key=lambda x: x[0], reverse=True)
        return apks_encontrados[0] # Retorna (versao_float, versao_texto, nome_do_arquivo)
    
    return None

# --- 3. INTERFACE VISUAL ---

# Container principal em HTML para simular o card
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Exibe a logo local (LogoDoApp.png deve estar na mesma pasta)
nome_logo = "LogoDoApp.png"
if os.path.exists(nome_logo):
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.image(nome_logo, use_container_width=True)

st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>Fluxo de Rotas</h1>", unsafe_allow_html=True)

# Busca o APK local
dados_apk = buscar_apk_local_recente()

if dados_apk:
    _, versao_texto, nome_arquivo = dados_apk
    
    st.markdown(f'<div style="text-align: center;"><span class="version-tag">Versão Atual: v{versao_texto}</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Otimize suas entregas e gerencie suas rotas direto do celular.</p>', unsafe_allow_html=True)
    
    # Abre o arquivo em modo binário para o Streamlit servir o download real
    with open(nome_arquivo, "rb") as file:
        st.download_button(
            label="📥 Baixar Aplicativo (APK)",
            data=file,
            file_name=nome_arquivo,
            mime="application/vnd.android.package-archive",
            type="primary",
            use_container_width=True
        )
else:
    st.markdown('<div style="text-align: center;"><span class="version-tag" style="background-color: #ffebee; color: #c62828;">⚠️ Nenhum APK encontrado</span></div>', unsafe_allow_html=True)
    st.info("Garante que o arquivo APK está na mesma pasta que este script e com o nome no padrão: app-release_1.10.apk")

st.markdown('</div>', unsafe_allow_html=True)

# --- 4. RODAPÉ ---
st.markdown("""
    <div style="text-align: center; margin-top: 40px; color: #a0a0a0; font-size: 12px;">
        Desenvolvido para otimização de rotas logísticas.<br>
        Campinas • São Paulo
    </div>
""", unsafe_allow_html=True)
