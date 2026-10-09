import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import json
import urllib.parse
from supabase import create_client, Client

# ReportLab para geração de PDFs
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- CONFIGURAÇÃO E PERSISTÊNCIA VIA SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error("⚠️ Erro de conexão com o Supabase. Verifique se configurou as chaves nos Secrets do Streamlit Cloud.")
    st.stop()

def parse_json_safely(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    try:
        data = json.loads(val)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []

def carregar_eventos():
    try:
        response = supabase.table("eventos").select("*").order("id", desc=True).execute()
        rows = response.data or []
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        rows = []

    eventos = []
    for d in rows:
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

        reembolsos_list = parse_json_safely(d.get("reembolsos"))
        custo_reembolsos_total = sum(to_float(r.get("Valor", 0.0)) for r in reembolsos_list)
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
            "Desc. Fornecedor Externo": ", ".join([str(f.get("Descrição", "")) for f in forn_ext_list]),
            "Reembolsos": reembolsos_list,
            "Custo Reembolsos": custo_reembolsos_total,
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
    payload = {
        "cliente": reg["Cliente"],
        "data_evento": reg["Data Evento"],
        "horario": reg["Horário"],
        "data_montagem": reg["Data Montagem"],
        "horario_montagem": reg["Horário Montagem"],
        "complexo": reg["Complexo / Local"],
        "aprovado": reg["Aprovado"],
        "val_extra": reg["Val. Extra"],
        "itens_extras": reg["Itens Extras"],
        "faturamento_bruto": reg["Faturamento Bruto"],
        "imposto_nf": reg["10% NF"],
        "responsavel_imposto": reg["Responsável Imposto"],
        "custos_total": reg["Custos Operacionais + Logística"],
        "custo_resolume": reg["Custo Resolume"],
        "custo_iluminacao": reg["Custo Iluminação"],
        "custo_sonorizacao": reg["Custo Sonorização"],
        "custo_diretor": reg["Custo Diretor"],
        "custo_logistica": reg["Custo Logística"],
        "custo_fornecedor_externo": reg["Custo Fornecedor Externo"],
        "desc_fornecedor_externo": reg["Desc. Fornecedor Externo"],
        "fornecedores_externos": reg["Fornecedores Externos"],
        "reembolsos": reg["Reembolsos"],
        "custo_reembolsos": reg["Custo Reembolsos"],
        "val_recebido_cliente": reg["Valor Recebido Cliente"],
        "val_pago_equipe": reg["Valor Pago Equipe"],
        "status_recebimento": reg["Status Recebimento"],
        "status_pagamento": reg["Status Pagamento"],
        "lucro_real": reg["Lucro Real"],
        "lucro_miguel": reg["Lucro Miguel Araújo"],
        "lucro_antonio": reg["Lucro Antonio Carlos"],
        "pag_operacional": reg["Pag. Operacional"],
        "rec_champions": reg["Rec. Champions"],
        "equipamentos": reg["Equipamentos"],
        "equipe_tecnica": reg["Equipe Técnica"],
        "observacoes": reg["Observações"]
    }
    supabase.table("eventos").insert(payload).execute()

def atualizar_evento_db(id_evento, reg):
    payload = {
        "cliente": reg["Cliente"],
        "data_evento": reg["Data Evento"],
        "horario": reg["Horário"],
        "data_montagem": reg["Data Montagem"],
        "horario_montagem": reg["Horário Montagem"],
        "complexo": reg["Complexo / Local"],
        "aprovado": reg["Aprovado"],
        "val_extra": reg["Val. Extra"],
        "itens_extras": reg["Itens Extras"],
        "faturamento_bruto": reg["Faturamento Bruto"],
        "imposto_nf": reg["10% NF"],
        "responsavel_imposto": reg["Responsável Imposto"],
        "custos_total": reg["Custos Operacionais + Logística"],
        "custo_resolume": reg["Custo Resolume"],
        "custo_iluminacao": reg["Custo Iluminação"],
        "custo_sonorizacao": reg["Custo Sonorização"],
        "custo_diretor": reg["Custo Diretor"],
        "custo_logistica": reg["Custo Logística"],
        "custo_fornecedor_externo": reg["Custo Fornecedor Externo"],
        "desc_fornecedor_externo": reg["Desc. Fornecedor Externo"],
        "fornecedores_externos": reg["Fornecedores Externos"],
        "reembolsos": reg["Reembolsos"],
        "custo_reembolsos": reg["Custo Reembolsos"],
        "val_recebido_cliente": reg["Valor Recebido Cliente"],
        "val_pago_equipe": reg["Valor Pago Equipe"],
        "status_recebimento": reg["Status Recebimento"],
        "status_pagamento": reg["Status Pagamento"],
        "lucro_real": reg["Lucro Real"],
        "lucro_miguel": reg["Lucro Miguel Araújo"],
        "lucro_antonio": reg["Lucro Antonio Carlos"],
        "pag_operacional": reg["Pag. Operacional"],
        "rec_champions": reg["Rec. Champions"],
        "equipamentos": reg["Equipamentos"],
        "equipe_tecnica": reg["Equipe Técnica"],
        "observacoes": reg["Observações"]
    }
    supabase.table("eventos").update(payload).eq("id", id_evento).execute()

def deletar_evento_db(id_evento):
    supabase.table("eventos").delete().eq("id", id_evento).execute()

def gerar_excel_backup(eventos):
    df_export = pd.DataFrame(eventos)
    df_export["Itens Extras (Texto)"] = df_export["Itens Extras"].apply(lambda x: json.dumps(x, ensure_ascii=False))
    df_export["Fornecedores Externos (Texto)"] = df_export["Fornecedores Externos"].apply(lambda x: json.dumps(x, ensure_ascii=False))
    df_export["Reembolsos (Texto)"] = df_export["Reembolsos"].apply(lambda x: json.dumps(x, ensure_ascii=False))
    
    cols_drop = ["Itens Extras", "Fornecedores Externos", "Reembolsos"]
    df_export_clean = df_export.drop(columns=[c for c in cols_drop if c in df_export.columns])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export_clean.to_excel(writer, index=False, sheet_name='Eventos_Backup')
    output.seek(0)
    return output

# GERADOR DE RECIBO DE PAGAMENTO / CACHÊ / REEMBOLSO
def gerar_pdf_recibo(favorecido, valor, servico_desc, cliente, data_evento):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('RTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=16, textColor=colors.HexColor("#2A201C"), alignment=1)
    body_style = ParagraphStyle('RBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor("#1A1412"), leading=14)
    
    if os.path.exists("logo.jpg"):
        story.append(RLImage("logo.jpg", width=500, height=110))
        story.append(Spacer(1, 15))
    elif os.path.exists("logo.png"):
        story.append(RLImage("logo.png", width=500, height=110))
        story.append(Spacer(1, 15))
        
    story.append(Paragraph("<b>RECIBO DE PAGAMENTO / RESSARCIMENTO</b>", title_style))
    story.append(Spacer(1, 20))
    
    val_box = Table([[Paragraph(f"<b>VALOR TOTAL: R$ {valor:,.2f}</b>", ParagraphStyle('VBox', parent=title_style, fontSize=14, textColor=colors.HexColor("#FFD700")))]], colWidths=[520])
    val_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 10), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(val_box)
    story.append(Spacer(1, 20))
    
    texto_recibo = f"""
    Recebi(emos) de <b>MIGUEL ARAÚJO PRODUÇÕES</b> a quantia de <b>R$ {valor:,.2f}</b>, referente ao pagamento por serviços prestados ou reembolso de despesas operacionais referentes ao evento do cliente <b>{cliente}</b> realizado na data de <b>{data_evento}</b>.
    <br/><br/>
    <b>Descrição dos Serviços / Reembolso:</b><br/>
    {servico_desc}
    """
    story.append(Paragraph(texto_recibo, body_style))
    story.append(Spacer(1, 40))
    
    data_atual = datetime.now().strftime("%d de %B de %Y")
    story.append(Paragraph(f"São Paulo, {data_atual}.", body_style))
    story.append(Spacer(1, 50))
    
    t_ass = Table([
        [Paragraph("__________________________________________", body_style), Paragraph("__________________________________________", body_style)],
        [Paragraph(f"<b>{favorecido}</b><br/>Favorecido / Recebedor", body_style), Paragraph("<b>MIGUEL ARAÚJO PRODUÇÕES</b><br/>Emissor / Aprovador", body_style)]
    ], colWidths=[260, 260])
    t_ass.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_ass)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# GERADOR DE PDF DUAL DE ORÇAMENTO E CONTROLE
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

    if os.path.exists("logo.jpg"):
        story.append(RLImage("logo.jpg", width=560, height=130))
        story.append(Spacer(1, 10))
    elif os.path.exists("logo.png"):
        story.append(RLImage("logo.png", width=560, height=130))
        story.append(Spacer(1, 10))

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

    sec2_hdr = Table([[Paragraph("🛠️ SETOR DE ENGENHARIA DE ÁUDIO, LUZ, VÍDEO & ESTRUTURA", sec_title_style)]], colWidths=[560])
    sec2_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
    story.append(sec2_hdr)
    t2 = Table([[Paragraph("ITEM / ATIVO TÉCNICO CONTRATADO", th_style), Paragraph("STATUS OPERACIONAL", th_style)], [Paragraph(str(registro["Equipamentos"]).replace('\n', '<br/>'), td_style), Paragraph("INCLUSO", td_status)]], colWidths=[440, 120])
    t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")), ('PADDING', (0,0), (-1,-1), 6), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t2)
    story.append(Spacer(1, 10))

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

        reembolsos_pdf_list = registro.get("Reembolsos", [])
        if reembolsos_pdf_list:
            sec_reemb_hdr = Table([[Paragraph("💸 DESPESAS E REEMBOLSOS LANÇADOS", sec_title_style)]], colWidths=[560])
            sec_reemb_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
            story.append(sec_reemb_hdr)

            dados_reemb = [[Paragraph("FAVORECIDO", th_style), Paragraph("DESCRIÇÃO / SOBRE O QUE É", th_style), Paragraph("VALOR (R$)", th_style)]]
            for r_item in reembolsos_pdf_list:
                r_fav = r_item.get("Favorecido") or "Não informado"
                r_desc = r_item.get("Descrição") or "Reembolso Operacional"
                r_val = float(r_item.get("Valor", 0.0))
                dados_reemb.append([Paragraph(str(r_fav), td_style), Paragraph(str(r_desc), td_style), Paragraph(f"R$ {r_val:,.2f}", td_bold)])

            t_reemb = Table(dados_reemb, colWidths=[160, 260, 140])
            t_reemb.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EAE3D2")),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF6EE")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C5A059")),
                ('PADDING', (0,0), (-1,-1), 5), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            story.append(t_reemb)
            story.append(Spacer(1, 10))

        sec4_hdr = Table([[Paragraph("💰 BALANÇO FINANCEIRO & DIVISÃO DE LUCRO OPERACIONAL", sec_title_style)]], colWidths=[560])
        sec4_hdr.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#2A201C")), ('PADDING', (0,0), (-1,-1), 6)]))
        story.append(sec4_hdr)
        
        dados_sec4 = [
            [Paragraph("Faturamento Bruto:", th_style), Paragraph(f"R$ {registro['Faturamento Bruto']:,.2f}", td_bold), Paragraph(f"Imposto NF ({resp_imposto}):", th_style), Paragraph(f"R$ {registro['10% NF']:,.2f}", td_style)],
            [Paragraph("Custos Operacionais Totais:", th_style), Paragraph(f"R$ {registro['Custos Operacionais + Logística']:,.2f}", td_style), Paragraph("Total Reembolsos:", th_style), Paragraph(f"R$ {registro.get('Custo Reembolsos', 0.0):,.2f}", td_style)],
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

# --- PAINEL GERAL DE INDICADORES (FILTRO POR CLIENTE) ---
if faturamentos:
    df_kpi_raw = pd.DataFrame(faturamentos)
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

    st.markdown("---")

aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs([
    "➕ Novo Evento",
    "✏️ Baixas & Edição",
    "🗓️ Calendário",
    "🧾 Recibos de Cachê",
    "📊 Dashboards & Margens",
    "📲 WhatsApp Rápido",
    "📄 Relatórios & PDFs"
])

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

        st.markdown("### 💸 4. Reembolsos e Despesas Operacionais Extras")
        df_reemb_init = pd.DataFrame([{"Favorecido": "", "Descrição": "", "Valor": 0.0}])
        df_reemb_edit = st.data_editor(
            df_reemb_init, num_rows="dynamic", use_container_width=True,
            column_config={
                "Favorecido": st.column_config.TextColumn("Quem irá receber o reembolso?", required=True),
                "Descrição": st.column_config.TextColumn("Sobre o que se trata (Uber, Alimentação, Peça...)", required=True),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=10.0)
            }, key="editor_reembolsos_novo"
        )
        val_reembolso_total = float(df_reemb_edit["Valor"].sum()) if not df_reemb_edit.empty else 0.0

        st.markdown("### 💰 5. Faturamento & Negociação Fiscal")
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

        st.markdown("### 👥 6. Custos: Equipe Técnica, Logística & Fornecedores")
        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
        with col_c1: custo_resolume = st.number_input("Técnico Resolume (R$)", min_value=0.0, step=50.0)
        with col_c2: custo_iluminacao = st.number_input("Técnico Iluminação (R$)", min_value=0.0, step=50.0)
        with col_c3: custo_sonorizacao = st.number_input("Técnico Som (R$)", min_value=0.0, step=50.0)
        with col_c4: custo_diretor = st.number_input("Direção Técnica (R$)", min_value=0.0, step=50.0)
        with col_c5: custo_logistica = st.number_input("Logística / Frete (R$)", min_value=0.0, step=20.0)

        st.markdown("#### 🌐 Fornecedores Externos")
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

        st.markdown("### 💳 7. Status Inicial de Caixa")
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            val_recebido_init = st.number_input("Quanto o cliente JÁ PAGOU? (R$)", min_value=0.0, step=100.0, key="v_rec_init")
        with col_st2:
            val_pago_equipe_init = st.number_input("Quanto você JÁ PAGOU à equipe/fornecedores/reembolsos? (R$)", min_value=0.0, step=100.0, key="v_pag_init")

        col_d1, col_d2 = st.columns(2)
        with col_d1: dt_pag_operacional = st.date_input("Previsão Pagamento Operacional")
        with col_d2: dt_rec_champions = st.date_input("Previsão Recebimento Cliente")

        obs_gerais = st.text_area("Observações Financeiras / Gerais")

        reembolsos_novo = df_reemb_edit.to_dict('records') if not df_reemb_edit.empty else []
        total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica + custo_externo_total + val_reembolso_total
        
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
                "Reembolsos": reembolsos_novo,
                "Custo Reembolsos": val_reembolso_total,
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
            st.success("✅ Evento cadastrado com sucesso no Supabase!")
            st.rerun()

