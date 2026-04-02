import streamlit as st
import pandas as pd
import io

# 1. Função para normalizar os títulos compatíveis (Lógica de Deduplicação)
def normalizar_titulo(titulo):
    t = str(titulo).strip()
    # Se for qualquer um dos dois compatíveis, retorna um nome único
    trilhas_obrigatorias = [
        "ASP Brasil e Plano de Aprendizado Obrigatório no Local",
        "Brazil ASP & Onsite Mandatory Learning Plan"
    ]
    if t in trilhas_obrigatorias:
        return "ASP/Onsite Mandatory Learning (Unificado)"
    
    return t

# 2. Função de categorização
def categorizar_treinamento(titulo):
    titulo_str = str(titulo).lower()
    if any(x in titulo_str for x in ["obrigatório", "mandatory"]):
        return "Aprendizado Obrigatório"
    elif any(x in titulo_str for x in ["continuing", "continuada"]):
        return "Educação Continuada"
    return "Outros"

# Função para gerar Excel na memória
def gerar_excel(df, nome_aba):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=nome_aba)
        worksheet = writer.sheets[nome_aba]
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, 25)
    return output.getvalue()

# Configuração da Página
st.set_page_config(page_title="Dashboard de Treinamentos", layout="wide")
st.title("📊 Painel de Controle: Evolução de Treinamentos")

uploaded_file = st.file_uploader("Selecione a planilha", type=['xlsx', 'csv'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}"); st.stop()

    df.columns = [str(c).strip() for c in df.columns]
    
    mapeamento_real = {
        'E-mail': 'email',
        'Nome completo': 'tecnico',
        'REGIONAL': 'regional',
        'Título do plano de aprendizagem': 'plano_titulo',
        'Status do plano de aprendizagem': 'status_plano',
        'Porcentagem de progresso (cursos obrigatórios)': 'progresso'
    }
    
    df_clean = df.rename(columns=mapeamento_real)
    
    # Aplicação da lógica de unificação
    df_clean['Plano_Normalizado'] = df_clean['plano_titulo'].apply(normalizar_titulo)
    df_clean['Categoria'] = df_clean['Plano_Normalizado'].apply(categorizar_treinamento)
    df_clean['regional'] = df_clean['regional'].fillna('VERIFICAR').replace('NaN', 'VERIFICAR')
    df_clean['Status_Filtro'] = df_clean['progresso'].apply(lambda x: 'Concluído (100%)' if x == 100 else 'Com Pendência (<100%)')

    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("Filtros de Visão")
    lista_regionais = sorted(df_clean['regional'].unique().tolist())
    sel_regionais = st.sidebar.multiselect("Regionais", options=lista_regionais, default=lista_regionais)
    
    lista_planos = sorted(df_clean['Plano_Normalizado'].unique().tolist())
    sel_planos = st.sidebar.multiselect("Planos (Unificados)", options=lista_planos, default=lista_planos)
    
    sel_status = st.sidebar.multiselect("Status de Conclusão", options=sorted(df_clean['Status_Filtro'].unique().tolist()), default=df_clean['Status_Filtro'].unique().tolist())

    # Aplicação dos Filtros
    df_filtrado = df_clean[
        (df_clean['regional'].isin(sel_regionais)) &
        (df_clean['Plano_Normalizado'].isin(sel_planos)) &
        (df_clean['Status_Filtro'].isin(sel_status))
    ]

    # Consolidação (Deduplicação de compatíveis)
    df_consolidado = df_filtrado.groupby(['email', 'tecnico', 'regional', 'Plano_Normalizado', 'Categoria']).agg({
        'progresso': 'max',
        'status_plano': 'first'
    }).reset_index()

    # --- MÉTRICAS GERAIS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Técnicos Únicos", df_consolidado['email'].nunique())
    m2.metric("Média de Progresso", f"{df_consolidado['progresso'].mean():.1f}%" if not df_consolidado.empty else "0%")
    m3.metric("Total Concluídos", df_consolidado[df_consolidado['progresso'] == 100].shape[0])

    st.divider()
    
    # --- SEÇÃO 1: RESUMO POR REGIONAL (COM EXPORTAÇÃO) ---
    st.subheader("📍 Resumo Executivo por Regional")
    
    resumo_regional = df_consolidado.groupby('regional').agg(
        total_tecnicos=('email', 'nunique'),
        progresso_medio=('progresso', 'mean')
    ).reset_index()

    # Botão de exportação específico para o resumo regional
    st.download_button(
        label="📥 Exportar Resumo das Regionais (Excel)",
        data=gerar_excel(resumo_regional, 'Resumo_Regional'),
        file_name='resumo_regionais_unificado.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.dataframe(
        resumo_regional,
        column_config={
            "regional": "Regional",
            "total_tecnicos": "Qtd. Técnicos",
            "progresso_medio": st.column_config.ProgressColumn("Média de Conclusão", format="%.1f%%", min_value=0, max_value=100)
        },
        use_container_width=True, hide_index=True
    )

    st.divider()

    # --- SEÇÃO 2: DETALHAMENTO POR TÉCNICO (COM EXPORTAÇÃO) ---
    st.subheader("📋 Status Detalhado por Técnico")
    
    busca = st.text_input("🔍 Pesquisar por Nome ou E-mail")
    df_view = df_consolidado
    if busca:
        df_view = df_consolidado[
            (df_consolidado['tecnico'].str.contains(busca, case=False, na=False)) | 
            (df_consolidado['email'].str.contains(busca, case=False, na=False))
        ]

    # Botão de exportação para o detalhamento completo
    st.download_button(
        label="📥 Exportar Detalhamento de Técnicos (Excel)",
        data=gerar_excel(df_consolidado, 'Detalhamento'),
        file_name='detalhes_tecnicos_unificado.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.dataframe(
        df_view[['email', 'tecnico', 'regional', 'Plano_Normalizado', 'progresso']],
        column_config={
            "Plano_Normalizado": "Trilha (Unificada)",
            "progresso": st.column_config.ProgressColumn("Progresso Individual", format="%d%%", min_value=0, max_value=100),
        },
        use_container_width=True, hide_index=True
    )

else:
    st.info("Aguardando upload da planilha...")