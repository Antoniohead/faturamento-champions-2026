import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import io
import sqlite3
import json

# ReportLab para geração de PDFs
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- CONFIGURAÇÃO E PERSISTÊNCIA VIA SQLITE ---
DB_NAME = "eventos.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            data_evento TEXT,
            horario TEXT,
            complexo TEXT,
            transmissao TEXT,
            aprovado REAL,
            val_extra REAL,
            itens_extras TEXT,
            faturamento_bruto REAL,
            imposto_nf REAL,
            custos_total REAL,
            custo_resolume REAL,
            custo_iluminacao REAL,
            custo_sonorizacao REAL,
            custo_diretor REAL,
            custo_logistica REAL,
            lucro_real REAL,
            lucro_miguel REAL,
            lucro_antonio REAL,
            pag_operacional TEXT,
            rec_champions TEXT,
            equipamentos TEXT,
            equipe_tecnica TEXT,
            observacoes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def carregar_eventos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM eventos ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    eventos = []
    for row in rows:
        eventos.append({
            "id": row[0],
            "Cliente": row[1],
            "Data Evento": row[2],
            "Horário": row[3],
            "Complexo Champions": row[4],
            "Transmissão TVs": row[5],
            "Aprovado": row[6],
            "Val. Extra": row[7],
            "Itens Extras": json.loads(row[8]) if row[8] else [],
            "Faturamento Bruto": row[9],
            "10% NF": row[10],
            "Custos Operacionais + Logística": row[11],
            "Custo Resolume": row[12],
            "Custo Iluminação": row[13],
            "Custo Sonorização": row[14],
            "Custo Diretor": row[15],
            "Custo Logística": row[16],
            "Lucro Real": row[17],
            "Lucro Miguel Araújo": row[18],
            "Lucro Antonio Carlos": row[19],
            "Pag. Operacional": row[20],
            "Rec. Champions": row[21],
            "Equipamentos": row[22],
            "Equipe Técnica": row[23],
            "Observações": row[24]
        })
    return eventos

def salvar_evento_db(reg):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO eventos (
            cliente, data_evento, horario, complexo, transmissao, aprovado, val_extra, itens_extras,
            faturamento_bruto, imposto_nf, custos_total, custo_resolume, custo_iluminacao, custo_sonorizacao,
            custo_diretor, custo_logistica, lucro_real, lucro_miguel, lucro_antonio, pag_operacional,
            rec_champions, equipamentos, equipe_tecnica, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Complexo Champions"], reg["Transmissão TVs"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Lucro Real"],
        reg["Lucro Miguel Araújo"], reg["Lucro Antonio Carlos"], reg["Pag. Operacional"], reg["Rec. Champions"],
        reg["Equipamentos"], reg["Equipe Técnica"], reg["Observações"]
    ))
    conn.commit()
    conn.close()

def atualizar_evento_db(id_evento, reg):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE eventos SET
            cliente=?, data_evento=?, horario=?, complexo=?, transmissao=?, aprovado=?, val_extra=?,
            itens_extras=?, faturamento_bruto=?, imposto_nf=?, custos_total=?, custo_resolume=?,
            custo_iluminacao=?, custo_sonorizacao=?, custo_diretor=?, custo_logistica=?, lucro_real=?,
            lucro_miguel=?, lucro_antonio=?, pag_operacional=?, rec_champions=?, equipamentos=?,
            equipe_tecnica=?, observacoes=?
        WHERE id=?
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Complexo Champions"], reg["Transmissão TVs"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Lucro Real"],
        reg["Lucro Miguel Araújo"], reg["Lucro Antonio Carlos"], reg["Pag. Operacional"], reg["Rec. Champions"],
        reg["Equipamentos"], reg["Equipe Técnica"], reg["Observações"], id_evento
    ))
    conn.commit()
    conn.close()

def deletar_evento_db(id_evento):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM eventos WHERE id=?', (id_evento,))
    conn.commit()
    conn.close()

# Inicializa Banco de Dados
init_db()

