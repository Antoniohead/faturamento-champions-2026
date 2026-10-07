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
            data_montagem TEXT DEFAULT '',
            horario_montagem TEXT DEFAULT '',
            complexo TEXT,
            aprovado REAL DEFAULT 0,
            val_extra REAL DEFAULT 0,
            itens_extras TEXT DEFAULT '[]',
            faturamento_bruto REAL DEFAULT 0,
            imposto_nf REAL DEFAULT 0,
            responsavel_imposto TEXT DEFAULT 'Incluso no Valor',
            custos_total REAL DEFAULT 0,
            custo_resolume REAL DEFAULT 0,
            custo_iluminacao REAL DEFAULT 0,
            custo_sonorizacao REAL DEFAULT 0,
            custo_diretor REAL DEFAULT 0,
            custo_logistica REAL DEFAULT 0,
            custo_fornecedor_externo REAL DEFAULT 0,
            desc_fornecedor_externo TEXT DEFAULT '',
            fornecedores_externos TEXT DEFAULT '[]',
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
        "data_montagem": "TEXT DEFAULT ''",
        "horario_montagem": "TEXT DEFAULT ''",
        "responsavel_imposto": "TEXT DEFAULT 'Incluso no Valor'",
        "val_recebido_cliente": "REAL DEFAULT 0",
        "val_pago_equipe": "REAL DEFAULT 0",
        "status_recebimento": "TEXT DEFAULT 'Pendente'",
        "status_pagamento": "TEXT DEFAULT 'Pendente'",
        "lucro_real": "REAL DEFAULT 0",
        "lucro_miguel": "REAL DEFAULT 0",
        "lucro_antonio": "REAL DEFAULT 0",
        "custo_fornecedor_externo": "REAL DEFAULT 0",
        "desc_fornecedor_externo": "TEXT DEFAULT ''",
        "fornecedores_externos": "TEXT DEFAULT '[]'",
        "itens_extras": "TEXT DEFAULT '[]'"
    }
    
    c.execute("PRAGMA table_info(eventos)")
    colunas_existentes = [info[1] for info in c.fetchall()]
    
    for col, tipo in colunas_necessarias.items():
        if col not in colunas_existentes:
            c.execute(f"ALTER TABLE eventos ADD COLUMN {col} {tipo}")
            
    conn.commit()
    conn.close()

