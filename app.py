import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import io

# ReportLab para geração de PDFs
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página
st.set_page_config(
    page_title="Miguel Araújo Produções - Gestão & Orçamentos",
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

# --- FUNÇÃO GERADORA DE PDF (DUAL: ORÇAMENTO CLIENTE OU CONTROLE INTERNO) ---
def gerar_pdf_evento(registro, tipo_documento="ORCAMENTO"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    story = []
    
    styles = getSampleStyleSheet()
    
    sec_title_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white,
        spaceAfter=0
    )
    
    th_style = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#2A201C"))
    td_style = ParagraphStyle('TD', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#1A1412"))
    td_bold = ParagraphStyle('TDBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#1A1412"))
    td_status = ParagraphStyle('TDStatus', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#2E7D32"), alignment=1)
    
    val_title_style = ParagraphStyle('ValTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)
    val_num_style = ParagraphStyle('ValNum', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#FFD700"), alignment=2)

    # 1. Cabeçalho com Logo
    if os.path.exists("logo.jpg"):
        story.append(RLImage("logo.jpg", width=560, height=130))
        story.append(Spacer(1, 10))
    elif os.path.exists("logo.png"):
        story.append(RLImage("logo.png", width=560, height=130))
        story.append(Spacer(1, 10))

    # --- SEÇÃO 1: RESUMO DO EVENTO ---
    titulo_sec1 = "📌 ORÇAMENTO COMERCIAL E ESCOPO TÉCNICO" if tipo_documento == "ORCAMENTO" else "📌 RELATÓRIO DE CONTROLE FINANCEIRO INTERNO"
    sec1_hdr = Table([[Paragraph(titulo_sec1, sec_title_style)]], colWidths=[560])
    sec1_hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sec1_hdr)
    
    dados_sec1 = [
        [Paragraph("CLIENTE / EMPRESA", th_style), Paragraph(str(registro["Cliente"]), td_bold), Paragraph("DATA DO EVENTO", th_style), Paragraph(str(registro["Data Evento"]), td_style)],
        [Paragraph("COMPLEXO / SETOR", th_style), Paragraph(str(registro["Complexo Champions"]), td_style), Paragraph("HORÁRIO", th_style), Paragraph(str(registro["Horário"]), td_style)],
        [Paragraph("TRANSMISSÃO TVs", th_style), Paragraph(str(registro["Transmissão TVs"]), td_style), Paragraph("OBSERVAÇÕES", th_style), Paragraph(str(registro["Observações"]), td_style)]
    ]
    t1 = Table(dados_sec1, colWidths=[110, 170, 110, 170])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF6EE")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

    # --- SEÇÃO 2: EQUIPAMENTOS E INFRAESTRUTURA TÉCNICA ---
    sec2_hdr = Table([[Paragraph("🛠️ SETOR 2: ENGENHARIA DE ÁUDIO, LUZ, VÍDEO & ESTRUTURA", sec_title_style)]], colWidths=[560])
    sec2_hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sec2_hdr)

    dados_sec2 = [
        [Paragraph("ITEM / ATIVO TÉCNICO CONTRATADO", th_style), Paragraph("STATUS OPERACIONAL", th_style)],
        [Paragraph(str(registro["Equipamentos"]).replace('\n', '<br/>'), td_style), Paragraph("INCLUSO", td_status)]
    ]
    t2 = Table(dados_sec2, colWidths=[440, 120])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # --- SEÇÃO 3: EQUIPE TÉCNICA ESCALADA ---
    sec3_hdr = Table([[Paragraph("👥 SETOR 3: DIRETORIA TÉCNICA, STAFF ESPECIALIZADO & ENSAIOS", sec_title_style)]], colWidths=[560])
    sec3_hdr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(sec3_hdr)

    dados_sec3 = [
        [Paragraph("FUNÇÃO / EQUIPE ESCALADA", th_style), Paragraph("STATUS", th_style)],
        [Paragraph(str(registro["Equipe Técnica"]).replace('\n', '<br/>'), td_style), Paragraph("ESCALADO", td_status)]
    ]
    t3 = Table(dados_sec3, colWidths=[440, 120])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t3)
    story.append(Spacer(1, 10))

    # --- SEÇÃO 4: CONTRATAÇÃO EXTRA (LINHA POR LINHA) ---
    extras_lista = registro.get("Itens Extras", [])
    if extras_lista:
        sec_extra_hdr = Table([[Paragraph("➕ SEÇÃO EXTRA: ITENS E SERVIÇOS ADICIONAIS CONTRATADOS", sec_title_style)]], colWidths=[560])
        sec_extra_hdr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(sec_extra_hdr)

        dados_extra = [[Paragraph("DESCRIÇÃO DO ITEM EXTRA", th_style), Paragraph("VALOR (R$)", th_style)]]
        for item in extras_lista:
            desc = item.get("Descrição", "")
            val = item.get("Valor", 0.0)
            if desc:
                dados_extra.append([Paragraph(desc, td_style), Paragraph(f"R$ {val:,.2f}", td_bold)])

        if len(dados_extra) > 1:
            t_extra = Table(dados_extra, colWidths=[420, 140])
            t_extra.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
                ('PADDING', (0,0), (-1,-1), 6),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t_extra)
            story.append(Spacer(1, 10))

    # --- SEÇÃO 5: FINANCEIRO COMPLETO OU RESUMO CLIENTE ---
    if tipo_documento == "FINANCEIRO":
        sec4_hdr = Table([[Paragraph("💰 BALANÇO FINANCEIRO & DIVISÃO DE LUCRO OPERACIONAL", sec_title_style)]], colWidths=[560])
        sec4_hdr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(sec4_hdr)

        lucro_total = registro["Lucro Real"]
        lucro_miguel = registro["Lucro Miguel Araújo"]
        lucro_antonio = registro["Lucro Antonio Carlos"]

        dados_sec4 = [
            [Paragraph("Faturamento Bruto:", th_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", td_bold), Paragraph("Imposto Nota Fiscal (10%):", th_style), Paragraph(f"R$ {registro['10% NF']:,.2f}", td_style)],
            [Paragraph("Custos Operacionais:", th_style), Paragraph(f"R$ {registro['Custos Operacionais + Logística']:,.2f}", td_style), Paragraph("Lucro Real Líquido:", th_style), Paragraph(f"R$ {lucro_total:,.2f}", td_bold)],
            [Paragraph("<b>PARTE MIGUEL ARAÚJO (50%)</b>", th_style), Paragraph(f"<b>R$ {lucro_miguel:,.2f}</b>", td_bold), Paragraph("<b>PARTE ANTONIO CARLOS (50%)</b>", th_style), Paragraph(f"<b>R$ {lucro_antonio:,.2f}</b>", td_bold)]
        ]
        t4 = Table(dados_sec4, colWidths=[140, 140, 140, 140])
        t4.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF6EE")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t4)
        story.append(Spacer(1, 12))

    # Banner Final de Valor Global
    val_box = Table([[
        Paragraph(f"VALOR FINANCEIRO GLOBAL (PACOTE MGL - {registro['Cliente']}):", val_title_style),
        Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", val_num_style)
    ]], colWidths=[360, 200])
    val_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(val_box)

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
    st.subheader("Especialista em Audiovisual — Gestão, Orçamentos e Sociedade")

st.markdown("---")

if "faturamentos" not in st.session_state:
    st.session_state.faturamentos = []

# NAVEGAÇÃO POR ABAS
aba1, aba2 = st.tabs(["➕ Novo Cadastro / Visão Geral", "✏️ Editar Registros Salvos"])

with aba1:
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

        st.markdown("### ➕ 3. Contratação Extra (Item por Linha)")
        st.info("💡 Digite a descrição e o valor de cada item extra. O somatório será calculado automaticamente.")
        
        df_extras_init = pd.DataFrame([{"Descrição": "Painel de LED Adicional", "Valor": 500.0}])
        df_extras_edit = st.data_editor(
            df_extras_init,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Descrição": st.column_config.TextColumn("Descrição do Item Extra", required=True),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=50.0)
            },
            key="editor_extras_novo"
        )
        
        val_extra_total = float(df_extras_edit["Valor"].sum()) if not df_extras_edit.empty else 0.0

        st.markdown("### 💰 4. Valores do Orçamento Inicial e Impostos")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            val_aprovado = st.number_input("Valor do Orçamento Aprovado Inicial (R$)", min_value=0.0, step=100.0)
        with col_v2:
            fat_bruto_temp = val_aprovado + val_extra_total
            imp_temp = fat_bruto_temp * 0.10
            st.success(f"**Faturamento Bruto Total:** R$ {fat_bruto_temp:,.2f}  \n"
                       f"• Orçamento Base: R$ {val_aprovado:,.2f} | Extras: R$ {val_extra_total:,.2f}  \n"
                       f"• Imposto Nota Fiscal (10%): R$ {imp_temp:,.2f}")

        st.markdown("### 👥 5. Custos Operacionais & Logística")
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

        st.markdown("### 🗓️ 6. Prazos e Observações")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            dt_pag_operacional = st.date_input("Data Pagamento Operacional (Equipe)")
        with col_d2:
            dt_rec_champions = st.date_input("Data Recebimento Champions League")

        obs_gerais = st.text_area("Observações Gerais / Escopo", placeholder="Ex: Fornecimento de estrutura audiovisual completa e suporte de logística...")

        # CÁLCULOS AUTOMÁTICOS COM DIVISÃO DE LUCRO
        faturamento_bruto = val_aprovado + val_extra_total
        imposto_nf = faturamento_bruto * 0.10
        total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica
        lucro_real = faturamento_bruto - imposto_nf - total_custos_op
        lucro_miguel = lucro_real * 0.50
        lucro_antonio = lucro_real * 0.50

        st.markdown("---")
        if st.button("💾 Salvar Registros de Faturamento", use_container_width=True):
            itens_extras_list = df_extras_edit.to_dict('records') if not df_extras_edit.empty else []
            novo_registro = {
                "Cliente": cliente,
                "Data Evento": data_evento.strftime("%d/%m/%Y"),
                "Horário": horario,
                "Complexo Champions": local_str,
                "Transmissão TVs": transmissao,
                "Aprovado": val_aprovado,
                "Val. Extra": val_extra_total,
                "Itens Extras": itens_extras_list,
                "Faturamento Bruto": faturamento_bruto,
                "10% NF": imposto_nf,
                "Custos Operacionais + Logística": total_custos_op,
                "Custo Resolume": custo_resolume,
                "Custo Iluminação": custo_iluminacao,
                "Custo Sonorização": custo_sonorizacao,
                "Custo Diretor": custo_diretor,
                "Custo Logística": custo_logistica,
                "Lucro Real": lucro_real,
                "Lucro Miguel Araújo": lucro_miguel,
                "Lucro Antonio Carlos": lucro_antonio,
                "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"),
                "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
                "Equipamentos": equipamentos_contrato if equipamentos_contrato else "Não especificado",
                "Equipe Técnica": equipe_tecnica if equipe_tecnica else "Não especificado",
                "Observações": obs_gerais if obs_gerais else "Nenhuma observação registrada."
            }
            st.session_state.faturamentos.append(novo_registro)
            st.success("✅ Faturamento salvo com sucesso!")

# ABA 2: EDIÇÃO DE REGISTROS EXISTENTES
with aba2:
    st.subheader("✏️ Editar Registro Preenchido")
    if not st.session_state.faturamentos:
        st.info("Nenhum evento cadastrado para edição no momento.")
    else:
        idx_edit = st.selectbox(
            "Selecione o Evento que deseja editar:",
            range(len(st.session_state.faturamentos)),
            format_func=lambda x: f"{st.session_state.faturamentos[x]['Cliente']} - {st.session_state.faturamentos[x]['Data Evento']} ({st.session_state.faturamentos[x]['Complexo Champions']})"
        )
        
        reg_edit = st.session_state.faturamentos[idx_edit]
        
        with st.form("form_edicao"):
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                e_cliente = st.text_input("Cliente / Empresa", value=reg_edit["Cliente"])
                e_horario = st.text_input("Horário", value=reg_edit["Horário"])
            with col_e2:
                e_data = st.text_input("Data do Evento", value=reg_edit["Data Evento"])
                e_transmissao = st.selectbox("Transmissão TVs", ["Sim", "Não"], index=0 if reg_edit["Transmissão TVs"]=="Sim" else 1)
            with col_e3:
                e_complexo = st.text_input("Complexo Champions", value=reg_edit["Complexo Champions"])

            st.markdown("#### 🛠️ Equipamentos e Equipe")
            e_equip = st.text_area("Equipamentos Contratados", value=reg_edit["Equipamentos"])
            e_equipe = st.text_area("Equipe Técnica", value=reg_edit["Equipe Técnica"])

            st.markdown("#### ➕ Itens Extras")
            df_extras_existente = pd.DataFrame(reg_edit.get("Itens Extras", []))
            if df_extras_existente.empty:
                df_extras_existente = pd.DataFrame([{"Descrição": "", "Valor": 0.0}])
            
            e_extras_edit = st.data_editor(
                df_extras_existente,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Descrição": st.column_config.TextColumn("Descrição do Item Extra"),
                    "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0)
                },
                key=f"editor_edit_{idx_edit}"
            )

            st.markdown("#### 💰 Valores & Custos Operacionais")
            col_ev1, col_ev2 = st.columns(2)
            with col_ev1:
                e_aprovado = st.number_input("Valor Aprovado Base (R$)", value=float(reg_edit["Aprovado"]), step=100.0)
            with col_ev2:
                e_resolume = st.number_input("Custo Resolume (R$)", value=float(reg_edit.get("Custo Resolume", 0.0)))
                e_iluminacao = st.number_input("Custo Iluminação (R$)", value=float(reg_edit.get("Custo Iluminação", 0.0)))
                e_sonorizacao = st.number_input("Custo Sonorização (R$)", value=float(reg_edit.get("Custo Sonorização", 0.0)))
                e_diretor = st.number_input("Custo Direção (R$)", value=float(reg_edit.get("Custo Diretor", 0.0)))
                e_logistica = st.number_input("Custo Logística (R$)", value=float(reg_edit.get("Custo Logística", 0.0)))

            e_obs = st.text_area("Observações Gerais", value=reg_edit["Observações"])

            btn_atualizar = st.form_submit_button("🔄 Atualizar Registro")
            
            if btn_atualizar:
                e_val_extra_total = float(e_extras_edit["Valor"].sum()) if not e_extras_edit.empty else 0.0
                e_fat_bruto = e_aprovado + e_val_extra_total
                e_imp = e_fat_bruto * 0.10
                e_custos_total = e_resolume + e_iluminacao + e_sonorizacao + e_diretor + e_logistica
                e_lucro = e_fat_bruto - e_imp - e_custos_total
                
                reg_edit_atualizado = {
                    "Cliente": e_cliente,
                    "Data Evento": e_data,
                    "Horário": e_horario,
                    "Complexo Champions": e_complexo,
                    "Transmissão TVs": e_transmissao,
                    "Aprovado": e_aprovado,
                    "Val. Extra": e_val_extra_total,
                    "Itens Extras": e_extras_edit.to_dict('records') if not e_extras_edit.empty else [],
                    "Faturamento Bruto": e_fat_bruto,
                    "10% NF": e_imp,
                    "Custos Operacionais + Logística": e_custos_total,
                    "Custo Resolume": e_resolume,
                    "Custo Iluminação": e_iluminacao,
                    "Custo Sonorização": e_sonorizacao,
                    "Custo Diretor": e_diretor,
                    "Custo Logística": e_logistica,
                    "Lucro Real": e_lucro,
                    "Lucro Miguel Araújo": e_lucro * 0.50,
                    "Lucro Antonio Carlos": e_lucro * 0.50,
                    "Pag. Operacional": reg_edit["Pag. Operacional"],
                    "Rec. Champions": reg_edit["Rec. Champions"],
                    "Equipamentos": e_equip,
                    "Equipe Técnica": e_equipe,
                    "Observações": e_obs
                }
                
                st.session_state.faturamentos[idx_edit] = reg_edit_atualizado
                st.success("✅ Registro atualizado com sucesso! Atualize a página ou verifique a dashboard.")

# --- DASHBOARD & GERADOR DE PDFS DUAIS ---
if st.session_state.faturamentos:
    df = pd.DataFrame(st.session_state.faturamentos)
    
    st.markdown("---")
    st.subheader("📊 Indicadores Financeiros & Divisão de Sociedade")
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Faturamento Bruto Total", f"R$ {df['Faturamento Bruto'].sum():,.2f}")
    kpi2.metric("Custos + NF (10%)", f"R$ {(df['10% NF'].sum() + df['Custos Operacionais + Logística'].sum()):,.2f}")
    kpi3.metric("Lucro Real Total", f"R$ {df['Lucro Real'].sum():,.2f}")
    kpi4.metric("Parte Miguel Araújo (50%)", f"R$ {df['Lucro Miguel Araújo'].sum():,.2f}")
    kpi5.metric("Parte Antonio Carlos (50%)", f"R$ {df['Lucro Antonio Carlos'].sum():,.2f}")

    st.markdown("### 📈 Análise Visual de Resultados")
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        tot_imp = df['10% NF'].sum()
        tot_custo = df['Custos Operacionais + Logística'].sum()
        tot_miguel = df['Lucro Miguel Araújo'].sum()
        tot_antonio = df['Lucro Antonio Carlos'].sum()
        
        df_pizza = pd.DataFrame({
            "Categoria": ["Impostos (10% NF)", "Custos Op. + Logística", "Lucro Miguel (50%)", "Lucro Antonio (50%)"],
            "Valor": [tot_imp, tot_custo, tot_miguel, tot_antonio]
        })
        
        fig_pizza = px.pie(
            df_pizza, values='Valor', names='Categoria',
            title='Distribuição do Faturamento Bruto (R$)',
            hole=0.4,
            color_discrete_sequence=['#9A7B3E', '#2A201C', '#00E676', '#C5A059']
        )
        fig_pizza.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#FAF6EE')
        st.plotly_chart(fig_pizza, use_container_width=True)

    with g_col2:
        fig_barras = px.bar(
            df, x='Complexo Champions', y=['Lucro Miguel Araújo', 'Lucro Antonio Carlos'],
            title='Divisão de Lucro por Setor (R$)',
            barmode='group',
            color_discrete_sequence=['#00E676', '#C5A059']
        )
        fig_barras.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#FAF6EE')
        st.plotly_chart(fig_barras, use_container_width=True)

    st.markdown("---")
    st.subheader("📄 Emissão de Documentos em PDF")
    
    col_sel, col_btn1, col_btn2 = st.columns([2, 1, 1])
    with col_sel:
        evento_idx = st.selectbox(
            "Selecione o Evento para PDF:",
            range(len(st.session_state.faturamentos)),
            format_func=lambda x: f"{st.session_state.faturamentos[x]['Cliente']} - {st.session_state.faturamentos[x]['Data Evento']} ({st.session_state.faturamentos[x]['Complexo Champions']})"
        )
    
    reg_selecionado = st.session_state.faturamentos[evento_idx]
    
    with col_btn1:
        pdf_orcamento = gerar_pdf_evento(reg_selecionado, tipo_documento="ORCAMENTO")
        st.download_button(
            label="📄 Baixar ORÇAMENTO (Cliente)",
            data=pdf_orcamento,
            file_name=f"Orcamento_{reg_selecionado['Cliente'].replace(' ', '_')}_{reg_selecionado['Data Evento'].replace('/', '-')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_btn2:
        pdf_financeiro = gerar_pdf_evento(reg_selecionado, tipo_documento="FINANCEIRO")
        st.download_button(
            label="📊 Baixar CONTROLE (Interno)",
            data=pdf_financeiro,
            file_name=f"ControleFinanceiro_{reg_selecionado['Cliente'].replace(' ', '_')}_{reg_selecionado['Data Evento'].replace('/', '-')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("---")
    st.subheader("📋 Tabela Geral de Eventos Cadastrados")
    st.dataframe(df, use_container_width=True)