# --- CONFIGURAÇÃO DA PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Miguel Araújo Produções - Gestão & Orçamentos",
    page_icon="🎬",
    layout="wide"
)

# Estilização CSS Personalizada
st.markdown("""
    <style>
    .stApp { background-color: #1A1412; color: #FAF6EE; }
    .stExpander { background-color: #2A201C !important; border: 1px solid #C5A059 !important; border-radius: 8px; }
    input, textarea, select, div[role="combobox"] { color: #FAF6EE !important; background-color: #2A201C !important; -webkit-text-fill-color: #FAF6EE !important; }
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] { background-color: #2A201C !important; border: 1px solid #C5A059 !important; border-radius: 6px !important; }
    ::placeholder { color: #A09080 !important; opacity: 0.8 !important; }
    .stButton>button { background: linear-gradient(135deg, #C5A059 0%, #9A7B3E 100%); color: #1A1412 !important; font-weight: bold; border-radius: 8px; border: none; padding: 0.6rem 1rem; transition: all 0.3s ease; }
    .stButton>button:hover { background: linear-gradient(135deg, #00E676 0%, #00C853 100%); color: #1A1412 !important; box-shadow: 0 0 12px rgba(0, 230, 118, 0.4); }
    div[data-testid="stMetricValue"] { color: #C5A059 !important; font-weight: bold; }
    label, p, span { color: #FAF6EE !important; }
    h1, h2, h3 { color: #C5A059 !important; }
    </style>
""", unsafe_allow_html=True)

