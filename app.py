import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Faturamento - Champions League Experience", layout="wide")

st.title("🏆 Gestão de Faturamento - Champions League Experience Brasil")

# Inicialização do banco de dados na sessão
if "faturamentos" not in st.session_state:
    st.session_state.faturamentos = []

# --- FORMULÁRIO DE CADASTRO ---
with st.expander("➕ Cadastrar Novo Faturamento / Evento", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cliente = st.text_input("Nome do Cliente")
        data_evento = st.date_input("Data do Evento", datetime.now())
        horario = st.text_input("Horário (ex: 08h às 18h)")
        local = st.selectbox("Local", ["Arena", "Sala Glass", "Rooftop Maior", "Rooftop Menor"])
        transmissao = st.radio("Transmissão para Painéis e TVs?", ["Sim", "Não"])
        
    with col2:
        val_orcamento = st.number_input("Valor do Orçamento (R$)", min_value=0.0, step=100.0)
        val_aprovado = st.number_input("Valor Aprovado (R$)", min_value=0.0, step=100.0)
        contratacao_extra = st.number_input("Contratação Extra (R$)", min_value=0.0, step=50.0)
        equipe_tecnica = st.text_area("Equipe Técnica (Nomes e Funções)")
        
    with col3:
        custo_resolume = st.number_input("Custo Operacional Resolume / PPT (R$)", min_value=0.0, step=50.0)
        custo_iluminacao = st.number_input("Custo Operacional Iluminação (R$)", min_value=0.0, step=50.0)
        custo_sonorizacao = st.number_input("Custo Operacional Sonorização (R$)", min_value=0.0, step=50.0)
        custo_diretor = st.number_input("Custo Operacional Diretor Técnico (R$)", min_value=0.0, step=50.0)

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dt_pag_operacional = st.date_input("Data de Pagamento Operacional")
    with col_d2:
        dt_rec_champions = st.date_input("Data de Recebimento Champions League")

    # Cálculos Automáticos
    faturamento_bruto = val_aprovado + contratacao_extra
    imposto_nf = faturamento_bruto * 0.10
    total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor
    lucro_real = faturamento_bruto - imposto_nf - total_custos_op

    if st.button("💾 Salvar Faturamento", use_container_width=True):
        novo_registro = {
            "Cliente": cliente,
            "Data Evento": data_evento.strftime("%d/%m/%Y"),
            "Horário": horario,
            "Local": local,
            "Transmissão TVs": transmissao,
            "Valor Aprovado": val_aprovado,
            "Extra": contratacao_extra,
            "Faturamento Bruto": faturamento_bruto,
            "10% NF": imposto_nf,
            "Custos Operacionais": total_custos_op,
            "Lucro Real": lucro_real,
            "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"),
            "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
            "Equipe": equipe_tecnica
        }
        st.session_state.faturamentos.append(novo_registro)
        st.success("Faturamento registrado com sucesso!")

# --- DASHBOARD DE RESUMO & TABELA ---
if st.session_state.faturamentos:
    df = pd.DataFrame(st.session_state.faturamentos)
    
    st.markdown("---")
    st.subheader("📊 Resumo Financeiro Consolidado")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Faturamento Bruto Total", f"R$ {df['Faturamento Bruto'].sum():,.2f}")
    kpi2.metric("Impostos (10% NF)", f"R$ {df['10% NF'].sum():,.2f}")
    kpi3.metric("Custos Operacionais", f"R$ {df['Custos Operacionais'].sum():,.2f}")
    kpi4.metric("Lucro Real Total", f"R$ {df['Lucro Real'].sum():,.2f}")

    st.markdown("---")
    st.subheader("📋 Registros de Faturamento")
    st.dataframe(df, use_container_width=True)