# ABA 2: EDITAR COMPLETO, REEMBOLSOS E BAIXAS
with aba2:
    st.subheader("✏️ Edição Completa, Reembolsos e Baixas")
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

            st.markdown("#### 💸 4. Reembolsos e Despesas Extras do Evento")
            reemb_existentes = reg.get("Reembolsos", [])
            df_reemb_edit_existing = pd.DataFrame(reemb_existentes if reemb_existentes else [{"Favorecido": "", "Descrição": "", "Valor": 0.0}])
            df_reemb_updated = st.data_editor(
                df_reemb_edit_existing, num_rows="dynamic", use_container_width=True,
                column_config={
                    "Favorecido": st.column_config.TextColumn("Quem irá receber o reembolso?", required=True),
                    "Descrição": st.column_config.TextColumn("Sobre o que se trata (Uber, Alimentação...)", required=True),
                    "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.0, step=10.0)
                }, key=f"editor_reemb_edit_{reg['id']}"
            )
            e_val_reemb_total = float(df_reemb_updated["Valor"].sum()) if not df_reemb_updated.empty else 0.0

            st.markdown("#### 💰 5. Faturamento & Negociação Fiscal")
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

            st.markdown("#### 👥 6. Custos: Equipe Técnica, Logística & Cachês")
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

            st.markdown("#### 💳 7. Baixas de Caixa (Pagamentos e Recebimentos)")
            c_rec1, c_rec2 = st.columns(2)
            with c_rec1:
                e_val_rec = st.number_input("Valor JÁ RECEBIDO do Cliente (R$)", value=float(reg["Valor Recebido Cliente"]))
            with c_rec2:
                e_val_pago = st.number_input("Valor JÁ PAGO à Equipe/Fornecedores/Reembolsos (R$)", value=float(reg["Valor Pago Equipe"]))

            e_obs = st.text_area("Observações Gerais", value=reg["Observações"])

            st.markdown("---")
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                btn_salvar_baixa = st.form_submit_button("🔄 Salvar Alterações no Supabase", use_container_width=True)
            with col_btn2:
                btn_excluir_eve = st.form_submit_button("❌ Excluir Evento", use_container_width=True)

            if btn_salvar_baixa:
                forn_atualizados_list = df_forn_updated.to_dict('records') if not df_forn_updated.empty else []
                e_externo_total = float(df_forn_updated["Valor"].sum()) if not df_forn_updated.empty else 0.0
                e_desc_externo_concat = ", ".join([str(f.get("Descrição", "")) for f in forn_atualizados_list if f.get("Descrição")])

                extras_atualizados_list = df_extras_updated.to_dict('records') if not df_extras_updated.empty else []
                reemb_atualizados_list = df_reemb_updated.to_dict('records') if not df_reemb_updated.empty else []

                novos_custos = e_resolume + e_iluminacao + e_sonorizacao + e_diretor + e_logistica + e_externo_total + e_val_reemb_total
                
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
                    "Reembolsos": reemb_atualizados_list,
                    "Custo Reembolsos": e_val_reemb_total,
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
                st.success("✅ Evento atualizado com sucesso no Supabase!")
                st.rerun()

            if btn_excluir_eve:
                deletar_evento_db(reg['id'])
                st.warning("🗑️ Evento excluído do Supabase!")
                st.rerun()

