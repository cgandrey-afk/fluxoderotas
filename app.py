import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from funcoes import *

# 1. Configuração inicial
st.set_page_config(page_title="Gerenciador de Rotas", layout="wide", page_icon="🚚")

if 'enderecos_planilha' not in st.session_state:
    st.session_state.enderecos_planilha = []

st.title("🚚 Gerenciador de Rotas")

tab1, tab2, tab3 = st.tabs(["📋 Processar Planilha", "📝 Gerenciar Notas", "🏢 Condomínios Agrupados"])

with tab1:
    arquivo = st.file_uploader("1. Carregar Planilha", type=['xlsx', 'csv'], key="up_v5")
    
    if arquivo:
        df_temp = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
        
        if 'Destination Address' in df_temp.columns:
            novos = sorted(df_temp['Destination Address'].unique().tolist())
            if novos != st.session_state.enderecos_planilha:
                st.session_state.enderecos_planilha = novos
                st.rerun()

            if st.button("🚀 Processar e Agrupar AGORA"):
                # 1. Carrega dados de apoio
                notas_vivas = carregar_obs()
                db_condos = carregar_json(CONDO_FILE)
                
                # 2. FUNÇÃO MESTRA: Aqui dentro já acontece a Etapa 1, 2, 3, 4 e a 5 (com GPS)
                df_processado = processar_agrupamento(df_temp, notas_vivas, db_condos)
                
                # 3. Agrupamento para exibição (usando o GroupID gerado pela função acima)
                df_f = df_processado.groupby('GroupID').agg({
                    'Sequence': lambda x: list(x),
                    'Destino_Agrupamento': 'first', 
                    'Bairro': 'first', 
                    'City': 'first',
                    'Zipcode/Postal code': 'first', 
                    'Latitude': 'first', 
                    'Longitude': 'first',
                    'Rua_Base': 'first', 
                    'Num_Casa': 'first', 
                    'Comp_Padrao': 'first'
                }).reset_index(drop=True)

                # 4. Formatação visual final (Sequência + Notas)
                df_f['Sequence'] = df_f.apply(lambda row: aplicar_formatacao_final(row, notas_vivas), axis=1)
                
                # 5. Ajuste de colunas e Adição do Ícone 📍
                df_f = df_f.rename(columns={'Destino_Agrupamento': 'Destination Address'})
                df_f['Destination Address'] = df_f['Destination Address'].apply(lambda x: f"📍 {x}" if not str(x).startswith("📍") else x)
                
                cols_final = ['Sequence', 'Destination Address', 'Bairro', 'City', 'Zipcode/Postal code', 'Latitude', 'Longitude']
                
                st.success("✅ Processamento concluído seguindo as 5 etapas (Incluindo GPS)!")
                st.dataframe(df_f[cols_final])
                
                # 6. Preparação do Download
                data_str = datetime.now().strftime("%d-%m-%Y")
                nome_base = arquivo.name.split('.')[0]
                nome_final = f"Entregas {data_str} {nome_base}.csv"
                
                csv = df_f[cols_final].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Baixar Planilha", csv, nome_final, "text/csv")

with tab2:
    import interface_notas
    interface_notas.mostrar_aba_notas()

with tab3:
    import interface_condos
    interface_condos.mostrar_aba_condos()