import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Miguel Araújo Produções - Gestão de Faturamento",
    page_icon="🎬",
    layout="wide"
)

# Estilização CSS Personalizada (Inspirada na marca Miguel Araújo Produções: Marrom, Dourado e Verde Cênico)
st.markdown("""
    <style>
    /* Fundo Marrom Escuro Elegante */
    .stApp {
        background-color: #1A1412;
        color: #FAF6EE;
    }
    
    /* Cabeçalho e Caixas de Texto / Expander */
    .stExpander {
        background-color: #2A201C !important;
        border: 1px solid #C5A059 !important;
        border-radius: 8px;
    }
    
    /* Botão Salvar em Dourado com Efeito */
    .stButton>button {
        background: linear-gradient(135deg, #C5A059 0%, #9A7B3E 100%);
        color: #1A1412;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00E676 0%, #00C853 100%);
        color: #1A1412;
        box-shadow: 0 0 12px rgba(0, 230, 118, 0.4);
    }
    
    /* Estilização das Métricas / Cards */
    div[data-testid="stMetricValue"] {
        color: #C5A059 !important;
        font-weight: bold;
    }
    
    /* Ajustes de rótulos de texto */
    label, p, span {
        color: #FAF6EE !important;
    }
    
    h1, h2, h3 {
        color: #C5A059 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABEÇALHO DA APLICAÇÃO ---
col_logo, col_tit = st.columns([1, 4])
with col_logo:
    st.markdown("""
        <div style="background-color: #2A201C; padding: 15px; border-radius: 10px; border: 2px solid #C5A059; text-align: center;">
            <h2 style="color: #C5A059; margin: 0; font-weight: 900; letter-spacing: 3px;">MGL</h2>
            <span style="color: #00E676; font-size: 11px; font-weight: bold; letter-spacing: 1px;">MIGUEL ARAÚJO<br>PRODUÇÕES</span>
        </div>
    """, unsafe_allow_html=True)

with col_tit:
    st.title("MIGUEL ARAÚJO PRODUÇÕES")
    st.subheader("Especialista em Audiovisual — Painel de Gestão e Faturamento")

st.markdown("---")

# Inicialização da base de dados na sessão
if "faturamentos" not in st.session_state:
    st.session_state.faturamentos = []

# --- FORMULÁRIO DE CADASTRO ---
with st.expander("➕ Cadastrar Novo Faturamento / Orçamento Operacional", expanded=True):
    
    st.markdown("### 📋 1. Dados Básicos do Evento")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cliente = st.text_input("Cliente / Empresa", value="CHAMPIONS LEAGUE EXPERIENCE BRASIL")
        data_evento = st.date_input("Data do Evento", datetime.now())
        horario = st.text_input("Horário (ex: 08h às 18h)")
        
    with col2:
        locais_selecionados = st.multiselect(
            "Complexo Champions League (Setores Contratados)",
            ["Arena", "Sala Glass", "Rooftop Maior", "Rooftop Menor"],
            default=["Arena"]
        )
        local_str = ", ".join(locais_selecionados) if locais_selecionados else "Não informado"
        
        transmissao = st.radio("Transmissão para Painéis e TVs?", ["Sim", "Não"], horizontal=True)
        
    with col3:
        equipe_tecnica = st.text_area(
            "Equipe Técnica Escalada",
            placeholder="Ex: 01 Técnico de Som, 01 Técnico PPT / Resolume, 01 Técnico de Iluminação"
        )

    st.markdown("### 🛠️ 2. Equipamentos em Contrato")
    equipamentos_contrato = st.text_area(
        "Lista de Equipamentos Contratados",
        placeholder="Ex: 04 Microfones Shure QLXD, 01 Rack Amplificador, 01 Mesa XR16, 01 Servidor Resolume, 02 Notebooks PPT..."
    )

    st.markdown("### 💰 3. Valores e Contratação Extra")
    col_v1, col_v2, col_v3 = st.columns(3)
    
    with col_v1:
        val_orcamento = st.number_input("Valor do Orçamento Proposto (R$)", min_value=0.0, step=100.0)
        val_aprovado = st.number_input("Valor Aprovado (R$)", min_value=0.0, step=100.0)
        
    with col_v2:
        contratacao_extra = st.number_input("Valor Contratação Extra (R$)", min_value=0.0, step=50.0)
        desc_extra = st.text_input("Descrição da Contratação Extra", placeholder="Ex: Diária estendida, iluminação cênica adicional...")
        
    with col_v3:
        fat_bruto_temp = val_aprovado + contratacao_extra
        imp_temp = fat_bruto_temp * 0.10
        st.info("💡 **Resumo Fiscal**\n"
                f"• Faturamento Bruto: **R$ {fat_bruto_temp:,.2f}**\n"
                f"• Nota Fiscal (10%): **R$ {imp_temp:,.2f}**")

    st.markdown("### 👥 4. Custos Operacionais & Logística")
    col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
    with col_c1:
        custo_resolume = st.number_input("Técnico / Resolume (R$)", min_value=0.0, step=50.0)
    with col_c2:
        custo_iluminacao = st.number_input("Técnico Iluminação (R$)", min_value=0.0, step=50.0)
    with col_c3:
        custo_sonorizacao = st.number_input("Técnico Som (R$)", min_value=0.0, step=50.0)
    with col_c4:
        custo_diretor = st.number_input("Direção Técnica (R$)", min_value=0.0, step=50.0)
    with col_c5:
        custo_logistica = st.number_input("Logística / Estac. (R$)", min_value=0.0, step=20.0)

    st.markdown("### 🗓️ 5. Prazos e Observações")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        dt_pag_operacional = st.date_input("Data Pagamento Operacional (Equipe)")
    with col_d2:
        dt_rec_champions = st.date_input("Data Recebimento Champions League")

    obs_gerais = st.text_area("Observações Gerais / Escopo", placeholder="Ex: Fornecimento de estrutura audiovisual completa e suporte de logística...")

    # CÁLCULOS AUTOMÁTICOS
    faturamento_bruto = val_aprovado + contratacao_extra
    imposto_nf = faturamento_bruto * 0.10
    total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica
    lucro_real = faturamento_bruto - imposto_nf - total_custos_op

    st.markdown("---")
    if st.button("💾 Salvar Registros de Faturamento", use_container_width=True):
        novo_registro = {
            "Cliente": cliente,
            "Data Evento": data_evento.strftime("%d/%m/%Y"),
            "Horário": horario,
            "Complexo Champions": local_str,
            "Transmissão TVs": transmissao,
            "Aprovado": val_aprovado,
            "Val. Extra": contratacao_extra,
            "Descrição Extra": desc_extra,
            "Faturamento Bruto": faturamento_bruto,
            "10% NF": imposto_nf,
            "Custos Operacionais + Logística": total_custos_op,
            "Lucro Real": lucro_real,
            "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"),
            "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
            "Equipamentos": equipamentos_contrato,
            "Equipe Técnica": equipe_tecnica,
            "Observações": obs_gerais
        }
        st.session_state.faturamentos.append(novo_registro)
        st.success("✅ Faturamento e detalhes do evento registrados com sucesso!")

# --- DASHBOARD, GRÁFICOS E TABELA COMPLETA ---
if st.session_state.faturamentos:
    df = pd.DataFrame(st.session_state.faturamentos)
    
    st.markdown("---")
    st.subheader("📊 Indicadores Financeiros Consolidados")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Faturamento Bruto Total", f"R$ {df['Faturamento Bruto'].sum():,.2f}")
    kpi2.metric("Impostos (10% NF)", f"R$ {df['10% NF'].sum():,.2f}")
    kpi3.metric("Custos Operacionais + Logística", f"R$ {df['Custos Operacionais + Logística'].sum():,.2f}")
    kpi4.metric("Lucro Real Total", f"R$ {df['Lucro Real'].sum():,.2f}")

    # --- GRÁFICOS ---
    st.markdown("### 📈 Análise Visual de Resultados")
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        tot_imp = df['10% NF'].sum()
        tot_custo = df['Custos Operacionais + Logística'].sum()
        tot_lucro = df['Lucro Real'].sum()
        
        df_pizza = pd.DataFrame({
            "Categoria": ["Impostos (10% NF)", "Custos Op. + Logística", "Lucro Real"],
            "Valor": [tot_imp, tot_custo, tot_lucro]
        })
        
        fig_pizza = px.pie(
            df_pizza, values='Valor', names='Categoria',
            title='Composição do Faturamento Bruto (R$)',
            hole=0.4,
            color_discrete_sequence=['#9A7B3E', '#2A201C', '#00E676']
        )
        fig_pizza.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#FAF6EE')
        st.plotly_chart(fig_pizza, use_container_width=True)

    with g_col2:
        fig_barras = px.bar(
            df, x='Complexo Champions', y='Lucro Real', color='Cliente',
            title='Lucro Real por Setor / Espaço',
            text_auto='.2f',
            color_discrete_sequence=['#C5A059', '#00E676', '#9A7B3E']
        )
        fig_barras.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#FAF6EE')
        st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Painel Geral de Eventos & Faturamentos")
    st.dataframe(df, use_container_width=True)
