import pandas as pd
import numpy as np
import re
import json
import os
from difflib import SequenceMatcher

OBS_FILE = "observacoes.json"
CONDO_FILE = "condominios.json"

# --- FUNÇÕES DE CARREGAMENTO E SALVAMENTO ---

def carregar_obs():
    if os.path.exists(OBS_FILE):
        try:
            with open(OBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def salvar_obs(dic_obs):
    with open(OBS_FILE, "w", encoding="utf-8") as f:
        json.dump(dic_obs, f, indent=4, ensure_ascii=False)

def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def salvar_json(dados, arquivo):
    """Salva o dicionário de dados em um arquivo JSON."""
    try:
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar JSON: {e}")

# --- FUNÇÕES DE LIMPEZA E EXTRAÇÃO ---

def limpar_duplicidade_numero(texto):
    if pd.isna(texto): return ""
    texto = str(texto).strip()
    padrao_repetido = r'\b(\d+)[\s,.]+\1\b'
    texto_limpo = re.sub(padrao_repetido, r'\1', texto)
    return texto_limpo.replace(', ,', ',').replace('  ', ' ')

def extrair_numero(texto):
    if pd.isna(texto): return ""
    texto_str = str(texto).strip()
    
    # Pega a PRIMEIRA sequência de números que aparece após um espaço
    # Ex: "Sylvio Carvalhaes 150, A34" -> Pega o 150 e para.
    match = re.search(r'\s(\d+)\b', texto_str)
    if match:
        return match.group(1)
    return ""
    
def normalizar_rua(texto):
    if pd.isna(texto): return ""
    t = str(texto).upper().strip()
    
    subs = {
        r'\bAV\b': 'AVENIDA', r'\bR\b': 'RUA', r'\bEST\b': 'ESTRADA',
        r'\bAL\b': 'ALAMEDA', r'\bPC\b': 'PRACA', r'\bPROF\b': 'PROFESSOR',
        r'\bDR\b': 'DOUTOR', r'\bJD\b': 'JARDIM', r'\.': ''
    }
    for padrao, sub in subs.items():
        t = re.sub(padrao, sub, t)
    
    # Corta o texto assim que encontrar o primeiro número
    # Isso remove o "150, A34" do nome da rua
    partes = re.split(r'\s\d+', t, maxsplit=1)
    rua_limpa = partes[0].strip().replace(',', '')
    
    return rua_limpa

def limpar_para_agrupamento(rua, numero):
    """Cria a chave radical 'RUA, NUMERO' para ignorar lixo no final."""
    if not rua or not numero: return ""
    return f"{rua}, {numero}".strip().upper()

def formatar_endereco_condo(texto):
    """Usada na interface de condomínios para padronizar entradas."""
    rua = normalizar_rua(texto)
    num = extrair_numero(texto)
    return f"{rua}, {num}" if rua and num else str(texto).upper().strip()

def extrair_complemento_puro(texto):
    if pd.isna(texto): return ""
    t = str(texto).upper().strip()
    match_palavra = re.search(r'\b(APT|APTO|AP|APARTAMENTO|BLOCO|BL|SL|SALA|FUNDOS|CASA|TORRE)\b.*', t)
    if match_palavra: return match_palavra.group(0).strip()
    return ""

def padronizar_complemento(texto):
    if not texto: return ""
    t = str(texto).upper().strip().replace('-', '')
    t = re.sub(r'\b(APARTAMENTO|APTO|APT)\b', 'AP', t)
    t = re.sub(r'\b(BLOCO)\b', 'BL', t)
    return t.replace('.', '').replace('  ', ' ')

# --- FORMATAÇÃO VISUAL ---

def formatar_sequencia_visual(lista_seq):
    numeros = []
    for s in lista_seq:
        num = "".join(filter(str.isdigit, str(s).split('.')[0]))
        if num: numeros.append(int(num))
    if not numeros: return "📦 Pacotes"
    numeros = sorted(list(set(numeros)))
    ranges = []
    if not numeros: return ""
    start, last = numeros[0], numeros[0]
    for n in numeros[1:]:
        if n == last + 1: last = n
        else:
            ranges.append(f"{start} ao {last}" if start != last else str(start))
            start = last = n
    ranges.append(f"{start} ao {last}" if start != last else str(start))
    return f"📦 Pacotes: {', '.join(ranges)}"

def aplicar_formatacao_final(row, notas_vivas):
    texto_seq = formatar_sequencia_visual(row['Sequence'])
    r_p, n_p, c_p = row['Rua_Base'], row['Num_Casa'], row['Comp_Padrao']
    nota_encontrada = ""
    for chave_s, nota_s in notas_vivas.items():
        try:
            partes_s = chave_s.split('|')
            if len(partes_s) == 3:
                r_s, n_s, c_s = partes_s
                if n_p == n_s and c_p == c_s and SequenceMatcher(None, r_p, r_s).ratio() > 0.8:
                    nota_encontrada = nota_s
                    break
        except: continue
    return f"⚠️ {nota_encontrada} | {texto_seq}" if nota_encontrada else texto_seq

# --- FUNÇÃO MESTRA ---

def processar_agrupamento(df_bruto, notas_vivas, db_condos):
    df = df_bruto.copy()
    
    # 1. Limpezas Iniciais e Extração
    df['Destination Address'] = df['Destination Address'].apply(limpar_duplicidade_numero)
    df['Num_Casa'] = df['Destination Address'].apply(extrair_numero)
    df['Rua_Base'] = df['Destination Address'].apply(normalizar_rua)
    df['Comp_Padrao'] = df['Destination Address'].apply(extrair_complemento_puro).apply(padronizar_complemento)
    
    # Chave para ignorar variações de texto no final (Ex: "Ckmercio")
    df['Chave_Rua_Num'] = df.apply(lambda r: limpar_para_agrupamento(r['Rua_Base'], r['Num_Casa']), axis=1)

    # 2. Verificar Notas
    def verificar_nota(row):
        r_p, n_p, c_p = row['Rua_Base'], row['Num_Casa'], row['Comp_Padrao']
        for chave_s in notas_vivas.keys():
            try:
                p = chave_s.split('|')
                if len(p) == 3 and n_p == p[1] and c_p == p[2] and SequenceMatcher(None, r_p, p[0]).ratio() > 0.8:
                    return True
            except: continue
        return False
    df['Tem_Minha_Nota'] = df.apply(verificar_nota, axis=1)

    # 3. Definir Destinos (Regras de Condomínio)
    def definir_destino(row):
        chave = f"{row['Rua_Base']}, {row['Num_Casa']}"
        for principal, info in db_condos.items():
            membros = info.get('membros', [])
            if chave == principal or chave in membros:
                if info.get('tipo') == "Varios Condomínios com 1 Portaria":
                    return f"📍 {principal} (PORTARIA)"
                if info.get('tipo') == "Varias portaria de 1 condominio":
                    return "REGRA_SEPARAR"
        return row['Destination Address']

    df['Destino_Agrupamento'] = df.apply(definir_destino, axis=1)

   # 4. Agrupamento (GroupID) - LÓGICA DE JUNÇÃO TOTAL
    group_ids = np.zeros(len(df))
    curr = 1
    for i in range(len(df)):
        if group_ids[i] == 0:
            group_ids[i] = curr
            for j in range(i + 1, len(df)):
                # Bloqueio por nota: Se um tem nota e o outro não, não junta.
                if df.iloc[i]['Tem_Minha_Nota'] != df.iloc[j]['Tem_Minha_Nota']:
                    continue
                
                # CHAVES DE COMPARAÇÃO
                mesma_chave = (df.iloc[i]['Chave_Rua_Num'] == df.iloc[j]['Chave_Rua_Num'] and df.iloc[i]['Chave_Rua_Num'] != "")
                mesmo_destino = (df.iloc[i]['Destino_Agrupamento'] == df.iloc[j]['Destino_Agrupamento'])
                
                # Se for o mesmo endereço ou o mesmo destino definido
                if mesma_chave or mesmo_destino:
                    # ÚNICA EXCEÇÃO: Se na Aba 3 estiver como "Varias portarias de 1 condominio"
                    # o Destino_Agrupamento será "REGRA_SEPARAR". Só aqui ele checa o apartamento.
                    if df.iloc[i]['Destino_Agrupamento'] == "REGRA_SEPARAR" or df.iloc[j]['Destino_Agrupamento'] == "REGRA_SEPARAR":
                        if df.iloc[i]['Comp_Padrao'] == df.iloc[j]['Comp_Padrao']:
                            group_ids[j] = curr
                    else:
                        # PARA TODO O RESTO: Viu que é o mesmo número? 
                        # JUNTA TUDO (Ignora se um é A34, J34, Casa ou Comércio)
                        group_ids[j] = curr
            curr += 1

    df['GroupID'] = group_ids
    return df