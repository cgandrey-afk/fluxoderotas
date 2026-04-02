import streamlit as st
from funcoes import carregar_json, salvar_json, formatar_endereco_condo, limpar_duplicidade_numero, CONDO_FILE

def mostrar_aba_condos():
    st.subheader("🏢 Configuração de Grupos de Condomínios")
    db_condo = carregar_json(CONDO_FILE)

    tipo = st.radio("Selecione o objetivo do grupo:", 
        ["Varios Condomínios com 1 Portaria", "Varias portaria de 1 condominio"],
        help="2.1: Une vários endereços em uma portaria principal.\n2.2: Mantém endereços separados por Torre/Bloco mesmo que o número seja igual.")

    if tipo == "Varios Condomínios com 1 Portaria":
        st.info("**Objetivo:** Unificar endereços diferentes que são entregues em uma única portaria.")
    else:
        st.info("**Objetivo:** Evitar que torres/blocos diferentes (A1, B2) sejam agrupados, mesmo no mesmo número.")

    with st.form("form_condo"):
        selecionados_brutos = st.multiselect("Selecione endereços da planilha:", st.session_state.enderecos_planilha)
        manuais_brutos = st.text_area("Ou digite endereços manuais (um por linha):")
        
        # --- PROCESSAMENTO DA LISTA ---
        # 1. Une multiselect + texto manual
        lista_bruta = list(set(selecionados_brutos + [x.strip() for x in manuais_brutos.split('\n') if x.strip()]))
        
        # 2. LIMPEZA TOTAL (Sequencial):
        # Primeiro: Limpa números duplicados (150, 150)
        # Segundo: O formatar_endereco_condo joga fora o que não é Rua e Número (como A34)
        lista_formatada = sorted(list(set([formatar_endereco_condo(limpar_duplicidade_numero(e)) for e in lista_bruta])))

        if lista_formatada:
            st.write("### Endereços Identificados (Limpinhos):")
            st.code(", ".join(lista_formatada)) 
            
        st.write("---")
        
        principal = None
        if tipo == "Varios Condomínios com 1 Portaria":
            principal = st.selectbox("Escolha a PORTARIA PRINCIPAL:", ["-- Selecione --"] + lista_formatada)

        if st.form_submit_button("💾 Salvar Grupo"):
            if not lista_formatada:
                st.error("Adicione pelo menos um endereço.")
            elif tipo == "Varios Condomínios com 1 Portaria" and (not principal or principal == "-- Selecione --"):
                st.error("Erro: Selecione qual endereço será a Portaria Principal.")
            else:
                # Define a chave que será usada no JSON
                chave_mestra = principal if tipo == "Varios Condomínios com 1 Portaria" else lista_formatada[0]
                
                # Monta os membros (todos menos a chave mestra)
                membros = [c for c in lista_formatada if c != chave_mestra]
                
                db_condo[chave_mestra] = {
                    "tipo": tipo,
                    "membros": membros
                }
                
                salvar_json(db_condo, CONDO_FILE)
                st.success(f"Grupo '{chave_mestra}' salvo com sucesso!")
                st.rerun()

    # --- LISTAGEM PARA EXCLUSÃO ---
    st.write("### Grupos Cadastrados")
    if not db_condo:
        st.write("Nenhum grupo cadastrado.")
    
    for p, info in list(db_condo.items()):
        with st.expander(f"📍 {p} ({info['tipo']})"):
            st.write(f"**Membros vinculados:** {', '.join(info['membros']) if info['membros'] else 'Nenhum'}")
            if st.button("🗑️ Excluir Grupo", key=f"del_{p}"):
                del db_condo[p]
                salvar_json(db_condo, CONDO_FILE)
                st.rerun()