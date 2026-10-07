import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import io

# ReportLab para geração de PDFs
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página
st.set_page_config(
    page_title="Miguel Araújo Produções - Gestão de Faturamento",
    page_icon="🎬",
    layout="wide"
)

# Estilização CSS Personalizada
st.markdown("""
    <style>
    .stApp {
        background-color: #1A1412;
        color: #FAF6EE;
    }
    .stExpander {
        background-color: #2A201C !important;
        border: 1px solid #C5A059 !important;
        border-radius: 8px;
    }
    input, textarea, select, div[role="combobox"] {
        color: #FAF6EE !important;
        background-color: #2A201C !important;
        -webkit-text-fill-color: #FAF6EE !important;
    }
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {
        background-color: #2A201C !important;
        border: 1px solid #C5A059 !important;
        border-radius: 6px !important;
    }
    ::placeholder {
        color: #A09080 !important;
        opacity: 0.8 !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #C5A059 0%, #9A7B3E 100%);
        color: #1A1412 !important;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00E676 0%, #00C853 100%);
        color: #1A1412 !important;
        box-shadow: 0 0 12px rgba(0, 230, 118, 0.4);
    }
    div[data-testid="stMetricValue"] {
        color: #C5A059 !important;
        font-weight: bold;
    }
    label, p, span {
        color: #FAF6EE !important;
    }
    h1, h2, h3 {
        color: #C5A059 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE GERAÇÃO DE PDF ---
def gerar_pdf_relatorio(df_dados):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor("#C5A059"),
        spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor("#1A1412"),
        spaceAfter=20
    )
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=9)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.white)

    # Cabeçalho do PDF
    story.append(Paragraph("MIGUEL ARAÚJO PRODUÇÕES", title_style))
    story.append(Paragraph("Relatório Consolidado de Faturamento Operacional & Audiovisual", subtitle_style))
    story.append(Spacer(1, 10))

    # Tabela com Dados
    colunas = ["Cliente", "Data", "Setor", "Fat. Bruto", "Lucro Real"]
    tabela_data = [[Paragraph(c, header_style) for c in colunas]]

    for idx, row in df_dados.iterrows():
        tabela_data.append([
            Paragraph(str(row["Cliente"]), normal_style),
            Paragraph(str(row["Data Evento"]), normal_style),
            Paragraph(str(row["Complexo Champions"]), normal_style),
            Paragraph(f"R$ {row['Faturamento Bruto']:,.2f}", normal_style),
            Paragraph(f"R$ {row['Lucro Real']:,.2f}", normal_style)
        ])

    pdf_table = Table(tabela_data, colWidths=[160, 70, 120, 100, 100])
    pdf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2A201C")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#C5A059")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
    ]))

    story.append(pdf_table)
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- CABEÇALHO DA APLICAÇÃO ---
col_logo, col_tit = st.columns([1.5, 3.5])

with col_logo:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
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

# --- DASHBOARD & EXPORTAÇÃO EM PDF ---
if st.session_state.faturamentos:
    df = pd.DataFrame(st.session_state.faturamentos)
    
    st.markdown("---")
    st.subheader("📊 Indicadores Financeiros Consolidados")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Faturamento Bruto Total", f"R$ {df['Faturamento Bruto'].sum():,.2f}")
    kpi2.metric("Impostos (10% NF)", f"R$ {df['10% NF'].sum():,.2f}")
    kpi3.metric("Custos Operacionais + Logística", f"R$ {df['Custos Operacionais + Logística'].sum():,.2f}")
    kpi4.metric("Lucro Real Total", f"R$ {df['Lucro Real'].sum():,.2f}")

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
    col_tb1, col_tb2 = st.columns([3, 1])
    
    with col_tb1:
        st.subheader("📋 Painel Geral de Eventos & Faturamentos")
    with col_tb2:
        pdf_file = gerar_pdf_relatorio(df)
        st.download_button(
            label="📄 Baixar Relatório em PDF",
            data=pdf_file,
            file_name=f"Relatorio_Faturamento_MAP_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.dataframe(df, use_container_width=True)