def parse_json_safely(val):
    if not val:
        return []
    try:
        data = json.loads(val)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []

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

        forn_ext_list = parse_json_safely(d.get("fornecedores_externos"))
        if not forn_ext_list and (d.get("custo_fornecedor_externo") or d.get("desc_fornecedor_externo")):
            c_val = to_float(d.get("custo_fornecedor_externo"))
            d_desc = d.get("desc_fornecedor_externo") or "Fornecedor Externo"
            if c_val > 0 or d_desc:
                forn_ext_list = [{"Descrição": d_desc, "Valor": c_val}]

        custo_forn_total = sum(to_float(f.get("Valor", 0.0)) for f in forn_ext_list)

        eventos.append({
            "id": d.get("id"),
            "Cliente": d.get("cliente") or "Não informado",
            "Data Evento": d.get("data_evento") or "",
            "Horário": d.get("horario") or "",
            "Data Montagem": d.get("data_montagem") or "",
            "Horário Montagem": d.get("horario_montagem") or "",
            "Complexo / Local": d.get("complexo") or "",
            "Aprovado": to_float(d.get("aprovado")),
            "Val. Extra": to_float(d.get("val_extra")),
            "Itens Extras": parse_json_safely(d.get("itens_extras")),
            "Faturamento Bruto": fat_bruto,
            "10% NF": imp_nf,
            "Responsável Imposto": d.get("responsavel_imposto") or "Incluso no Valor",
            "Custos Operacionais + Logística": custos_tot,
            "Custo Resolume": to_float(d.get("custo_resolume")),
            "Custo Iluminação": to_float(d.get("custo_iluminacao")),
            "Custo Sonorização": to_float(d.get("custo_sonorizacao")),
            "Custo Diretor": to_float(d.get("custo_diretor")),
            "Custo Logística": to_float(d.get("custo_logistica")),
            "Fornecedores Externos": forn_ext_list,
            "Custo Fornecedor Externo": custo_forn_total,
            "Desc. Fornecedor Externo": ", ".join([f.get("Descrição", "") for f in forn_ext_list]),
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
            cliente, data_evento, horario, data_montagem, horario_montagem, complexo, aprovado, val_extra, itens_extras,
            faturamento_bruto, imposto_nf, responsavel_imposto, custos_total, custo_resolume, custo_iluminacao, custo_sonorizacao,
            custo_diretor, custo_logistica, custo_fornecedor_externo, desc_fornecedor_externo, fornecedores_externos,
            val_recebido_cliente, val_pago_equipe, status_recebimento, status_pagamento, lucro_real, lucro_miguel,
            lucro_antonio, pag_operacional, rec_champions, equipamentos, equipe_tecnica, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Data Montagem"], reg["Horário Montagem"], reg["Complexo / Local"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Responsável Imposto"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Custo Fornecedor Externo"],
        reg["Desc. Fornecedor Externo"], json.dumps(reg["Fornecedores Externos"]), reg["Valor Recebido Cliente"],
        reg["Valor Pago Equipe"], reg["Status Recebimento"], reg["Status Pagamento"], reg["Lucro Real"],
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
            cliente=?, data_evento=?, horario=?, data_montagem=?, horario_montagem=?, complexo=?, aprovado=?, val_extra=?,
            itens_extras=?, faturamento_bruto=?, imposto_nf=?, responsavel_imposto=?, custos_total=?, custo_resolume=?,
            custo_iluminacao=?, custo_sonorizacao=?, custo_diretor=?, custo_logistica=?, custo_fornecedor_externo=?,
            desc_fornecedor_externo=?, fornecedores_externos=?, val_recebido_cliente=?, val_pago_equipe=?,
            status_recebimento=?, status_pagamento=?, lucro_real=?, lucro_miguel=?, lucro_antonio=?,
            pag_operacional=?, rec_champions=?, equipamentos=?, equipe_tecnica=?, observacoes=?
        WHERE id=?
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Data Montagem"], reg["Horário Montagem"], reg["Complexo / Local"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Responsável Imposto"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Custo Fornecedor Externo"],
        reg["Desc. Fornecedor Externo"], json.dumps(reg["Fornecedores Externos"]), reg["Valor Recebido Cliente"],
        reg["Valor Pago Equipe"], reg["Status Recebimento"], reg["Status Pagamento"], reg["Lucro Real"],
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

# GERADOR DE PDF DUAL
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
    nota_text_style = ParagraphStyle('NotaText', parent=styles['Normal'], fontName='Helvetica', fontSize=7, textColor=colors.HexColor("#4A3E39"), leading=9)

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
    
    dt_montagem_str = f"{registro.get('Data Montagem', '')} {registro.get('Horário Montagem', '')}".strip()
    if not dt_montagem_str:
        dt_montagem_str = "Não informada"

    if tipo_documento == "ORCAMENTO":
        dados_sec1 = [
            [Paragraph("CLIENTE / EMPRESA", th_style), Paragraph(str(registro["Cliente"]), td_bold), Paragraph("DATA DO EVENTO", th_style), Paragraph(f"{registro['Data Evento']} ({registro['Horário']})", td_style)],
            [Paragraph("LOCAL / ESPAÇO", th_style), Paragraph(str(registro["Complexo / Local"]), td_style), Paragraph("DATA MONTAGEM", th_style), Paragraph(dt_montagem_str, td_style)],
            [Paragraph("OBSERVAÇÕES", th_style), Paragraph(str(registro["Observações"]), td_style), Paragraph("", th_style), Paragraph("", td_style)]
        ]
    else:
        dados_sec1 = [
            [Paragraph("CLIENTE / EMPRESA", th_style), Paragraph(str(registro["Cliente"]), td_bold), Paragraph("DATA DO EVENTO", th_style), Paragraph(f"{registro['Data Evento']} ({registro['Horário']})", td_style)],
            [Paragraph("LOCAL / ESPAÇO", th_style), Paragraph(str(registro["Complexo / Local"]), td_style), Paragraph("DATA MONTAGEM", th_style), Paragraph(dt_montagem_str, td_style)],
            [Paragraph("EQUIPE ESCALADA", th_style), Paragraph(str(registro["Equipe Técnica"]).replace('\n', '<br/>'), td_style), Paragraph("OBSERVAÇÕES", th_style), Paragraph(str(registro["Observações"]), td_style)]
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

    # 3. RESUMO FINANCEIRO
    val_base = float(registro.get("Aprovado", 0.0))
    val_extra_tot = float(registro.get("Val. Extra", 0.0))
    val_imposto = float(registro.get("10% NF", 0.0))
    resp_imposto = registro.get("Responsável Imposto", "Incluso no Valor")
    itens_extras = registro.get("Itens Extras", [])

    if tipo_documento == "ORCAMENTO":
        sec_or_hdr = Table([[Paragraph("💵 RESUMO DE VALORES (ESCOPO BASE + ADICIONAIS)", sec_title_style)]], colWidths=[560])
        sec_or_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(sec_or_hdr)

        dados_orc_resumo = [
            [Paragraph("ESCOPO BASE APROVADO", th_style), Paragraph("STATUS / DESCRIÇÃO", th_style), Paragraph("VALOR BASE (R$)", th_style)],
            [Paragraph("Estrutura, Equipamentos e Serviço Base", td_style), Paragraph("Pacote Padrão Aprovado", td_style), Paragraph(f"R$ {val_base:,.2f}", td_bold)]
        ]

        if itens_extras and len(itens_extras) > 0:
            for item in itens_extras:
                desc = item.get("Descrição") or item.get("Descricao") or "Item Extra"
                val = float(item.get("Valor", 0.0))
                dados_orc_resumo.append([
                    Paragraph(f"➕ Extra: {desc}", td_style),
                    Paragraph("Item Solicitado Adicionalmente", td_style),
                    Paragraph(f"R$ {val:,.2f}", td_bold)
                ])

            dados_orc_resumo.append([
                Paragraph("<b>SUBTOTAL DE ADICIONAIS / EXTRAS</b>", th_style),
                Paragraph("", th_style),
                Paragraph(f"<b>R$ {val_extra_tot:,.2f}</b>", td_bold)
            ])

        if resp_imposto == "Por Conta do Cliente":
            dados_orc_resumo.append([
                Paragraph("<b>IMPOSTOS E ENCARGOS FISCAIS (10% NF)</b>", th_style),
                Paragraph("Por conta do Cliente / Adicionado ao Total", td_style),
                Paragraph(f"<b>R$ {val_imposto:,.2f}</b>", td_bold)
            ])

        t_orc_resumo = Table(dados_orc_resumo, colWidths=[240, 180, 140])
        t_orc_resumo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        story.append(t_orc_resumo)
        story.append(Spacer(1, 10))

    # 4. Balanço Financeiro Interno
    if tipo_documento == "FINANCEIRO":
        if itens_extras and len(itens_extras) > 0:
            sec_ext_hdr = Table([[Paragraph("➕ ITENS E SERVIÇOS ADICIONAIS (EXTRAS)", sec_title_style)]], colWidths=[560])
            sec_ext_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
            story.append(sec_ext_hdr)

            dados_extras = [[Paragraph("DESCRIÇÃO DO ITEM EXTRA", th_style), Paragraph("VALOR (R$)", th_style)]]
            for item in itens_extras:
                desc = item.get("Descrição") or item.get("Descricao") or "Item Extra"
                val = float(item.get("Valor", 0.0))
                dados_extras.append([Paragraph(str(desc), td_style), Paragraph(f"R$ {val:,.2f}", td_bold)])

            t_extras = Table(dados_extras, colWidths=[420, 140])
            t_extras.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
                ('PADDING', (0,0), (-1,-1), 5), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            story.append(t_extras)
            story.append(Spacer(1, 10))

        fornecedores_list = registro.get("Fornecedores Externos", [])
        if fornecedores_list:
            sec_forn_hdr = Table([[Paragraph("🌐 FORNECEDORES EXTERNOS CONTRATADOS", sec_title_style)]], colWidths=[560])
            sec_forn_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
            story.append(sec_forn_hdr)

            dados_forn = [[Paragraph("SERVIÇO / FORNECEDOR", th_style), Paragraph("CUSTO (R$)", th_style)]]
            for f_item in fornecedores_list:
                f_desc = f_item.get("Descrição") or "Fornecedor Externo"
                f_val = float(f_item.get("Valor", 0.0))
                dados_forn.append([Paragraph(str(f_desc), td_style), Paragraph(f"R$ {f_val:,.2f}", td_bold)])

            t_forn = Table(dados_forn, colWidths=[420, 140])
            t_forn.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
                ('PADDING', (0,0), (-1,-1), 5), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            story.append(t_forn)
            story.append(Spacer(1, 10))

        sec4_hdr = Table([[Paragraph("💰 BALANÇO FINANCEIRO & DIVISÃO DE LUCRO OPERACIONAL", sec_title_style)]], colWidths=[560])
        sec4_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(sec4_hdr)
        
        dados_sec4 = [
            [Paragraph("Faturamento Bruto:", th_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", td_bold), Paragraph(f"Imposto NF ({resp_imposto}):", th_style), Paragraph(f"R$ {registro['10% NF']:,.2f}", td_style)],
            [Paragraph("Custos Operacionais Totais:", th_style), Paragraph(f"R$ {registro['Custos Operacionais + Logística']:,.2f}", td_style), Paragraph("Total Fornecedores Ext.:", th_style), Paragraph(f"R$ {registro['Custo Fornecedor Externo']:,.2f}", td_style)],
            [Paragraph("<b>LUCRO REAL LÍQUIDO</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Real']:,.2f}</b>", td_bold), Paragraph("", th_style), Paragraph("", td_style)],
            [Paragraph("<b>PARTE MIGUEL ARAÚJO (50%)</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Miguel Araújo']:,.2f}</b>", td_bold), Paragraph("<b>PARTE ANTONIO CARLOS (50%)</b>", th_style), Paragraph(f"<b>R$ {registro['Lucro Antonio Carlos']:,.2f}</b>", td_bold)]
        ]
        t4 = Table(dados_sec4, colWidths=[140, 140, 140, 140])
        t4.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 5)]))
        story.append(t4)
        story.append(Spacer(1, 12))

    val_box = Table([[Paragraph(f"VALOR FINANCEIRO GLOBAL ({registro['Cliente']}):", val_title_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", val_num_style)]], colWidths=[360, 200])
    val_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 10), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(val_box)

    if tipo_documento == "ORCAMENTO":
        story.append(Spacer(1, 12))
        texto_notas = """
        <b>⚠️ NOTAS DE CONVENÇÃO E CONDIÇÕES GERAIS</b><br/><br/>
        • <b>Otimização de Custos (Patrimônio do Local):</b> Em conformidade com a estratégia acordada, os custos de locação de ativos já disponíveis no estoque fixo da casa (como conversores/transmitters, receivers e mesas de som sobressalentes) foram integralmente deduzidos ou omitidos, evitando compras ou cobranças redundantes.<br/>
        • <b>Período Operacional:</b> As diárias comerciais acima referem-se a uma jornada padrão por evento no período de 12hs. Prorrogações ou alterações de rider deverão ser notificadas com antecedência de 48 horas.<br/>
        • <b>Faturamento & Compliance:</b> Pagamentos deverão ser realizados preferencialmente de forma antecipada à data dos eventos. As Notas Fiscais (NF) de prestação de serviços e locação serão emitidas no dia útil subsequente à realização de cada agenda.
        """
        t_notas = Table([[Paragraph(texto_notas, nota_text_style)]], colWidths=[560])
        t_notas.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF6EE")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
            ('PADDING', (0,0), (-1,-1), 8)
        ]))
        story.append(t_notas)

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

# --- PAINEL GERAL DE INDICADORES (COM FILTRO POR CLIENTE) ---
if faturamentos:
    df_kpi_raw = pd.DataFrame(faturamentos)
    
    # Lista de clientes únicos para seleção
    clientes_unicos = sorted(list(set(df_kpi_raw["Cliente"].dropna().tolist())))
    opcoes_filtro_cliente = ["Todos os Clientes (Consolidado Geral)"] + clientes_unicos
    
    st.markdown("## 📊 Controle Financeiro por Cliente")
    cliente_selecionado_kpi = st.selectbox("🔍 Selecione o Cliente para filtrar os indicadores:", opcoes_filtro_cliente)
    
    if cliente_selecionado_kpi != "Todos os Clientes (Consolidado Geral)":
        df_kpi = df_kpi_raw[df_kpi_raw["Cliente"] == cliente_selecionado_kpi]
        lbl_contexto = f"Cliente: {cliente_selecionado_kpi}"
    else:
        df_kpi = df_kpi_raw
        lbl_contexto = "Consolidado Geral"

    total_faturado = float(df_kpi["Faturamento Bruto"].sum())
    total_custos_equipe = float(df_kpi["Custos Operacionais + Logística"].sum())
    total_impostos = float(df_kpi["10% NF"].sum())
    
    total_recebido = float(df_kpi["Valor Recebido Cliente"].sum())
    total_falta_receber = total_faturado - total_recebido
    
    total_pago_equipe = float(df_kpi["Valor Pago Equipe"].sum())
    total_falta_pagar_equipe = total_custos_equipe - total_pago_equipe
    
    lucro_liquido_total = float(df_kpi["Lucro Real"].sum())

    st.caption(f"Exibindo dados de: **{lbl_contexto}** ({len(df_kpi)} evento(s) encontrado(s))")

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

    # RESUMO COMPARATIVO POR CLIENTE
    with st.expander("🏢 Visão Consolidada Comparativa por Cliente (Tabela)", expanded=False):
        df_agrupado = df_kpi_raw.groupby("Cliente").agg({
            "id": "count",
            "Faturamento Bruto": "sum",
            "Valor Recebido Cliente": "sum",
            "Custos Operacionais + Logística": "sum",
            "Valor Pago Equipe": "sum",
            "Lucro Real": "sum"
        }).reset_index()

        df_agrupado.rename(columns={
            "id": "Qtd Eventos",
            "Faturamento Bruto": "Faturamento Total",
            "Valor Recebido Cliente": "Total Recebido",
            "Custos Operacionais + Logística": "Custos Totais",
            "Valor Pago Equipe": "Total Pago Equipe",
            "Lucro Real": "Lucro Líquido Total"
        }, inplace=True)

        df_agrupado["A Receber"] = df_agrupado["Faturamento Total"] - df_agrupado["Total Recebido"]
        df_agrupado["A Pagar"] = df_agrupado["Custos Totais"] - df_agrupado["Total Pago Equipe"]

        st.dataframe(
            df_agrupado[[
                "Cliente", "Qtd Eventos", "Faturamento Total", "Total Recebido", "A Receber",
                "Custos Totais", "Total Pago Equipe", "A Pagar", "Lucro Líquido Total"
            ]],
            use_container_width=True
        )

    st.markdown("---")

aba1, aba2, aba3 = st.tabs(["➕ Novo Evento / Lançamento", "✏️ Baixas & Edição Completa", "📊 Relatórios & PDFs"])

# ABA 1: NOVO EVENTO
with aba1:
    with st.expander("➕ Cadastrar Novo Evento e Valores", expanded=True):
        st.markdown("### 📋 1. Identificação do Evento")
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente = st.text_input("Cliente / Empresa", placeholder="Digite o nome do cliente/empresa...")
            data_evento = st.date_input("Data do Evento", datetime.now())
            horario = st.text_input("Horário do Evento", value="08h às 18h")
        with col2:
            complexo_local = st.text_input("Local / Espaço do Evento", placeholder="Ex: Arena, Rooftop, Espaço das Américas...")
            data_montagem = st.date_input("Data da Montagem", datetime.now())
            horario_montagem = st.text_input("Horário da Montagem", value="06h às 10h")
        with col3:
            equipe_tecnica = st.text_area("Descrição da Equipe Escalada (Uso Interno)", placeholder="Ex: 1 Tech Resolume, 1 Iluminação, 1 Som...")

        st.markdown("### 🛠️ 2. Equipamentos Contratados")
        equipamentos_contrato = st.text_area("Equipamentos em Contrato", placeholder="Ex: Painéis LED, Processadores, Microfones...")

        st.markdown("### ➕ 3. Adicionais e Extras")
        df_extras_init = pd.DataFrame([{"Descrição": "", "Valor": 0.0}])
        df_extras_edit = st.data_editor(
            df_extras_init, num_rows="dynamic", use_container_width=True,
            column_config={
                "Descrição": st.column_config.TextColumn("Descrição do Item Extra", required=True),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=50.0)
            }, key="editor_extras_novo"
        )
        val_extra_total = float(df_extras_edit["Valor"].sum()) if not df_extras_edit.empty else 0.0

        st.markdown("### 💰 4. Faturamento & Negociação Fiscal")
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            val_aprovado = st.number_input("Valor Base Aprovado (R$)", min_value=0.0, step=100.0)
        with col_v2:
            resp_imposto = st.selectbox("Imposto Nota Fiscal (10% NF):", ["Incluso no Valor", "Por Conta do Cliente", "Isento / Não Aplicável"])
        
        base_e_extra = val_aprovado + val_extra_total
        if resp_imposto == "Por Conta do Cliente":
            imposto_nf_calc = base_e_extra * 0.10
            faturamento_bruto_calc = base_e_extra + imposto_nf_calc
        elif resp_imposto == "Incluso no Valor":
            imposto_nf_calc = base_e_extra * 0.10
            faturamento_bruto_calc = base_e_extra
        else:
            imposto_nf_calc = 0.0
            faturamento_bruto_calc = base_e_extra

        with col_v3:
            st.success(f"**Faturamento Bruto Final:** R$ {faturamento_bruto_calc:,.2f}\n• Base: R$ {val_aprovado:,.2f} | Extras: R$ {val_extra_total:,.2f}\n• Imposto (10% NF): R$ {imposto_nf_calc:,.2f} ({resp_imposto})")

        st.markdown("### 👥 5. Custos: Equipe Técnica, Logística & Fornecedores")
        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
        with col_c1: custo_resolume = st.number_input("Técnico Resolume (R$)", min_value=0.0, step=50.0)
        with col_c2: custo_iluminacao = st.number_input("Técnico Iluminação (R$)", min_value=0.0, step=50.0)
        with col_c3: custo_sonorizacao = st.number_input("Técnico Som (R$)", min_value=0.0, step=50.0)
        with col_c4: custo_diretor = st.number_input("Direção Técnica (R$)", min_value=0.0, step=50.0)
        with col_c5: custo_logistica = st.number_input("Logística / Frete (R$)", min_value=0.0, step=20.0)

        st.markdown("#### 🌐 Fornecedores Externos (Ex: DJ, Internet Dedicada, Gerador, etc.)")
        df_forn_init = pd.DataFrame([{"Descrição": "", "Valor": 0.0}])
        df_forn_edit = st.data_editor(
            df_forn_init, num_rows="dynamic", use_container_width=True,
            column_config={
                "Descrição": st.column_config.TextColumn("Descrição / Nome do Fornecedor", required=True),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=50.0)
            }, key="editor_fornecedores_novo"
        )
        
        fornecedores_externos_novo = df_forn_edit.to_dict('records') if not df_forn_edit.empty else []
        custo_externo_total = float(df_forn_edit["Valor"].sum()) if not df_forn_edit.empty else 0.0
        desc_externo_concat = ", ".join([str(f.get("Descrição", "")) for f in fornecedores_externos_novo if f.get("Descrição")])

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

        total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica + custo_externo_total
        
        if resp_imposto == "Por Conta do Cliente":
            lucro_real = (faturamento_bruto_calc - imposto_nf_calc) - imposto_nf_calc - total_custos_op
        else:
            lucro_real = faturamento_bruto_calc - imposto_nf_calc - total_custos_op

        status_rec = "Pago Total" if val_recebido_init >= faturamento_bruto_calc and faturamento_bruto_calc > 0 else ("Parcial" if val_recebido_init > 0 else "Pendente")
        status_pag = "Pago Total" if val_pago_equipe_init >= total_custos_op and total_custos_op > 0 else ("Parcial" if val_pago_equipe_init > 0 else "Pendente")

        st.markdown("---")
        if st.button("💾 Gravar Evento no Controle Financeiro", use_container_width=True):
            novo_registro = {
                "Cliente": cliente if cliente else "Não informado",
                "Data Evento": data_evento.strftime("%d/%m/%Y"),
                "Horário": horario,
                "Data Montagem": data_montagem.strftime("%d/%m/%Y"),
                "Horário Montagem": horario_montagem,
                "Complexo / Local": complexo_local if complexo_local else "Não informado",
                "Aprovado": val_aprovado,
                "Val. Extra": val_extra_total,
                "Itens Extras": df_extras_edit.to_dict('records') if not df_extras_edit.empty else [],
                "Faturamento Bruto": faturamento_bruto_calc,
                "10% NF": imposto_nf_calc,
                "Responsável Imposto": resp_imposto,
                "Custos Operacionais + Logística": total_custos_op,
                "Custo Resolume": custo_resolume,
                "Custo Iluminação": custo_iluminacao,
                "Custo Sonorização": custo_sonorizacao,
                "Custo Diretor": custo_diretor,
                "Custo Logística": custo_logistica,
                "Custo Fornecedor Externo": custo_externo_total,
                "Desc. Fornecedor Externo": desc_externo_concat,
                "Fornecedores Externos": fornecedores_externos_novo,
                "Valor Recebido Cliente": val_recebido_init,
                "Valor Pago Equipe": val_pago_equipe_init,
                "Status Recebimento": status_rec,
                "Status Pagamento": status_pag,
                "Lucro Real": lucro_real,
                "Lucro Miguel Araújo": lucro_real * 0.50,
                "Lucro Antonio Carlos": lucro_real * 0.50,
                "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"),
                "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
                "Equipamentos": equipamentos_contrato if equipamentos_contrato else "Não especificado",
                "Equipe Técnica": equipe_tecnica if equipe_tecnica else "Não especificado",
                "Observações": obs_gerais if obs_gerais else "Nenhuma observação."
            }
            salvar_evento_db(novo_registro)
            st.success("✅ Evento cadastrado com sucesso!")
            st.rerun()

