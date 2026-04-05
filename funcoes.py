import pandas as pd
import numpy as np
import re
import json
import os
from difflib import SequenceMatcher

OBS_FILE = "observacoes.json"
CONDO_FILE = "condominios.json"

# -----------------------------
# FUNÇÕES DE CARREGAMENTO
# -----------------------------
def carregar_obs():
    if os.path.exists(OBS_FILE):
        try:
            with open(OBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_obs(dic_obs):
    with open(OBS_FILE, "w", encoding="utf-8") as f:
        json.dump(dic_obs, f, indent=4, ensure_ascii=False)

def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_json(dados, arquivo):
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar JSON: {e}")

# -----------------------------
# LIMPEZA E EXTRAÇÃO
# -----------------------------
def extrair_bloco(texto):
    if pd.isna(texto): return ""
    t = str(texto).upper().replace(',', ' ')
    
    # Regex melhorado: busca BL ou BLC ou BLOCO e pega o que vem depois
    # O ?: faz com que ele ignore a palavra "BLOCO" e pegue só o valor (A, B, 1, etc)
    bl_match = re.search(r'\b(?:BLOCO|BLC|BL)\s*([A-Z0-9]+)\b', t)
    tr_match = re.search(r'\b(?:TORRE|T)\s*([A-Z0-9]+)\b', t)
    
    partes = []
    if bl_match:
        partes.append(f"BL {bl_match.group(1)}")
    if tr_match:
        partes.append(f"TORRE {tr_match.group(1)}")
        
    return " ".join(partes)

def sao_ruas_similares(rua1, rua2):
    if rua1 == rua2: return True
    return SequenceMatcher(None, str(rua1), str(rua2)).ratio() > 0.85

def limpar_duplicidade_numero(texto):
    if pd.isna(texto): return ""
    texto = str(texto).upper().strip()
    
    # Remove vírgulas e pontos para não interferir na posição do número
    texto = texto.replace(',', ' ').replace('.', ' ')
    
    # Remove espaços duplos que sobraram da remoção das vírgulas
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # Remove números repetidos (ex: 150 150)
    texto = re.sub(r'\b(\d+[A-Z]?)[\s]+\1\b', r'\1', texto)
    
    return texto

def limpar_rua_com_bairro(endereco, bairro_oficial):
    if pd.isna(endereco): return ""
    t = str(endereco).upper().strip()
    
    # Remove vírgulas e pontos logo de cara para não atrapalhar
    t = t.replace(',', ' ').replace('.', ' ')
    
    # Se o usuário escreveu o bairro no meio do endereço, nós removemos
    bairro = str(bairro_oficial).upper().strip() if pd.notna(bairro_oficial) else ""
    if bairro:
        t = t.replace(bairro, "")
        # Também tenta remover abreviações comuns de bairro
        t = t.replace("JD " + bairro.replace("JARDIM ", ""), "")
        t = t.replace("JARDIM " + bairro.replace("JD ", ""), "")

    # Remove o número e tudo o que vem depois para sobrar só o NOME da rua
    t = re.sub(r'\s\d+.*', '', t)
    
    return normalizar_rua(t)

def extrair_numero(texto):
    if pd.isna(texto): return ""
    # Primeiro limpamos o texto de vírgulas/pontos
    t = str(texto).upper().replace(',', ' ').replace('.', ' ')
    
    # Busca o primeiro conjunto de números que pode ter uma letra (ex: 150 ou 7B)
    match = re.search(r'\b(\d+[A-Z]?)\b', t)
    return match.group(1) if match else ""

def normalizar_rua(texto):
    if pd.isna(texto): return ""
    # Remove pontuação antes de começar
    t = str(texto).upper().replace(',', ' ').replace('.', ' ').strip()
    
    subs = {r'\bAV\b': 'AVENIDA', r'\bR\b': 'RUA', r'\bDR\b': 'DOUTOR', r'\bPROF\b': 'PROFESSOR'}
    for p, s in subs.items(): 
        t = re.sub(p, s, t)
        
    # Pega apenas o que vem antes do número
    partes = re.split(r'\s\d+', t, maxsplit=1)
    return partes[0].strip()

def extrair_complemento_puro(texto):
    if pd.isna(texto): return ""
    match = re.search(r'\b(APT|APTO|AP|BLOCO|BL|TORRE|CASA)\b.*', str(texto).upper())
    return match.group(0).strip() if match else ""

def padronizar_complemento(texto):
    if not texto: return ""
    t = str(texto).upper().replace('-', '').replace('.', '')
    t = re.sub(r'\b(APARTAMENTO|APTO|APT)\b', 'AP', t)
    t = re.sub(r'\b(BLOCO)\b', 'BL', t)
    return t.strip()
    
def formatar_endereco_condo(texto):
    """Garante o padrão RUA, NUMERO BL X mesmo que digitado sem vírgula"""
    if pd.isna(texto): return ""
    
    # 1. Limpeza inicial de sujeira e espaços
    t = str(texto).upper().replace(',', ' ').strip()
    t = re.sub(r'\s+', ' ', t)
    
    # 2. Extrai as partes separadamente
    rua = normalizar_rua(t)
    num = extrair_numero(t)
    bloco = extrair_bloco(t) # Pega BL A, TORRE 1, etc.
    
    if rua and num:
        # Monta o padrão RUA, NUMERO
        base = f"{rua}, {num}"
        # Se houver bloco/torre, adiciona com espaço (sem grudar)
        if bloco:
            # Remove o bloco da base se ele foi pego por engano na rua
            base = base.replace(bloco, "").strip()
            return f"{base} {bloco}".replace(" ,", ",")
        return base
    
    return t

# -----------------------------
# REGRAS DE CONDOMÍNIO (A SUA SOLICITAÇÃO)
# -----------------------------
def verificar_separacao_bloco(row, db_condos):
    rua_num = f"{row['Rua_Base']}, {row['Num_Casa']}".upper()
    for info in db_condos.values():
        if info.get('tipo') == "separado_por_bloco":
            portarias = [str(p).upper() for p in info.get('portarias', [])]
            if any(rua_num in p for p in portarias):
                return True
    return False

def normalizar_termos_condo(texto):
    """Padroniza BLOCO/BLC/BL para 'BL' e TORRE/T para 'TORRE', mantendo o que vem depois."""
    if not texto: return ""
    t = str(texto).upper().replace(',', ' ').replace('.', ' ')
    
    # Padroniza variações mantendo o identificador (ex: BLOCO B -> BL B)
    t = re.sub(r'\b(BLOCO|BLC|BL)\s*([A-Z0-9]+)\b', r'BL \2', t)
    t = re.sub(r'\b(TORRE|T)\s*([A-Z0-9]+)\b', r'TORRE \2', t)
    
    # Remove espaços duplos
    return re.sub(r'\s+', ' ', t).strip()
def formatar_endereco_agrupado(row, db_condos):
    rua_planilha = str(row['Rua_Base']).upper().strip()
    num_planilha = str(row['Num_Casa']).upper().strip()
    # Texto da Shopee normalizado (ex: Rua Ema 150 Bloco C -> RUA EMA 150 BL C)
    end_original_norm = normalizar_termos_condo(row['Destination Address'])
    
    # 1. BUSCA POR REGRA DE CADASTRO (Aba 3 - Caso 2)
    for nome_grupo, info in db_condos.items():
        if info.get('tipo') == "separado_por_bloco":
            for portaria_cadastrada in info.get('portarias', []):
                # Normaliza o que você cadastrou
                p_cad_norm = normalizar_termos_condo(portaria_cadastrada)
                
                # Se Rua e Número batem exatamente
                if rua_planilha in p_cad_norm and num_planilha in p_cad_norm:
                    # Pega o termo que diferencia (ex: "BL C")
                    termo_cadastro = p_cad_norm.replace(rua_planilha, "").replace(num_planilha, "").strip()
                    
                    # TRAVA: O termo tem que estar INTEIRO e IGUAL no endereço da Shopee
                    # Ex: Se termo_cadastro é "BL C", procuramos "BL C" no endereço normalizado
                    if termo_cadastro and f" {termo_cadastro}" in f" {end_original_norm}":
                        return portaria_cadastrada # Retorna o nome do seu cadastro

    # 2. BUSCA POR MULTI-RUAS (Aba 3 - Caso 1)
    for info in db_condos.values():
        if info.get('tipo') == "multi_ruas":
            enderecos_lista = [normalizar_termos_condo(e) for e in info.get('enderecos', [])]
            meu_end_norm = normalizar_termos_condo(f"{rua_planilha} {num_planilha}")
            if meu_end_norm in enderecos_lista:
                return str(info.get('portaria', '')).upper()

    # 4. SE NÃO ACHOU NO CADASTRO: Identifica prédio genérico
    padroes_predio = [
        r'\bAP\b', r'\bAPT\b', r'\bAPTO\b', r'\bAPARTAMENTO\b',
        r'\bBL\b', r'\bBLC\b', r'\bBLOCO\b', r'\bTORRE\b',
        r'\b[A-Z]\d{2,4}\b',   # Captura A34, J34, B102
        r'\b\d{2,4}[A-Z]\b'    # Captura 34A, 102B
    ]
    
    if any(re.search(p, end_original_norm) for p in padroes_predio):
        return f"{rua_planilha}, {num_planilha} CONDOMINIO"

    # 4. CASO GERAL (Casa/Viela/Comércio)
    return f"{rua_planilha}, {num_planilha}"
# -----------------------------
# FORMATAÇÃO DE SEQUÊNCIA
# -----------------------------
def formatar_sequencia_visual(lista_seq):
    numeros, adds = [], 0
    for s in lista_seq:
        s = str(s).strip()
        if not s or s == "-": 
            adds += 1
            continue
        # Extrai apenas os dígitos
        n = "".join(filter(str.isdigit, s))
        if n: 
            numeros.append(int(n))
        else: 
            adds += 1

    numeros = sorted(set(numeros))
    partes, i = [], 0
    while i < len(numeros):
        ini = numeros[i]
        fim = ini
        while i + 1 < len(numeros) and numeros[i + 1] == fim + 1:
            i += 1
            fim = numeros[i]
        if ini == fim: partes.append(f"{ini}")
        elif fim == ini + 1: partes.append(f"{ini} e {fim}")
        else: partes.append(f"{ini}–{fim}")
        i += 1

    total = len(numeros) + adds
    texto_numeros = ", ".join(partes)
    
    # --- CORREÇÃO DA VÍRGULA AQUI ---
    if adds > 0:
        # Se já tiver números, adiciona ", Adds: X". Se não, apenas "Adds: X"
        if texto_numeros:
            texto_final = f"{texto_numeros}, Adds: {adds}"
        else:
            texto_final = f"Adds: {adds}"
    else:
        texto_final = texto_numeros

    return f"Qtd: {total} ({texto_final})"

def aplicar_formatacao_final(row, notas_vivas):
    texto = formatar_sequencia_visual(row['Sequence'])
    for chave, nota in notas_vivas.items():
        try:
            r, n, c = chave.split('|')
            if row['Num_Casa'] == n and row['Comp_Padrao'] == c and SequenceMatcher(None, row['Rua_Base'], r).ratio() > 0.8:
                return f"{nota} | {texto}"
        except: continue
    return texto

# -----------------------------
# PROCESSAMENTO PRINCIPAL
# -----------------------------
def processar_agrupamento(df_bruto, notas_vivas, db_condos):
    df = df_bruto.copy()
    
    # 1. Preparação de colunas base
    df['Destination Address'] = df['Destination Address'].apply(limpar_duplicidade_numero)
    df['Num_Casa'] = df['Destination Address'].apply(extrair_numero)
    df['Rua_Base'] = df.apply(lambda r: limpar_rua_com_bairro(r['Destination Address'], r['Bairro']), axis=1)
    df['Comp_Padrao'] = df['Destination Address'].apply(extrair_complemento_puro).apply(padronizar_complemento)
    df['Bloco'] = df['Destination Address'].apply(extrair_bloco)

    # 2. Identificação de Condomínios e Notas
    # Aqui o sistema decide se vira "CONDOMINIO", se usa o Bloco (Aba 3) ou se mantém o original (Casa/Viela)
    df['Separar_Bloco'] = df.apply(lambda r: verificar_separacao_bloco(r, db_condos), axis=1)
    df['Endereco_Formatado'] = df.apply(lambda r: formatar_endereco_agrupado(r, db_condos), axis=1)
    
    def verificar_nota(row):
        for chave in notas_vivas.keys():
            try:
                r, n, c = chave.split('|')
                if row['Num_Casa'] == n and row['Comp_Padrao'] == c and SequenceMatcher(None, row['Rua_Base'], r).ratio() > 0.8:
                    return True
            except: continue
        return False
    df['Tem_Minha_Nota'] = df.apply(verificar_nota, axis=1)

    # 3. Lógica de Agrupamento Inteligente (IDs)
    group_ids = np.zeros(len(df))
    curr = 1
    for i in range(len(df)):
        if group_ids[i] == 0:
            group_ids[i] = curr
            for j in range(i+1, len(df)):
                if df.iloc[i]['Tem_Minha_Nota'] != df.iloc[j]['Tem_Minha_Nota']:
                    continue
                
                num_i = str(df.iloc[i]['Num_Casa'])
                num_j = str(df.iloc[j]['Num_Casa'])
                
                if num_i == num_j and num_i != "":
                    end_i = str(df.iloc[i]['Endereco_Formatado'])
                    end_j = str(df.iloc[j]['Endereco_Formatado'])
                    
                    # --- A SOLUÇÃO DEFINITIVA ---
                    
                    # REGRA 1: Se o endereço veio de um cadastro seu (Aba 3), a comparação é EXATA.
                    # (Isso impede que o Bloco B junte com o Bloco C na Rua Ema)
                    if df.iloc[i]['Separar_Bloco'] or df.iloc[j]['Separar_Bloco']:
                        if end_i == end_j:
                            group_ids[j] = curr
                            
                    # REGRA 2: Se NÃO está no seu cadastro de separação (é condomínio comum ou casa)
                    # Usamos a similaridade de 0.85 para perdoar erros de "AP" vs "APTO" ou nomes de rua.
                    else:
                        if end_i == end_j or SequenceMatcher(None, end_i, end_j).ratio() > 0.85:
                            group_ids[j] = curr
                # -----------------------------
                
            curr += 1

    df['GroupID'] = group_ids

    # 4. Agrupamento Final (O que o app.py vai receber)
    df_agrupado = df.groupby('GroupID').agg({
        'Sequence': lambda x: list(x),
        'Endereco_Formatado': 'first',
        'Bairro': 'first',
        'City': 'first',
        'Zipcode/Postal code': 'first',
        'Latitude': 'first',
        'Longitude': 'first',
        'Num_Casa': 'first',
        'Rua_Base': 'first',
        'Comp_Padrao': 'first'
    }).reset_index(drop=True)

    # 5. Formatação Final de Exibição
    df_agrupado['Sequence'] = df_agrupado.apply(lambda row: aplicar_formatacao_final(row, notas_vivas), axis=1)
    
    # Adiciona o ícone 📍 apenas na visualização final para não atrapalhar a lógica acima
    df_agrupado = df_agrupado.rename(columns={'Endereco_Formatado': 'Destination Address'})
    df_agrupado['Destination Address'] = df_agrupado['Destination Address'].apply(
        lambda x: f"📍 {x}" if not str(x).startswith("📍") else x
    )

    return df_agrupado