import streamlit as st
import pandas as pd
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
            aprovado REAL DEFAULT 0,
            val_extra REAL DEFAULT 0,
            itens_extras TEXT,
            faturamento_bruto REAL DEFAULT 0,
            imposto_nf REAL DEFAULT 0,
            custos_total REAL DEFAULT 0,
            custo_resolume REAL DEFAULT 0,
            custo_iluminacao REAL DEFAULT 0,
            custo_sonorizacao REAL DEFAULT 0,
            custo_diretor REAL DEFAULT 0,
            custo_logistica REAL DEFAULT 0,
            custo_fornecedor_externo REAL DEFAULT 0,
            desc_fornecedor_externo TEXT DEFAULT '',
            val_recebido_cliente REAL DEFAULT 0,
            val_pago_equipe REAL DEFAULT 0,
            status_recebimento TEXT,
            status_pagamento TEXT,
            lucro_real REAL DEFAULT 0,
            lucro_miguel REAL DEFAULT 0,
            lucro_antonio REAL DEFAULT 0,
            pag_operacional TEXT,
            rec_champions TEXT,
            equipamentos TEXT,
            equipe_tecnica TEXT,
            observacoes TEXT
        )
    ''')
    conn.commit()
    
    colunas_necessarias = {
        "val_recebido_cliente": "REAL DEFAULT 0",
        "val_pago_equipe": "REAL DEFAULT 0",
        "status_recebimento": "TEXT DEFAULT 'Pendente'",
        "status_pagamento": "TEXT DEFAULT 'Pendente'",
        "lucro_real": "REAL DEFAULT 0",
        "lucro_miguel": "REAL DEFAULT 0",
        "lucro_antonio": "REAL DEFAULT 0",
        "custo_fornecedor_externo": "REAL DEFAULT 0",
        "desc_fornecedor_externo": "TEXT DEFAULT ''"
    }
    
    c.execute("PRAGMA table_info(eventos)")
    colunas_existentes = [info[1] for info in c.fetchall()]
    
    for col, tipo in colunas_necessarias.items():
        if col not in colunas_existentes:
            c.execute(f"ALTER TABLE eventos ADD COLUMN {col} {tipo}")
            
    conn.commit()
    conn.close()

def carregar_eventos():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM eventos ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    eventos = []
    for row in rows:
        d = dict(row)
        
        def to_float(val):
            try:
                return float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                return 0.0

        fat_bruto = to_float(d.get("faturamento_bruto"))
        imp_nf = to_float(d.get("imposto_nf"))
        custos_tot = to_float(d.get("custos_total"))
        lucro = to_float(d.get("lucro_real")) if d.get("lucro_real") is not None else (fat_bruto - imp_nf - custos_tot)

        eventos.append({
            "id": d.get("id"),
            "Cliente": d.get("cliente") or "Não informado",
            "Data Evento": d.get("data_evento") or "",
            "Horário": d.get("horario") or "",
            "Complexo Champions": d.get("complexo") or "",
            "Transmissão TVs": d.get("transmissao") or "Não",
            "Aprovado": to_float(d.get("aprovado")),
            "Val. Extra": to_float(d.get("val_extra")),
            "Itens Extras": json.loads(d.get("itens_extras")) if d.get("itens_extras") else [],
            "Faturamento Bruto": fat_bruto,
            "10% NF": imp_nf,
            "Custos Operacionais + Logística": custos_tot,
            "Custo Resolume": to_float(d.get("custo_resolume")),
            "Custo Iluminação": to_float(d.get("custo_iluminacao")),
            "Custo Sonorização": to_float(d.get("custo_sonorizacao")),
            "Custo Diretor": to_float(d.get("custo_diretor")),
            "Custo Logística": to_float(d.get("custo_logistica")),
            "Custo Fornecedor Externo": to_float(d.get("custo_fornecedor_externo")),
            "Desc. Fornecedor Externo": d.get("desc_fornecedor_externo") or "",
            "Valor Recebido Cliente": to_float(d.get("val_recebido_cliente")),
            "Valor Pago Equipe": to_float(d.get("val_pago_equipe")),
            "Status Recebimento": d.get("status_recebimento") or "Pendente",
            "Status Pagamento": d.get("status_pagamento") or "Pendente",
            "Lucro Real": lucro,
            "Lucro Miguel Araújo": lucro * 0.50,
            "Lucro Antonio Carlos": lucro * 0.50,
            "Pag. Operacional": d.get("pag_operacional") or "",
            "Rec. Champions": d.get("rec_champions") or "",
            "Equipamentos": d.get("equipamentos") or "",
            "Equipe Técnica": d.get("equipe_tecnica") or "",
            "Observações": d.get("observacoes") or ""
        })
    return eventos

def salvar_evento_db(reg):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO eventos (
            cliente, data_evento, horario, complexo, transmissao, aprovado, val_extra, itens_extras,
            faturamento_bruto, imposto_nf, custos_total, custo_resolume, custo_iluminacao, custo_sonorizacao,
            custo_diretor, custo_logistica, custo_fornecedor_externo, desc_fornecedor_externo, val_recebido_cliente,
            val_pago_equipe, status_recebimento, status_pagamento, lucro_real, lucro_miguel, lucro_antonio,
            pag_operacional, rec_champions, equipamentos, equipe_tecnica, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Complexo Champions"], reg["Transmissão TVs"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Custo Fornecedor Externo"],
        reg["Desc. Fornecedor Externo"], reg["Valor Recebido Cliente"], reg["Valor Pago Equipe"],
        reg["Status Recebimento"], reg["Status Pagamento"], reg["Lucro Real"], reg["Lucro Miguel Araújo"],
        reg["Lucro Antonio Carlos"], reg["Pag. Operacional"], reg["Rec. Champions"], reg["Equipamentos"],
        reg["Equipe Técnica"], reg["Observações"]
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
            custo_iluminacao=?, custo_sonorizacao=?, custo_diretor=?, custo_logistica=?, custo_fornecedor_externo=?,
            desc_fornecedor_externo=?, val_recebido_cliente=?, val_pago_equipe=?, status_recebimento=?,
            status_pagamento=?, lucro_real=?, lucro_miguel=?, lucro_antonio=?, pag_operacional=?,
            rec_champions=?, equipamentos=?, equipe_tecnica=?, observacoes=?
        WHERE id=?
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Complexo Champions"], reg["Transmissão TVs"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Custo Fornecedor Externo"],
        reg["Desc. Fornecedor Externo"], reg["Valor Recebido Cliente"], reg["Valor Pago Equipe"],
        reg["Status Recebimento"], reg["Status Pagamento"], reg["Lucro Real"], reg["Lucro Miguel Araújo"],
        reg["Lucro Antonio Carlos"], reg["Pag. Operacional"], reg["Rec. Champions"], reg["Equipamentos"],
        reg["Equipe Técnica"], reg["Observações"], id_evento
    ))
    conn.commit()
    conn.close()

def deletar_evento_db(id_evento):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM eventos WHERE id=?', (id_evento,))
    conn.commit()
    conn.close()

# GERADOR DE PDF DUAL COM ITENS EXTRAS DETALHADOS
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

    # Logótipo
    if os.path.exists("logo.jpg"):
        story.append(RLImage("logo.jpg", width=560, height=130))
        story.append(Spacer(1, 10))
    elif os.path.exists("logo.png"):
        story.append(RLImage("logo.png", width=560, height=130))
        story.append(Spacer(1, 10))

    # 1. Identificação do Evento
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

    # 2. Equipamentos Base
    sec2_hdr = Table([[Paragraph("🛠️ SETOR DE ENGENHARIA DE ÁUDIO, LUZ, VÍDEO & ESTRUTURA", sec_title_style)]], colWidths=[560])
    sec2_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(sec2_hdr)
    t2 = Table([[Paragraph("ITEM / ATIVO TÉCNICO CONTRATADO", th_style), Paragraph("STATUS OPERACIONAL", th_style)], [Paragraph(str(registro["Equipamentos"]).replace('\n', '<br/>'), td_style), Paragraph("INCLUSO", td_status)]], colWidths=[440, 120])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 6), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # 3. ITENS EXTRAS ADICIONADOS
    itens_extras = registro.get("Itens Extras", [])
    if itens_extras and len(itens_extras) > 0:
        sec_ext_hdr = Table([[Paragraph("➕ ITENS E SERVIÇOS ADICIONAIS (EXTRAS)", sec_title_style)]], colWidths=[560])
        sec_ext_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(sec_ext_hdr)

        dados_extras = [[Paragraph("DESCRIÇÃO DO ITEM EXTRA", th_style), Paragraph("VALOR (R$)", th_style)]]
        for item in itens_extras:
            desc = item.get("Descrição") or item.get("Descricao") or "Item Extra"
            val = float(item.get("Valor", 0.0))
            dados_extras.append([
                Paragraph(str(desc), td_style),
                Paragraph(f"R$ {val:,.2f}", td_bold)
            ])

        t_extras = Table(dados_extras, colWidths=[420, 140])
        t_extras.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(t_extras)
        story.append(Spacer(1, 10))

    # 4. Balanço Financeiro Interno (Apenas no PDF de Controle Financeiro)
    if tipo_documento == "FINANCEIRO":
        sec4_hdr = Table([[Paragraph("💰 BALANÇO FINANCEIRO & DIVISÃO DE LUCRO OPERACIONAL", sec_title_style)]], colWidths=[560])
        sec4_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(sec4_hdr)
        
        desc_ext_str = registro.get('Desc. Fornecedor Externo', '')
        lbl_forn = f"Forn. Externo ({desc_ext_str}):" if desc_ext_str else "Forn. Externo (DJ/Internet):"
        
        dados_sec4 = [
            [Paragraph("Faturamento Bruto:", th_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", td_bold), Paragraph("Imposto Nota Fiscal (10%):", th_style), Paragraph(f"R$ {registro['10% NF']:,.2f}", td_style)],
            [Paragraph("Custos Totais Operacionais:", th_style), Paragraph(f"R$ {registro['Custos Operacionais + Logística']:,.2f}", td_style), Paragraph(lbl_forn, th_style), Paragraph(f"R$ {registro['Custo Fornecedor Externo']:,.2f}", td_style)],
            [Paragraph("<b>LUCRO REAL LÍQUIDO</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Real']:,.2f}</b>", td_bold), Paragraph("", th_style), Paragraph("", td_style)],
            [Paragraph("<b>PARTE MIGUEL ARAÚJO (50%)</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Miguel Araújo']:,.2f}</b>", td_bold), Paragraph("<b>PARTE ANTONIO CARLOS (50%)</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Antonio Carlos']:,.2f}</b>", td_bold)]
        ]
        t4 = Table(dados_sec4, colWidths=[140, 140, 140, 140])
        t4.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 5)]))
        story.append(t4)
        story.append(Spacer(1, 12))

    # Rodapé com Valor Global
    val_box = Table([[Paragraph(f"VALOR FINANCEIRO GLOBAL ({registro['Cliente']}):", val_title_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", val_num_style)]], colWidths=[360, 200])
    val_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 10), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(val_box)

    doc.build(story)
    buffer.seek(0)
    return buffer

# Inicializa Banco de Dados
init_db()

# --- CONFIGURAÇÃO DA PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Miguel Araújo Produções - Gestão Financeira Unificada",
    page_icon="💰",
    layout="wide"
)

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

# CABEÇALHO
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
    st.subheader("Painel de Controle Financeiro, Recebimentos e Pagamentos")

st.markdown("---")

faturamentos = carregar_eventos()

# PAINEL GERAL DE INDICADORES (KPIs PROTEGIDOS)
if faturamentos:
    df_kpi = pd.DataFrame(faturamentos)
    
    total_faturado = float(df_kpi["Faturamento Bruto"].sum())
    total_custos_equipe = float(df_kpi["Custos Operacionais + Logística"].sum())
    total_impostos = float(df_kpi["10% NF"].sum())
    
    total_recebido = float(df_kpi["Valor Recebido Cliente"].sum())
    total_falta_receber = total_faturado - total_recebido
    
    total_pago_equipe = float(df_kpi["Valor Pago Equipe"].sum())
    total_falta_pagar_equipe = total_custos_equipe - total_pago_equipe
    
    lucro_liquido_total = float(df_kpi["Lucro Real"].sum())

    st.markdown("## 📊 Controle Financeiro Consolidado")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric("💵 Faturamento Bruto", f"R$ {total_faturado:,.2f}")
    kpi_col2.metric("✅ Total Recebido (Cliente)", f"R$ {total_recebido:,.2f}")
    kpi_col3.metric("⏳ A Receber (Cliente)", f"R$ {total_falta_receber:,.2f}")
    kpi_col4.metric("📈 Lucro Líquido Real", f"R$ {lucro_liquido_total:,.2f}")

    kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)
    kpi_col5.metric("👥 Custo Total Operacional", f"R$ {total_custos_equipe:,.2f}")
    kpi_col6.metric("💸 Total Já Pago (Equipe/Ext)", f"R$ {total_pago_equipe:,.2f}")
    kpi_col7.metric("⚠️ A Pagar Pessoas/Serviços", f"R$ {total_falta_pagar_equipe:,.2f}")
    kpi_col8.metric("🧾 Impostos Reservados (10% NF)", f"R$ {total_impostos:,.2f}")

    st.markdown("---")

aba1, aba2, aba3 = st.tabs(["➕ Novo Evento / Lançamento", "✏️ Baixas & Edição Financeira", "📊 Relatórios & PDFs"])

# ABA 1: NOVO EVENTO
with aba1:
    with st.expander("➕ Cadastrar Novo Evento e Valores", expanded=True):
        st.markdown("### 📋 1. Identificação do Evento")
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente = st.text_input("Cliente / Empresa", value="CHAMPIONS LEAGUE EXPERIENCE BRASIL")
            data_evento = st.date_input("Data do Evento", datetime.now())
            horario = st.text_input("Horário", value="08h às 18h")
        with col2:
            locais_selecionados = st.multiselect("Complexo Champions League", ["Arena", "Sala Glass", "Rooftop Maior", "Rooftop Menor"], default=["Arena"])
            local_str = ", ".join(locais_selecionados) if locais_selecionados else "Não informado"
            transmissao = st.radio("Transmissão para TVs?", ["Sim", "Não"], horizontal=True)
        with col3:
            equipe_tecnica = st.text_area("Descrição da Equipe Escalada", placeholder="Ex: 1 Tech Resolume, 1 Iluminação, 1 Som...")

        st.markdown("### 🛠️ 2. Equipamentos Contratados")
        equipamentos_contrato = st.text_area("Equipamentos em Contrato", placeholder="Ex: Painéis LED, Processadores, Microfones...")

        st.markdown("### ➕ 3. Adicionais e Extras")
        df_extras_init = pd.DataFrame([{"Descrição": "Painel de LED Adicional", "Valor": 0.0}])
        df_extras_edit = st.data_editor(
            df_extras_init, num_rows="dynamic", use_container_width=True,
            column_config={
                "Descrição": st.column_config.TextColumn("Descrição do Item Extra", required=True),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=50.0)
            }, key="editor_extras_novo"
        )
        val_extra_total = float(df_extras_edit["Valor"].sum()) if not df_extras_edit.empty else 0.0

        st.markdown("### 💰 4. Faturamento do Evento")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            val_aprovado = st.number_input("Valor Base Aprovado (R$)", min_value=0.0, step=100.0)
        with col_v2:
            fat_bruto_temp = val_aprovado + val_extra_total
            imp_temp = fat_bruto_temp * 0.10
            st.success(f"**Faturamento Bruto:** R$ {fat_bruto_temp:,.2f}\n• Imposto (10% NF): R$ {imp_temp:,.2f}")

        st.markdown("### 👥 5. Custos: Equipe Técnica, Logística & Fornecedores")
        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
        with col_c1: custo_resolume = st.number_input("Técnico Resolume (R$)", min_value=0.0, step=50.0)
        with col_c2: custo_iluminacao = st.number_input("Técnico Iluminação (R$)", min_value=0.0, step=50.0)
        with col_c3: custo_sonorizacao = st.number_input("Técnico Som (R$)", min_value=0.0, step=50.0)
        with col_c4: custo_diretor = st.number_input("Direção Técnica (R$)", min_value=0.0, step=50.0)
        with col_c5: custo_logistica = st.number_input("Logística / Frete (R$)", min_value=0.0, step=20.0)

        st.markdown("#### 🌐 Fornecedor Externo (Ex: DJ, Internet Dedicada, Estrutura Extra)")
        col_ext1, col_ext2 = st.columns([2, 1])
        with col_ext1:
            desc_externo = st.text_input("Descrição do Serviço do Fornecedor Externo", placeholder="Ex: Link Dedicado de Internet 100MB / DJ Pedro")
        with col_ext2:
            custo_externo = st.number_input("Valor Fornecedor Externo (R$)", min_value=0.0, step=50.0)

        st.markdown("### 💳 6. Status Inicial de Caixa")
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            val_recebido_init = st.number_input("Quanto o cliente JÁ PAGOU? (R$)", min_value=0.0, step=100.0, key="v_rec_init")
        with col_st2:
            val_pago_equipe_init = st.number_input("Quanto você JÁ PAGOU à equipe/fornecedores? (R$)", min_value=0.0, step=100.0, key="v_pag_init")

        col_d1, col_d2 = st.columns(2)
        with col_d1: dt_pag_operacional = st.date_input("Previsão Pagamento Operacional")
        with col_d2: dt_rec_champions = st.date_input("Previsão Recebimento Cliente")

        obs_gerais = st.text_area("Observações Financeiras / Gerais")

        faturamento_bruto = val_aprovado + val_extra_total
        imposto_nf = faturamento_bruto * 0.10
        total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica + custo_externo
        lucro_real = faturamento_bruto - imposto_nf - total_custos_op

        status_rec = "Pago Total" if val_recebido_init >= faturamento_bruto and faturamento_bruto > 0 else ("Parcial" if val_recebido_init > 0 else "Pendente")
        status_pag = "Pago Total" if val_pago_equipe_init >= total_custos_op and total_custos_op > 0 else ("Parcial" if val_pago_equipe_init > 0 else "Pendente")

        st.markdown("---")
        if st.button("💾 Gravar Evento no Controle Financeiro", use_container_width=True):
            novo_registro = {
                "Cliente": cliente, "Data Evento": data_evento.strftime("%d/%m/%Y"), "Horário": horario,
                "Complexo Champions": local_str, "Transmissão TVs": transmissao, "Aprovado": val_aprovado,
                "Val. Extra": val_extra_total, "Itens Extras": df_extras_edit.to_dict('records') if not df_extras_edit.empty else [],
                "Faturamento Bruto": faturamento_bruto, "10% NF": imposto_nf, "Custos Operacionais + Logística": total_custos_op,
                "Custo Resolume": custo_resolume, "Custo Iluminação": custo_iluminacao, "Custo Sonorização": custo_sonorizacao,
                "Custo Diretor": custo_diretor, "Custo Logística": custo_logistica,
                "Custo Fornecedor Externo": custo_externo, "Desc. Fornecedor Externo": desc_externo,
                "Valor Recebido Cliente": val_recebido_init, "Valor Pago Equipe": val_pago_equipe_init,
                "Status Recebimento": status_rec, "Status Pagamento": status_pag,
                "Lucro Real": lucro_real, "Lucro Miguel Araújo": lucro_real * 0.50, "Lucro Antonio Carlos": lucro_real * 0.50,
                "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"), "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
                "Equipamentos": equipamentos_contrato if equipamentos_contrato else "Não especificado",
                "Equipe Técnica": equipe_tecnica if equipe_tecnica else "Não especificado",
                "Observações": obs_gerais if obs_gerais else "Nenhuma observação."
            }
            salvar_evento_db(novo_registro)
            st.success("✅ Evento cadastrado com sucesso!")
            st.rerun()

# ABA 2: EDITAR E DAR BAIXA
with aba2:
    st.subheader("✏️ Dar Baixa em Recebimentos e Pagamentos")
    if not faturamentos:
        st.info("Nenhum evento registrado no banco de dados.")
    else:
        idx_edit = st.selectbox(
            "Selecione o Evento:", range(len(faturamentos)),
            format_func=lambda x: f"ID #{faturamentos[x]['id']} - {faturamentos[x]['Cliente']} ({faturamentos[x]['Data Evento']})"
        )
        
        reg = faturamentos[idx_edit]
        
        with st.form("form_baixa_financeira"):
            st.markdown(f"### 📍 Evento: **{reg['Cliente']}** ({reg['Data Evento']})")
            
            c_rec1, c_rec2, c_rec3 = st.columns(3)
            with c_rec1:
                e_fat_bruto = st.number_input("Faturamento Bruto (R$)", value=float(reg["Faturamento Bruto"]))
            with c_rec2:
                e_val_rec = st.number_input("Valor JÁ RECEBIDO do Cliente (R$)", value=float(reg["Valor Recebido Cliente"]))
            with c_rec3:
                falta_rec = e_fat_bruto - e_val_rec
                st.warning(f"**Falta Receber:** R$ {falta_rec:,.2f}")

            st.markdown("---")
            c_pag1, c_pag2, c_pag3 = st.columns(3)
            with c_pag1:
                e_custo_total = st.number_input("Custo Total Operacional (R$)", value=float(reg["Custos Operacionais + Logística"]))
            with c_pag2:
                e_val_pago = st.number_input("Valor JÁ PAGO à Equipe/Fornecedores (R$)", value=float(reg["Valor Pago Equipe"]))
            with c_pag3:
                falta_pag = e_custo_total - e_val_pago
                st.error(f"**Ainda Deve:** R$ {falta_pag:,.2f}")

            st.markdown("---")
            st.markdown("### 🛠️ Cachês Equipe Técnica")
            col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
            with col_p1: e_resolume = st.number_input("Resolume (R$)", value=float(reg["Custo Resolume"]))
            with col_p2: e_iluminacao = st.number_input("Iluminação (R$)", value=float(reg["Custo Iluminação"]))
            with col_p3: e_sonorizacao = st.number_input("Som (R$)", value=float(reg["Custo Sonorização"]))
            with col_p4: e_diretor = st.number_input("Diretor (R$)", value=float(reg["Custo Diretor"]))
            with col_p5: e_logistica = st.number_input("Logística (R$)", value=float(reg["Custo Logística"]))

            st.markdown("### 🌐 Fornecedor Externo")
            col_ext_e1, col_ext_e2 = st.columns([2, 1])
            with col_ext_e1:
                e_desc_externo = st.text_input("Descrição do Fornecedor Externo", value=reg.get("Desc. Fornecedor Externo", ""))
            with col_ext_e2:
                e_externo = st.number_input("Valor Fornecedor Externo (R$)", value=float(reg.get("Custo Fornecedor Externo", 0.0)))

            e_obs = st.text_area("Observações", value=reg["Observações"])

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                btn_salvar_baixa = st.form_submit_button("🔄 Salvar Alterações")
            with col_btn2:
                btn_excluir_eve = st.form_submit_button("❌ Excluir Evento")

            if btn_salvar_baixa:
                novos_custos = e_resolume + e_iluminacao + e_sonorizacao + e_diretor + e_logistica + e_externo
                novo_imposto = e_fat_bruto * 0.10
                novo_lucro = e_fat_bruto - novo_imposto - novos_custos

                st_rec = "Pago Total" if e_val_rec >= e_fat_bruto and e_fat_bruto > 0 else ("Parcial" if e_val_rec > 0 else "Pendente")
                st_pag = "Pago Total" if e_val_pago >= novos_custos and novos_custos > 0 else ("Parcial" if e_val_pago > 0 else "Pendente")

                reg_atualizado = {
                    "Cliente": reg["Cliente"], "Data Evento": reg["Data Evento"], "Horário": reg["Horário"],
                    "Complexo Champions": reg["Complexo Champions"], "Transmissão TVs": reg["Transmissão TVs"],
                    "Aprovado": reg["Aprovado"], "Val. Extra": reg["Val. Extra"], "Itens Extras": reg["Itens Extras"],
                    "Faturamento Bruto": e_fat_bruto, "10% NF": novo_imposto, "Custos Operacionais + Logística": novos_custos,
                    "Custo Resolume": e_resolume, "Custo Iluminação": e_iluminacao, "Custo Sonorização": e_sonorizacao,
                    "Custo Diretor": e_diretor, "Custo Logística": e_logistica,
                    "Custo Fornecedor Externo": e_externo, "Desc. Fornecedor Externo": e_desc_externo,
                    "Valor Recebido Cliente": e_val_rec, "Valor Pago Equipe": e_val_pago,
                    "Status Recebimento": st_rec, "Status Pagamento": st_pag,
                    "Lucro Real": novo_lucro, "Lucro Miguel Araújo": novo_lucro * 0.50, "Lucro Antonio Carlos": novo_lucro * 0.50,
                    "Pag. Operacional": reg["Pag. Operacional"], "Rec. Champions": reg["Rec. Champions"],
                    "Equipamentos": reg["Equipamentos"], "Equipe Técnica": reg["Equipe Técnica"], "Observações": e_obs
                }
                atualizar_evento_db(reg['id'], reg_atualizado)
                st.success("✅ Atualizado com sucesso!")
                st.rerun()

            if btn_excluir_eve:
                deletar_evento_db(reg['id'])
                st.warning("🗑️ Evento excluído!")
                st.rerun()

# ABA 3: TABELA DETALHADA E GERADOR DE PDF
with aba3:
    st.subheader("📄 Emissão de Documentos e PDFs")
    if faturamentos:
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
        st.subheader("📋 Relatório Geral Financeiro")
        
        df_full = pd.DataFrame(faturamentos)
        df_full["Falta Receber (Cliente)"] = df_full["Faturamento Bruto"] - df_full["Valor Recebido Cliente"]
        df_full["Falta Pagar (Equipe/Ext)"] = df_full["Custos Operacionais + Logística"] - df_full["Valor Pago Equipe"]

        st.dataframe(
            df_full[[
                "id", "Cliente", "Data Evento", "Faturamento Bruto", "Valor Recebido Cliente", "Falta Receber (Cliente)",
                "Custos Operacionais + Logística", "Desc. Fornecedor Externo", "Custo Fornecedor Externo", "Valor Pago Equipe", "Falta Pagar (Equipe/Ext)", "Lucro Real",
                "Lucro Miguel Araújo", "Lucro Antonio Carlos"
            ]],
            use_container_width=True
        )