# ABA 2: EDITAR COMPLETO E DAR BAIXA
with aba2:
    st.subheader("✏️ Edição Completa e Baixas do Evento")
    if not faturamentos:
        st.info("Nenhum evento registrado no banco de dados.")
    else:
        idx_edit = st.selectbox(
            "Selecione o Evento para Editar:", range(len(faturamentos)),
            format_func=lambda x: f"ID #{faturamentos[x]['id']} - {faturamentos[x]['Cliente']} ({faturamentos[x]['Data Evento']})"
        )
        
        reg = faturamentos[idx_edit]
        
        with st.form(f"form_edicao_completa_{reg['id']}"):
            st.markdown(f"### 📍 Editando Evento ID #{reg['id']}")
            
            # 1. Identificação Editável
            st.markdown("#### 📋 1. Identificação do Evento")
            ce_col1, ce_col2, ce_col3 = st.columns(3)
            with ce_col1:
                e_cliente = st.text_input("Cliente / Empresa", value=reg["Cliente"])
                try:
                    dt_parsed = datetime.strptime(reg["Data Evento"], "%d/%m/%Y").date()
                except Exception:
                    dt_parsed = datetime.now().date()
                e_data_evento = st.date_input("Data do Evento", value=dt_parsed)
                e_horario = st.text_input("Horário do Evento", value=reg["Horário"])

            with ce_col2:
                e_complexo_local = st.text_input("Local / Espaço do Evento", value=reg["Complexo / Local"])
                try:
                    dt_mont_parsed = datetime.strptime(reg["Data Montagem"], "%d/%m/%Y").date() if reg["Data Montagem"] else datetime.now().date()
                except Exception:
                    dt_mont_parsed = datetime.now().date()
                e_data_montagem = st.date_input("Data da Montagem", value=dt_mont_parsed)
                e_horario_montagem = st.text_input("Horário da Montagem", value=reg["Horário Montagem"])

            with ce_col3:
                e_equipe_tecnica = st.text_area("Descrição da Equipe Escalada (Uso Interno)", value=reg["Equipe Técnica"])

            st.markdown("#### 🛠️ 2. Equipamentos Contratados")
            e_equipamentos = st.text_area("Equipamentos em Contrato", value=reg["Equipamentos"])

            st.markdown("#### ➕ 3. Itens e Serviços Extras")
            extras_existentes = reg.get("Itens Extras", [])
            df_extras_edit_existing = pd.DataFrame(extras_existentes if extras_existentes else [{"Descrição": "", "Valor": 0.0}])
            df_extras_updated = st.data_editor(
                df_extras_edit_existing, num_rows="dynamic", use_container_width=True,
                column_config={
                    "Descrição": st.column_config.TextColumn("Descrição do Item Extra", required=True),
                    "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=50.0)
                }, key=f"editor_extras_edit_{reg['id']}"
            )
            e_val_extra_total = float(df_extras_updated["Valor"].sum()) if not df_extras_updated.empty else 0.0

            st.markdown("#### 💰 4. Faturamento & Negociação Fiscal")
            col_ev1, col_ev2, col_ev3 = st.columns(3)
            with col_ev1:
                e_val_aprovado = st.number_input("Valor Base Aprovado (R$)", value=float(reg["Aprovado"]), min_value=0.0, step=100.0)
            
            opcoes_resp = ["Incluso no Valor", "Por Conta do Cliente", "Isento / Não Aplicável"]
            resp_atual = reg.get("Responsável Imposto", "Incluso no Valor")
            idx_resp = opcoes_resp.index(resp_atual) if resp_atual in opcoes_resp else 0
            
            with col_ev2:
                e_resp_imposto = st.selectbox("Imposto Nota Fiscal (10% NF):", opcoes_resp, index=idx_resp)

            e_base_e_extra = e_val_aprovado + e_val_extra_total
            if e_resp_imposto == "Por Conta do Cliente":
                e_imposto_nf_calc = e_base_e_extra * 0.10
                e_fat_bruto_calc = e_base_e_extra + e_imposto_nf_calc
            elif e_resp_imposto == "Incluso no Valor":
                e_imposto_nf_calc = e_base_e_extra * 0.10
                e_fat_bruto_calc = e_base_e_extra
            else:
                e_imposto_nf_calc = 0.0
                e_fat_bruto_calc = e_base_e_extra

            with col_ev3:
                st.info(f"Faturamento Bruto Total: **R$ {e_fat_bruto_calc:,.2f}**\n• NF: R$ {e_imposto_nf_calc:,.2f} ({e_resp_imposto})")

            st.markdown("#### 👥 5. Custos: Equipe Técnica, Logística & Cachês")
            col_ep1, col_ep2, col_ep3, col_ep4, col_ep5 = st.columns(5)
            with col_ep1: e_resolume = st.number_input("Resolume (R$)", value=float(reg["Custo Resolume"]))
            with col_ep2: e_iluminacao = st.number_input("Iluminação (R$)", value=float(reg["Custo Iluminação"]))
            with col_ep3: e_sonorizacao = st.number_input("Som (R$)", value=float(reg["Custo Sonorização"]))
            with col_ep4: e_diretor = st.number_input("Diretor (R$)", value=float(reg["Custo Diretor"]))
            with col_ep5: e_logistica = st.number_input("Logística (R$)", value=float(reg["Custo Logística"]))

            st.markdown("#### 🌐 Fornecedores Externos")
            forn_existentes = reg.get("Fornecedores Externos", [])
            if not forn_existentes:
                forn_existentes = [{"Descrição": reg.get("Desc. Fornecedor Externo", ""), "Valor": float(reg.get("Custo Fornecedor Externo", 0.0))}]
            
            df_forn_edit_existing = pd.DataFrame(forn_existentes)
            df_forn_updated = st.data_editor(
                df_forn_edit_existing, num_rows="dynamic", use_container_width=True,
                column_config={
                    "Descrição": st.column_config.TextColumn("Descrição / Nome do Fornecedor", required=True),
                    "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=50.0)
                }, key=f"editor_forn_edit_{reg['id']}"
            )

            st.markdown("#### 💳 6. Baixas de Caixa (Pagamentos e Recebimentos)")
            c_rec1, c_rec2 = st.columns(2)
            with c_rec1:
                e_val_rec = st.number_input("Valor JÁ RECEBIDO do Cliente (R$)", value=float(reg["Valor Recebido Cliente"]))
            with c_rec2:
                e_val_pago = st.number_input("Valor JÁ PAGO à Equipe/Fornecedores (R$)", value=float(reg["Valor Pago Equipe"]))

            e_obs = st.text_area("Observações Gerais", value=reg["Observações"])

            st.markdown("---")
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                btn_salvar_baixa = st.form_submit_button("🔄 Salvar Alterações do Evento", use_container_width=True)
            with col_btn2:
                btn_excluir_eve = st.form_submit_button("❌ Excluir Evento", use_container_width=True)

            if btn_salvar_baixa:
                forn_atualizados_list = df_forn_updated.to_dict('records') if not df_forn_updated.empty else []
                e_externo_total = float(df_forn_updated["Valor"].sum()) if not df_forn_updated.empty else 0.0
                e_desc_externo_concat = ", ".join([str(f.get("Descrição", "")) for f in forn_atualizados_list if f.get("Descrição")])

                extras_atualizados_list = df_extras_updated.to_dict('records') if not df_extras_updated.empty else []

                novos_custos = e_resolume + e_iluminacao + e_sonorizacao + e_diretor + e_logistica + e_externo_total
                
                if e_resp_imposto == "Por Conta do Cliente":
                    novo_lucro = (e_fat_bruto_calc - e_imposto_nf_calc) - e_imposto_nf_calc - novos_custos
                else:
                    novo_lucro = e_fat_bruto_calc - e_imposto_nf_calc - novos_custos

                st_rec = "Pago Total" if e_val_rec >= e_fat_bruto_calc and e_fat_bruto_calc > 0 else ("Parcial" if e_val_rec > 0 else "Pendente")
                st_pag = "Pago Total" if e_val_pago >= novos_custos and novos_custos > 0 else ("Parcial" if e_val_pago > 0 else "Pendente")

                reg_atualizado = {
                    "Cliente": e_cliente,
                    "Data Evento": e_data_evento.strftime("%d/%m/%Y"),
                    "Horário": e_horario,
                    "Data Montagem": e_data_montagem.strftime("%d/%m/%Y"),
                    "Horário Montagem": e_horario_montagem,
                    "Complexo / Local": e_complexo_local,
                    "Aprovado": e_val_aprovado,
                    "Val. Extra": e_val_extra_total,
                    "Itens Extras": extras_atualizados_list,
                    "Faturamento Bruto": e_fat_bruto_calc,
                    "10% NF": e_imposto_nf_calc,
                    "Responsável Imposto": e_resp_imposto,
                    "Custos Operacionais + Logística": novos_custos,
                    "Custo Resolume": e_resolume,
                    "Custo Iluminação": e_iluminacao,
                    "Custo Sonorização": e_sonorizacao,
                    "Custo Diretor": e_diretor,
                    "Custo Logística": e_logistica,
                    "Custo Fornecedor Externo": e_externo_total,
                    "Desc. Fornecedor Externo": e_desc_externo_concat,
                    "Fornecedores Externos": forn_atualizados_list,
                    "Valor Recebido Cliente": e_val_rec,
                    "Valor Pago Equipe": e_val_pago,
                    "Status Recebimento": st_rec,
                    "Status Pagamento": st_pag,
                    "Lucro Real": novo_lucro,
                    "Lucro Miguel Araújo": novo_lucro * 0.50,
                    "Lucro Antonio Carlos": novo_lucro * 0.50,
                    "Pag. Operacional": reg["Pag. Operacional"],
                    "Rec. Champions": reg["Rec. Champions"],
                    "Equipamentos": e_equipamentos if e_equipamentos else "Não especificado",
                    "Equipe Técnica": e_equipe_tecnica if e_equipe_tecnica else "Não especificado",
                    "Observações": e_obs if e_obs else "Nenhuma observação."
                }
                atualizar_evento_db(reg['id'], reg_atualizado)
                st.success("✅ Evento atualizado com sucesso!")
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
                "id", "Cliente", "Data Evento", "Complexo / Local", "Aprovado", "Val. Extra", "Responsável Imposto", "Faturamento Bruto", "Valor Recebido Cliente", "Falta Receber (Cliente)",
                "Custos Operacionais + Logística", "Desc. Fornecedor Externo", "Custo Fornecedor Externo", "Valor Pago Equipe", "Falta Pagar (Equipe/Ext)", "Lucro Real",
                "Lucro Miguel Araújo", "Lucro Antonio Carlos"
            ]],
            use_container_width=True
        )