# ABA 3: CALENDÁRIO OPERACIONAL & CRONOGRAMA
with aba3:
    st.subheader("🗓️ Calendário Operacional & Cronograma de Produção")
    if not faturamentos:
        st.info("Nenhum evento registrado no banco de dados.")
    else:
        df_cal = pd.DataFrame(faturamentos)
        st.markdown("### 📋 Cronograma de Montagens e Eventos")
        
        df_cal_display = df_cal[["Data Montagem", "Horário Montagem", "Data Evento", "Horário", "Cliente", "Complexo / Local", "Equipe Técnica"]].copy()
        df_cal_display.sort_values(by="Data Evento", ascending=True, inplace=True)
        
        st.dataframe(df_cal_display, use_container_width=True)

# ABA 4: GERADOR DE RECIBOS DE CACHÊ / REEMBOLSO
with aba4:
    st.subheader("🧾 Gerador Automático de Recibos de Cachê e Reembolsos")
    if not faturamentos:
        st.info("Nenhum evento cadastrado para emissão de recibos.")
    else:
        idx_rec_evt = st.selectbox(
            "Selecione o Evento referente ao Recibo:", range(len(faturamentos)),
            format_func=lambda x: f"{faturamentos[x]['Cliente']} - {faturamentos[x]['Data Evento']}"
        )
        evt_rec = faturamentos[idx_rec_evt]
        
        st.markdown(f"#### Emissão para o Evento: **{evt_rec['Cliente']}** ({evt_rec['Data Evento']})")
        
        rec_col1, rec_col2 = st.columns(2)
        with rec_col1:
            rec_favorecido = st.text_input("Nome do Favorecido / Técnico / Fornecedor", placeholder="Ex: João Silva")
            rec_valor = st.number_input("Valor do Recibo (R$)", min_value=0.0, step=50.0)
        with rec_col2:
            rec_descricao = st.text_area("Descrição do Serviço ou Reembolso", value="Diária de Técnico de Resolume / Engenharia de Vídeo")

        if st.button("📄 Gerar Recibo em PDF", use_container_width=True):
            if not rec_favorecido or rec_valor <= 0:
                st.error("Por favor, preencha o nome do favorecido e um valor válido.")
            else:
                pdf_rec_bytes = gerar_pdf_recibo(rec_favorecido, rec_valor, rec_descricao, evt_rec['Cliente'], evt_rec['Data Evento'])
                st.download_button(
                    f"📥 Baixar Recibo - {rec_favorecido}",
                    data=pdf_rec_bytes,
                    file_name=f"Recibo_{rec_favorecido.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# ABA 5: DASHBOARD DE MARGENS E DESEMPENHO POR CLIENTE
with aba5:
    st.subheader("📊 Dashboards de Lucratividade e Margens por Cliente")
    if not faturamentos:
        st.info("Nenhum dado financeiro registrado para gráficos.")
    else:
        df_dash = pd.DataFrame(faturamentos)
        
        st.markdown("### 📈 Desempenho Financeiro por Cliente")
        df_dash_grp = df_dash.groupby("Cliente")[["Faturamento Bruto", "Custos Operacionais + Logística", "Lucro Real"]].sum()
        st.bar_chart(df_dash_grp)

        st.markdown("### 🥧 Distribuição do Faturamento por Cliente")
        df_pie = df_dash.groupby("Cliente")["Faturamento Bruto"].sum()
        st.dataframe(df_pie)

# ABA 6: ATENDIMENTO / WHATSAPP RÁPIDO
with aba6:
    st.subheader("📲 Atendimento & Envio Rápido via WhatsApp")
    if not faturamentos:
        st.info("Nenhum evento registrado para envio.")
    else:
        idx_wsp = st.selectbox(
            "Selecione o Evento para enviar o resumo ao cliente:", range(len(faturamentos)),
            format_func=lambda x: f"{faturamentos[x]['Cliente']} - {faturamentos[x]['Data Evento']}"
        )
        evt_wsp = faturamentos[idx_wsp]
        
        wsp_num = st.text_input("Número do WhatsApp (com DDD)", placeholder="Ex: 11999998888")
        
        msg_padrao = f"""Olá! Segue o resumo comercial do evento para *{evt_wsp['Cliente']}*:

📅 *Data do Evento:* {evt_wsp['Data Evento']} ({evt_wsp['Horário']})
📍 *Local:* {evt_wsp['Complexo / Local']}
💵 *Valor Global:* R$ {evt_wsp['Faturamento Bruto']:,.2f}

Permanecemos à disposição!
*Miguel Araújo Produções*"""

        msg_editada = st.text_area("Mensagem Formatada:", value=msg_padrao, height=180)
        
        if wsp_num:
            num_clean = "".join(filter(str.isdigit, wsp_num))
            msg_encoded = urllib.parse.quote(msg_editada)
            wsp_link = f"https://api.whatsapp.com/send?phone=55{num_clean}&text={msg_encoded}"
            st.markdown(f'<a href="{wsp_link}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; font-weight:bold; padding:10px 20px; border:none; border-radius:8px; cursor:pointer; width:100%;">💬 Abrir no WhatsApp Web</button></a>', unsafe_allow_html=True)

# ABA 7: TABELA DETALHADA, RELATÓRIOS E BACKUPS EXCEL
with aba7:
    st.subheader("📄 Emissão de Documentos e PDFs de Orçamento")
    if faturamentos:
        col_sel, col_btn1, col_btn2 = st.columns([2, 1, 1])
        with col_sel:
            evento_idx_pdf = st.selectbox(
                "Selecione o Evento para gerar o PDF Comercial/Interno:", range(len(faturamentos)),
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
        st.subheader("💾 Backup de Dados em Excel / CSV")
        col_bkp1, col_bkp2 = st.columns(2)
        with col_bkp1:
            excel_bytes = gerar_excel_backup(faturamentos)
            st.download_button(
                "📥 Baixar Backup Completo em Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"Backup_Eventos_Financeiro_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_bkp2:
            df_csv = pd.DataFrame(faturamentos)
            csv_data = df_csv.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📄 Baixar Backup em CSV",
                data=csv_data,
                file_name=f"Backup_Eventos_{datetime.now().strftime('%d_%m_%Y')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("---")
        st.subheader("📋 Relatório Geral Financeiro Consolidado")
        
        df_full = pd.DataFrame(faturamentos)
        df_full["Falta Receber (Cliente)"] = df_full["Faturamento Bruto"] - df_full["Valor Recebido Cliente"]
        df_full["Falta Pagar (Equipe/Ext)"] = df_full["Custos Operacionais + Logística"] - df_full["Valor Pago Equipe"]

        st.dataframe(
            df_full[[
                "id", "Cliente", "Data Evento", "Complexo / Local", "Aprovado", "Val. Extra", "Custo Reembolsos", "Responsável Imposto", "Faturamento Bruto", "Valor Recebido Cliente", "Falta Receber (Cliente)",
                "Custos Operacionais + Logística", "Desc. Fornecedor Externo", "Custo Fornecedor Externo", "Valor Pago Equipe", "Falta Pagar (Equipe/Ext)", "Lucro Real",
                "Lucro Miguel Araújo", "Lucro Antonio Carlos"
            ]],
            use_container_width=True
        )
