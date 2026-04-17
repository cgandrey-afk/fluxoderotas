import streamlit as st
import time
from datetime import datetime
# Importamos tudo que precisamos do funcoes.py
from funcoes import verificar_email_existente, criar_novo_usuario, db

def mostrar_tela_cadastro():
   
    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])

    with col2:
        st.markdown("<h2 class='titulo-cadastro'>📝 Criar Nova Conta</h2>", unsafe_allow_html=True)
        st.info("Preencha os dados para solicitar acesso ao sistema de rotas")

        with st.form("form_registro_usuario"):
            nome = st.text_input("Nome Completo", placeholder="Ex: Carlos Costa")
            email = st.text_input("E-mail", placeholder="seu@email.com")
            
            c1, c2 = st.columns(2)
            senha = c1.text_input("Senha", type="password", placeholder="********")
            senha_confirm = c2.text_input("Confirme a Senha", type="password", placeholder="********")
            
            st.markdown("---")
            submit = st.form_submit_button("SOLICITAR ACESSO", use_container_width=True)

            if submit:
                email_limpo = email.lower().strip()
                
                if not nome or not email or not senha:
                    st.error("⚠️ Preencha todos os campos obrigatórios.")
                elif senha != senha_confirm:
                    st.error("❌ As senhas não coincidem.")
                elif "@" not in email:
                    st.error("❌ Digite um e-mail válido.")
                else:
                    with st.spinner("Consultando disponibilidade..."):
                        if verificar_email_existente(email_limpo):
                            st.warning(f"⚠️ O e-mail **{email_limpo}** já está cadastrado.")
                        else:
                            # Montamos os dados. 
                            # O 'nivel' é definido aqui ou dentro da função criar_novo_usuario
                            dados = {
                                "nome": nome,
                                "email": email_limpo,
                                "senha": senha,
                                "nivel": "usuario", # Define o padrão como usuario
                                "data_cadastro": datetime.now(),
                                "status": "pendente"
                            }
                            
                            if criar_novo_usuario(dados):
                                st.success(f"✅ Conta de {nome} criada com sucesso!")
                                st.balloons()
                                time.sleep(2)
                                st.session_state.pagina_atual = "home"
                                st.rerun()
                            else:
                                st.error("❌ Erro ao conectar com o banco de dados.")

        if st.button("⬅️ Voltar para o Início", use_container_width=True):
            st.session_state.pagina_atual = "home"
            st.rerun()