# --- GERADOR DE PDF DUAL ---
def gerar_pdf_evento(registro, tipo_documento="ORCAMENTO"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    story = []
    styles = getSampleStyleSheet()
    
    sec_title_style = ParagraphStyle('SecTitle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, spaceAfter=0)
    th_style = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#2A201C"))
    td_style = ParagraphStyle('TD', parent=styles['Normal'], fontName='Helvetica', fontSize=8, textColor=colors.HexColor("#1A1412"))
    td_bold = ParagraphStyle('TDBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#1A1412"))
    td_status = ParagraphStyle('TDStatus', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#2E7D32"), alignment=1)
    val_title_style = ParagraphStyle('ValTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.white)
    val_num_style = ParagraphStyle('ValNum', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor("#FFD700"), alignment=2)

    if os.path.exists("logo.jpg"):
        story.append(RLImage("logo.jpg", width=560, height=130))
        story.append(Spacer(1, 10))
    elif os.path.exists("logo.png"):
        story.append(RLImage("logo.png", width=560, height=130))
        story.append(Spacer(1, 10))

    # Resumo
    titulo_sec1 = "📌 ORÇAMENTO COMERCIAL E ESCOPO TÉCNICO" if tipo_documento == "ORCAMENTO" else "📌 RELATÓRIO DE CONTROLE FINANCEIRO INTERNO"
    sec1_hdr = Table([[Paragraph(titulo_sec1, sec_title_style)]], colWidths=[560])
    sec1_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(sec1_hdr)
    
    dados_sec1 = [
        [Paragraph("CLIENTE / EMPRESA", th_style), Paragraph(str(registro["Cliente"]), td_bold), Paragraph("DATA DO EVENTO", th_style), Paragraph(str(registro["Data Evento"]), td_style)],
        [Paragraph("COMPLEXO / SETOR", th_style), Paragraph(str(registro["Complexo Champions"]), td_style), Paragraph("HORÁRIO", th_style), Paragraph(str(registro["Horário"]), td_style)],
        [Paragraph("TRANSMISSÃO TVs", th_style), Paragraph(str(registro["Transmissão TVs"]), td_style), Paragraph("OBSERVAÇÕES", th_style), Paragraph(str(registro["Observações"]), td_style)]
    ]
    t1 = Table(dados_sec1, colWidths=[110, 170, 110, 170])
    t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t1)
    story.append(Spacer(1, 10))

    # Equipamentos
    sec2_hdr = Table([[Paragraph("🛠️ SETOR 2: ENGENHARIA DE ÁUDIO, LUZ, VÍDEO & ESTRUTURA", sec_title_style)]], colWidths=[560])
    sec2_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(sec2_hdr)
    t2 = Table([[Paragraph("ITEM / ATIVO TÉCNICO CONTRATADO", th_style), Paragraph("STATUS OPERACIONAL", th_style)], [Paragraph(str(registro["Equipamentos"]).replace('\n', '<br/>'), td_style), Paragraph("INCLUSO", td_status)]], colWidths=[440, 120])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 6), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # Equipe
    sec3_hdr = Table([[Paragraph("👥 SETOR 3: DIRETORIA TÉCNICA, STAFF ESPECIALIZADO & ENSAIOS", sec_title_style)]], colWidths=[560])
    sec3_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(sec3_hdr)
    t3 = Table([[Paragraph("FUNÇÃO / EQUIPE ESCALADA", th_style), Paragraph("STATUS", th_style)], [Paragraph(str(registro["Equipe Técnica"]).replace('\n', '<br/>'), td_style), Paragraph("ESCALADO", td_status)]], colWidths=[440, 120])
    t3.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 6), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t3)
    story.append(Spacer(1, 10))

    # Extras
    extras_lista = registro.get("Itens Extras", [])
    if extras_lista:
        sec_extra_hdr = Table([[Paragraph("➕ SEÇÃO EXTRA: ITENS E SERVIÇOS ADICIONAIS CONTRATADOS", sec_title_style)]], colWidths=[560])
        sec_extra_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(sec_extra_hdr)
        dados_extra = [[Paragraph("DESCRIÇÃO DO ITEM EXTRA", th_style), Paragraph("VALOR (R$)", th_style)]]
        for item in extras_lista:
            desc = item.get("Descrição", "")
            val = item.get("Valor", 0.0)
            if desc:
                dados_extra.append([Paragraph(desc, td_style), Paragraph(f"R$ {val:,.2f}", td_bold)])
        if len(dados_extra) > 1:
            t_extra = Table(dados_extra, colWidths=[420, 140])
            t_extra.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 6), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            story.append(t_extra)
            story.append(Spacer(1, 10))

    # Financeiro (Interno)
    if tipo_documento == "FINANCEIRO":
        sec4_hdr = Table([[Paragraph("💰 BALANÇO FINANCEIRO & DIVISÃO DE LUCRO OPERACIONAL", sec_title_style)]], colWidths=[560])
        sec4_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(sec4_hdr)
        dados_sec4 = [
            [Paragraph("Faturamento Bruto:", th_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", td_bold), Paragraph("Imposto Nota Fiscal (10%):", th_style), Paragraph(f"R$ {registro['10% NF']:,.2f}", td_style)],
            [Paragraph("Custos Operacionais:", th_style), Paragraph(f"R$ {registro['Custos Operacionais + Logística']:,.2f}", td_style), Paragraph("Lucro Real Líquido:", th_style), Paragraph(f"R$ {registro['Lucro Real']:,.2f}", td_bold)],
            [Paragraph("<b>PARTE MIGUEL ARAÚJO (50%)</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Miguel Araújo']:,.2f}</b>", td_bold), Paragraph("<b>PARTE ANTONIO CARLOS (50%)</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Antonio Carlos']:,.2f}</b>", td_bold)]
        ]
        t4 = Table(dados_sec4, colWidths=[140, 140, 140, 140])
        t4.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 5)]))
        story.append(t4)
        story.append(Spacer(1, 12))

    val_box = Table([[Paragraph(f"VALOR FINANCEIRO GLOBAL (PACOTE MGL - {registro['Cliente']}):", val_title_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", val_num_style)]], colWidths=[360, 200])
    val_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 10), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(val_box)

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- CABEÇALHO ---
col_logo, col_tit = st.columns([1.5, 3.5])
with col_logo:
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown('<div style="background-color: #2A201C; padding: 15px; border-radius: 10px; border: 2px solid #C5A059; text-align: center;"><h2 style="color: #C5A059; margin: 0; font-weight: 900;">MGL</h2><span style="color: #00E676; font-size: 11px; font-weight: bold;">MIGUEL ARAÚJO<br>PRODUÇÕES</span></div>', unsafe_allow_html=True)

with col_tit:
    st.title("MIGUEL ARAÚJO PRODUÇÕES")
    st.subheader("Especialista em Audiovisual — Gestão, Orçamentos e Sociedade")

st.markdown("---")

# CARREGA EVENTOS SALVOS DO BANCO
faturamentos = carregar_eventos()

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
            locais_selecionados = st.multiselect("Complexo Champions League", ["Arena", "Sala Glass", "Rooftop Maior", "Rooftop Menor"], default=["Arena"])
            local_str = ", ".join(locais_selecionados) if locais_selecionados else "Não informado"
            transmissao = st.radio("Transmissão para TVs?", ["Sim", "Não"], horizontal=True)
        with col3:
            equipe_tecnica = st.text_area("Equipe Técnica Escalada", placeholder="Ex: 01 Técnico Som, 01 Técnico Resolume...")

        st.markdown("### 🛠️ 2. Equipamentos em Contrato")
        equipamentos_contrato = st.text_area("Lista de Equipamentos Contratados", placeholder="Ex: Microfones, Mesas, Processadores...")

        st.markdown("### ➕ 3. Contratação Extra (Item por Linha)")
        df_extras_init = pd.DataFrame([{"Descrição": "Painel de LED Adicional", "Valor": 500.0}])
        df_extras_edit = st.data_editor(
            df_extras_init, num_rows="dynamic", use_container_width=True,
            column_config={
                "Descrição": st.column_config.TextColumn("Descrição do Item Extra", required=True),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=50.0)
            }, key="editor_extras_novo"
        )
        val_extra_total = float(df_extras_edit["Valor"].sum()) if not df_extras_edit.empty else 0.0

        st.markdown("### 💰 4. Valores do Orçamento Inicial")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            val_aprovado = st.number_input("Valor do Orçamento Base (R$)", min_value=0.0, step=100.0)
        with col_v2:
            fat_bruto_temp = val_aprovado + val_extra_total
            imp_temp = fat_bruto_temp * 0.10
            st.success(f"**Faturamento Bruto Total:** R$ {fat_bruto_temp:,.2f}\n• NF (10%): R$ {imp_temp:,.2f}")

        st.markdown("### 👥 5. Custos Operacionais & Logística")
        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
        with col_c1: custo_resolume = st.number_input("Técnico / Resolume (R$)", min_value=0.0, step=50.0)
        with col_c2: custo_iluminacao = st.number_input("Técnico Iluminação (R$)", min_value=0.0, step=50.0)
        with col_c3: custo_sonorizacao = st.number_input("Técnico Som (R$)", min_value=0.0, step=50.0)
        with col_c4: custo_diretor = st.number_input("Direção Técnica (R$)", min_value=0.0, step=50.0)
        with col_c5: custo_logistica = st.number_input("Logística / Estac. (R$)", min_value=0.0, step=20.0)

        st.markdown("### 🗓️ 6. Prazos e Observações")
        col_d1, col_d2 = st.columns(2)
        with col_d1: dt_pag_operacional = st.date_input("Data Pagamento Operacional")
        with col_d2: dt_rec_champions = st.date_input("Data Recebimento Client")

        obs_gerais = st.text_area("Observações Gerais")

        faturamento_bruto = val_aprovado + val_extra_total
        imposto_nf = faturamento_bruto * 0.10
        total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica
        lucro_real = faturamento_bruto - imposto_nf - total_custos_op

        st.markdown("---")
        if st.button("💾 Salvar Registro de Forma Permanente", use_container_width=True):
            novo_registro = {
                "Cliente": cliente, "Data Evento": data_evento.strftime("%d/%m/%Y"), "Horário": horario,
                "Complexo Champions": local_str, "Transmissão TVs": transmissao, "Aprovado": val_aprovado,
                "Val. Extra": val_extra_total, "Itens Extras": df_extras_edit.to_dict('records') if not df_extras_edit.empty else [],
                "Faturamento Bruto": faturamento_bruto, "10% NF": imposto_nf, "Custos Operacionais + Logística": total_custos_op,
                "Custo Resolume": custo_resolume, "Custo Iluminação": custo_iluminacao, "Custo Sonorização": custo_sonorizacao,
                "Custo Diretor": custo_diretor, "Custo Logística": custo_logistica, "Lucro Real": lucro_real,
                "Lucro Miguel Araújo": lucro_real * 0.50, "Lucro Antonio Carlos": lucro_real * 0.50,
                "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"), "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
                "Equipamentos": equipamentos_contrato if equipamentos_contrato else "Não especificado",
                "Equipe Técnica": equipe_tecnica if equipe_tecnica else "Não especificado",
                "Observações": obs_gerais if obs_gerais else "Nenhuma observação."
            }
            salvar_evento_db(novo_registro)
            st.success("✅ Faturamento gravado com sucesso no Banco de Dados!")
            st.rerun()

# ABA 2: EDIÇÃO E EXCLUSÃO
with aba2:
    st.subheader("✏️ Editar ou Excluir Registro")
    if not faturamentos:
        st.info("Nenhum evento cadastrado no banco de dados no momento.")
    else:
        idx_edit = st.selectbox(
            "Selecione o Evento que deseja alterar:", range(len(faturamentos)),
            format_func=lambda x: f"ID #{faturamentos[x]['id']} - {faturamentos[x]['Cliente']} ({faturamentos[x]['Data Evento']})"
        )
        
        reg_edit = faturamentos[idx_edit]
        
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

            e_equip = st.text_area("Equipamentos", value=reg_edit["Equipamentos"])
            e_equipe = st.text_area("Equipe Técnica", value=reg_edit["Equipe Técnica"])

            df_extras_existente = pd.DataFrame(reg_edit.get("Itens Extras", []))
            if df_extras_existente.empty:
                df_extras_existente = pd.DataFrame([{"Descrição": "", "Valor": 0.0}])
            
            e_extras_edit = st.data_editor(
                df_extras_existente, num_rows="dynamic", use_container_width=True,
                column_config={"Descrição": st.column_config.TextColumn("Descrição Extra"), "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")},
                key=f"editor_edit_{reg_edit['id']}"
            )

            col_ev1, col_ev2 = st.columns(2)
            with col_ev1:
                e_aprovado = st.number_input("Valor Aprovado Base (R$)", value=float(reg_edit["Aprovado"]), step=100.0)
            with col_ev2:
                e_resolume = st.number_input("Custo Resolume (R$)", value=float(reg_edit.get("Custo Resolume", 0.0)))
                e_iluminacao = st.number_input("Custo Iluminação (R$)", value=float(reg_edit.get("Custo Iluminação", 0.0)))
                e_sonorizacao = st.number_input("Custo Sonorização (R$)", value=float(reg_edit.get("Custo Sonorização", 0.0)))
                e_diretor = st.number_input("Custo Direção (R$)", value=float(reg_edit.get("Custo Diretor", 0.0)))
                e_logistica = st.number_input("Custo Logística (R$)", value=float(reg_edit.get("Custo Logística", 0.0)))

            e_obs = st.text_area("Observações", value=reg_edit["Observações"])

            col_btn_at, col_btn_del = st.columns([3, 1])
            with col_btn_at:
                btn_atualizar = st.form_submit_button("🔄 Atualizar Registro")
            with col_btn_del:
                btn_excluir = st.form_submit_button("❌ Excluir Registro")
            
            if btn_atualizar:
                e_val_extra_total = float(e_extras_edit["Valor"].sum()) if not e_extras_edit.empty else 0.0
                e_fat_bruto = e_aprovado + e_val_extra_total
                e_imp = e_fat_bruto * 0.10
                e_custos_total = e_resolume + e_iluminacao + e_sonorizacao + e_diretor + e_logistica
                e_lucro = e_fat_bruto - e_imp - e_custos_total
                
                reg_atualizado = {
                    "Cliente": e_cliente, "Data Evento": e_data, "Horário": e_horario, "Complexo Champions": e_complexo,
                    "Transmissão TVs": e_transmissao, "Aprovado": e_aprovado, "Val. Extra": e_val_extra_total,
                    "Itens Extras": e_extras_edit.to_dict('records') if not e_extras_edit.empty else [],
                    "Faturamento Bruto": e_fat_bruto, "10% NF": e_imp, "Custos Operacionais + Logística": e_custos_total,
                    "Custo Resolume": e_resolume, "Custo Iluminação": e_iluminacao, "Custo Sonorização": e_sonorizacao,
                    "Custo Diretor": e_diretor, "Custo Logística": e_logistica, "Lucro Real": e_lucro,
                    "Lucro Miguel Araújo": e_lucro * 0.50, "Lucro Antonio Carlos": e_lucro * 0.50,
                    "Pag. Operacional": reg_edit["Pag. Operacional"], "Rec. Champions": reg_edit["Rec. Champions"],
                    "Equipamentos": e_equip, "Equipe Técnica": e_equipe, "Observações": e_obs
                }
                atualizar_evento_db(reg_edit['id'], reg_atualizado)
                st.success("✅ Evento atualizado permanentemente!")
                st.rerun()

            if btn_excluir:
                deletar_evento_db(reg_edit['id'])
                st.warning("🗑️ Evento removido do Banco de Dados!")
                st.rerun()

