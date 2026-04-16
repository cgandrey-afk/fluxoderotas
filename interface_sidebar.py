import streamlit as st
import extra_streamlit_components as stx
import time
import datetime 
from datetime import timedelta

def mostrar_sidebar():
    cookie_manager = stx.CookieManager(key="cookie_manager_andrey")

    # --- 1. INICIALIZAÇÃO DE SEGURANÇA ---
    # Se a página acabou de ser atualizada (F5), garantimos que as travas existam
    if "logout_feito" not in st.session_state:
        st.session_state.logout_feito = False

    # --- 2. TELA DE SPLASH (Só roda se NÃO houver intenção de logout) ---
    # Se o cara não está logado na memória E não acabou de clicar em sair
    if not st.session_state.get('logado') and not st.session_state.logout_feito:
        placeholder_loading = st.empty()
        
        # Mostra o carregamento enquanto tenta ler o cookie
        with placeholder_loading.container():
            st.markdown("<h3 style='text-align:center;'>🚚 Sincronizando...</h3>", unsafe_allow_html=True)

        for tentativa in range(4):
            token = cookie_manager.get(cookie="auth_fluxo")
            if token:
                from funcoes import db
                try:
                    doc = db.collection("usuarios").document(token).get()
                    if doc.exists:
                        dados = doc.to_dict()
                        st.session_state.logado = True
                        st.session_state.usuario_nome = dados.get('nome')
                        st.session_state.nivel_acesso = dados.get('nivel', 'usuario')
                        st.session_state.pagina_atual = "home"
                        placeholder_loading.empty()
                        st.rerun() # Loga e para tudo
                except:
                    pass
            time.sleep(0.5)
        
        placeholder_loading.empty()

    # --- LÓGICA DE RESET NO F5 ---
    if "carregamento_limpo" not in st.session_state:
        st.session_state.mostrar_form = False
        st.session_state.logout_feito = False
        st.session_state.carregamento_limpo = True

    with st.sidebar:
        st.title("🚚 Fluxo de Rotas")

        if st.session_state.get('logado'):
            # --- INTERFACE LOGADO ---
            nome_user = st.session_state.get('usuario_nome', 'Motorista')
            nivel = st.session_state.get('nivel_acesso', 'usuario')
            cor_status = "blue" if nivel == "admin" else "green"
            label_status = "● Administrador" if nivel == "admin" else "● Online"

            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background: #f0f2f6; border-radius: 10px; margin-bottom: 20px;">
                    <img src="https://www.w3schools.com/howto/img_avatar.png" style="width: 50px; border-radius: 50%;">
                    <div>
                        <p style="margin: 0; font-weight: bold; color: black; font-size: 15px;">{nome_user}</p>
                        <p style="margin: 0; font-size: 12px; color: {cor_status};">{label_status}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            menu = st.radio("Navegação", ["🏠 Início", "📝 Gerenciar Notas", "🏢 Condomínios"])
            st.divider()
            
            # Criamos um espaço vazio para mensagens de status da sidebar
            status_logout = st.empty()

            if st.button("Sair da Conta", use_container_width=True):
                # 1. Marca o logout na memória IMEDIATAMENTE
                st.session_state.logado = False
                st.session_state.logout_feito = True
                
                # 2. Manda deletar o cookie
                cookie_manager.delete("auth_fluxo")
                
                # 3. Dá um aviso visual rápido
                st.toast("Saindo...", icon="👋")
                
                # 4. Espera um pouco e RERUN
                time.sleep(0.8)
                st.rerun()

        elif st.session_state.get('mostrar_form'):
            # --- FORMULÁRIO DE LOGIN ---
            st.markdown("### 🔐 Entrar na Conta")
            with st.form(key="form_login_final"):
                user_email = st.text_input("E-mail").lower().strip()
                password = st.text_input("Senha", type="password")
                submit = st.form_submit_button("ENTRAR", use_container_width=True)
                
                if submit:
                    from funcoes import db, criptografar_senha
                    email_limpo = user_email.lower().strip()
                    senha_limpa = password.strip()
                    try:
                        user_ref = db.collection("usuarios").document(email_limpo)
                        doc = user_ref.get()
                        if doc.exists:
                            dados = doc.to_dict()
                            if criptografar_senha(senha_limpa) == dados.get('senha'):
                                # Grava Cookie e Sessão
                                validade = datetime.datetime.now() + datetime.timedelta(days=30)
                                cookie_manager.set("auth_fluxo", email_limpo, expires_at=validade)
                                
                                st.session_state.logado = True
                                st.session_state.usuario_nome = dados.get('nome')
                                st.session_state.nivel_acesso = dados.get('nivel', 'usuario')
                                st.session_state.mostrar_form = False
                                st.session_state.pagina_atual = "home"
                                
                                st.success("✅ Autenticado!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Senha incorreta.")
                        else:
                            st.error("Usuário não encontrado.")
                    except Exception as e:
                        st.error(f"Erro técnico: {e}")

            if st.button("⬅️ Voltar"):
                st.session_state.mostrar_form = False
                st.rerun()
            menu = "🏠 Início"

        else:
            # --- INTERFACE DESLOGADO ---
            st.info("Acesse sua conta para sincronizar dados.")
            if st.button("🔑 Fazer Login", type="primary", use_container_width=True):
                st.session_state.mostrar_form = True
                st.rerun()

            if st.button("📝 Criar Conta", use_container_width=True):
                st.session_state.pagina_atual = "cadastro"
                st.rerun()
            menu = "🏠 Início"

        st.divider()
        st.caption("Versão 5.6.0 - Campinas/SP")
        
    return menu
