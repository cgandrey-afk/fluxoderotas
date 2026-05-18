import streamlit as st
import os
import re

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
            margin-top: 0px;    /* Zera folga superior */
            margin-bottom: 20px; /* Reduzido para aproximar da logo no PC */
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

        /* =======================================================
           REGRAS EXCLUSIVAS PARA CELULAR (Telas de até 768px)
           ======================================================= */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 0.5rem !important; /* Encosta quase no topo da tela do celular */
            }
            .navbar-placeholder {
                margin-bottom: 10px; /* Colou o menu na logo */
                height: 42px;
            }
            .main-container {
                padding: 0px;
            }
            .version-tag {
                margin-bottom: 8px; /* Colou a versão no título */
            }
            .subtitle {
                margin-bottom: 12px; /* Colou o texto explicativo no botão */
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. FUNÇÃO LOCAL PARA BUSCAR O APK MAIS RECENTE ---
def buscar_apk_local_recente():
    arquivos = os.listdir('.')
    padrao = re.compile(r"app-release_(\d+\.\d+)\.apk")
    apks_encontrados = []
    
    for arquivo in arquivos:
        match = padrao.match(arquivo)
        if match:
            versao_str = match.group(1)
            try:
                apks_encontrados.append((float(versao_str), versao_str, arquivo))
            except ValueError:
                continue
                
    if apks_encontrados:
        apks_encontrados.sort(key=lambda x: x[0], reverse=True)
        return apks_encontrados[0]
    return None

# --- 3. INTERFACE VISUAL ---

# Renderiza a barra de menu no topo (isolada do bloco da logo)
st.markdown('<div class="navbar-placeholder"><span class="navbar-text">[ Espaço reservado para o futuro Menu ]</span></div>', unsafe_allow_html=True)

# Container principal (Logo + Download)
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Exibe a logo local com tamanho controlado para não estourar na tela
nome_logo = "LogoDoApp.png"
if os.path.exists(nome_logo):
    col1, col2, col3 = st.columns([1, 1.5, 1]) # Ajustado o centro para o logo ficar harmônico
    with col2:
        st.image(nome_logo, use_container_width=True)

st.markdown("<h1 style='text-align: center; margin-top: 15px; margin-bottom: 5px; color: white;'>Fluxo de Rotas</h1>", unsafe_allow_html=True)

# Busca o APK local
dados_apk = buscar_apk_local_recente()

if dados_apk:
    _, versao_texto, nome_arquivo = dados_apk
    
    st.markdown(f'<div style="text-align: center;"><span class="version-tag">Versão Atual: v{versao_texto}</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Otimize suas entregas e gerencie suas rotas direto do celular.</p>', unsafe_allow_html=True)
    
    # Botão de download real
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
    <div style="text-align: center; margin-top: 60px; color: #70757a; font-size: 12px;">
        Desenvolvido para otimização de rotas logísticas.<br>
        Campinas • São Paulo
    </div>
""", unsafe_allow_html=True)