# --- DASHBOARD DE RESULTADOS E EMISSÃO DE PDFS ---
if faturamentos:
    df = pd.DataFrame(faturamentos)
    st.markdown("---")
    st.subheader("📊 Indicadores Financeiros Gerais")
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Faturamento Bruto Total", f"R$ {df['Faturamento Bruto'].sum():,.2f}")
    kpi2.metric("Custos + NF (10%)", f"R$ {(df['10% NF'].sum() + df['Custos Operacionais + Logística'].sum()):,.2f}")
    kpi3.metric("Lucro Real Total", f"R$ {df['Lucro Real'].sum():,.2f}")
    kpi4.metric("Parte Miguel Araújo (50%)", f"R$ {df['Lucro Miguel Araújo'].sum():,.2f}")
    kpi5.metric("Parte Antonio Carlos (50%)", f"R$ {df['Lucro Antonio Carlos'].sum():,.2f}")

    st.markdown("---")
    st.subheader("📄 Emissão de PDF (Orçamento / Controle)")
    
    col_sel, col_btn1, col_btn2 = st.columns([2, 1, 1])
    with col_sel:
        evento_idx_pdf = st.selectbox(
            "Selecione o Evento para gerar o PDF:", range(len(faturamentos)),
            format_func=lambda x: f"{faturamentos[x]['Cliente']} - {faturamentos[x]['Data Evento']}"
        )
    
    reg_sel = faturamentos[evento_idx_pdf]
    
    with col_btn1:
        pdf_orcamento = gerar_pdf_evento(reg_sel, tipo_documento="ORCAMENTO")
        st.download_button("📄 Baixar ORÇAMENTO (Cliente)", data=pdf_orcamento, file_name=f"Orcamento_{reg_sel['Cliente']}.pdf", mime="application/pdf", use_container_width=True)

    with col_btn2:
        pdf_financeiro = gerar_pdf_evento(reg_sel, tipo_documento="FINANCEIRO")
        st.download_button("📊 Baixar CONTROLE (Interno)", data=pdf_financeiro, file_name=f"Controle_{reg_sel['Cliente']}.pdf", mime="application/pdf", use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Tabela Completa de Eventos")
    st.dataframe(df, use_container_width=True)
