import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Gestão de Faturamento - Champions League Experience",
    page_icon="🏆",
    layout="wide"
)

# Estilização CSS Personalizada (Cores Institucionais)
st.markdown("""
    <style>
    .main {
        background-color: #FDFBF7;
    }
    .stButton>button {
        background-color: #3B2319;
        color: #FFFFFF;
        font-weight: bold;
        border-radius: 6px;
        border: 1px solid #C8A051;
    }
    .stButton>button:hover {
        background-color: #C8A051;
        color: #3B2319;
    }
    div[data-testid="stMetricValue"] {
        color: #3B2319;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO COM LOGÓTIPO / ARTE ---
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    # Pode substituir pelo URL da sua imagem/logo oficial
    st.image("https://img.icons8.com/color/144/trophy.png", width=110)

with col_tit:
    st.title("🏆 Champions League Experience Brasil")
    st.subheader("Painel de Gestão de Faturamento & Operações Cênicas")

st.markdown("---")

# Inicialização da base de dados na sessão
if "faturamentos" not in st.session_state:
    st.session_state.faturamentos = []

# --- FORMULÁRIO DE CADASTRO ---
with st.expander("➕ Cadastrar Novo Faturamento / Evento", expanded=True):
    
    st.markdown("### 📋 1. Dados Básicos do Evento")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cliente = st.text_input("Nome do Cliente / Empresa")
        data_evento = st.date_input("Data do Evento", datetime.now())
        horario = st.text_input("Horário (ex: 08h às 18h)")
        
    with col2:
        local = st.selectbox("Local / Espaço", ["Arena", "Sala Glass", "Rooftop Maior", "Rooftop Menor"])
        transmissao = st.radio("Transmissão Painéis & TVs do Complexo?", ["Sim", "Não"], horizontal=True)
        
    with col3:
        equipe_tecnica = st.text_area("Equipe Técnica Escalada", placeholder="Ex: VJ Miguel, Técnico Som João...")

    st.markdown("### 🛠️ 2. Equipamentos em Contrato")
    equipamentos_contrato = st.text_area(
        "Lista de Equipamentos Contratados",
        placeholder="Ex: Servidor Resolume, 04 Microfones Shure QLXD, Mesa XR16, Switcher HDMI 4x1..."
    )

    st.markdown("### 💰 3. Valores e Contratação Extra")
    col_v1, col_v2, col_v3 = st.columns(3)
    
    with col_v1:
        val_orcamento = st.number_input("Valor do Orçamento Proposto (R$)", min_value=0.0, step=100.0)
        val_aprovado = st.number_input("Valor Aprovado (R$)", min_value=0.0, step=100.0)
        
    with col_v2:
        contratacao_extra = st.number_input("Valor Contratação Extra (R$)", min_value=0.0, step=50.0)
        desc_extra = st.text_input("Descrição da Contratação Extra", placeholder="Ex: Iluminação cênica adicional, diária extra...")
        
    with col_v3:
        st.info("💡 **Resumo da Receita**\n"
                f"• Aprovado + Extra: **R$ {val_aprovado + contratacao_extra:,.2f}**\n"
                f"• Imposto NF (10%): **R$ {(val_aprovado + contratacao_extra) * 0.10:,.2f}**")

    st.markdown("### 👥 4. Custos Operacionais")
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        custo_resolume = st.number_input("Custo Resolume / PPT (R$)", min_value=0.0, step=50.0)
    with col_c2:
        custo_iluminacao = st.number_input("Custo Iluminação (R$)", min_value=0.0, step=50.0)
    with col_c3:
        custo_sonorizacao = st.number_input("Custo Sonorização (R$)", min_value=0.0, step=50.0)
    with col_c4:
        custo_diretor = st.number_input("Custo Diretor Técnico (R$)", min_value=0.0, step=50.0)

    st.markdown("### 🗓️ 5. Prazos e Observações")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dt_pag_operacional = st.date_input("Data Pagamento Operacional (Equipe)")
    with col_d2:
        dt_rec_champions = st.date_input("Data Recebimento Champions League")

    obs_gerais = st.text_area("Observações Gerais / Alinhamento Contratual", placeholder="Ex: NF emitida no dia útil subsequente; Pagamento antecipado...")

    # CÁLCULOS AUTOMÁTICOS
    faturamento_bruto = val_aprovado + contratacao_extra
    imposto_nf = faturamento_bruto * 0.10
    total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor
    lucro_real = faturamento_bruto - imposto_nf - total_custos_op

    st.markdown("---")
    if st.button("💾 Salvar Registos de Faturamento", use_container_width=True):
        novo_registro = {
            "Cliente": cliente,
            "Data Evento": data_evento.strftime("%d/%m/%Y"),
            "Horário": horario,
            "Local": local,
            "Transmissão TVs": transmissao,
            "Aprovado": val_aprovado,
            "Val. Extra": contratacao_extra,
            "Descrição Extra": desc_extra,
            "Faturamento Bruto": faturamento_bruto,
            "10% NF": imposto_nf,
            "Custos Operacionais": total_custos_op,
            "Lucro Real": lucro_real,
            "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"),
            "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
            "Equipamentos": equipamentos_contrato,
            "Equipe Técnica": equipe_tecnica,
            "Observações": obs_gerais
        }
        st.session_state.faturamentos.append(novo_registro)
        st.success("✅ Faturamento e detalhes do evento registados com sucesso!")

# --- DASHBOARD E TABELA COMPLETA ---
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
    st.subheader("📋 Painel Geral de Eventos & Faturamentos")
    st.dataframe(df, use_container_width=True)
