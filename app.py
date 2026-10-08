import sqlite3
import urllib.parse
from io import BytesIO
from datetime import datetime
import pandas as pd
import streamlit as st

# ReportLab para geração de PDFs
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Eventos & AV",
    page_icon="🎬",
    layout="wide"
)

# ---------------------------------------------------------
# 2. BANCO DE DADOS LOCAL (SQLite)
# ---------------------------------------------------------
DB_NAME = "eventos_gestao.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            data_evento TEXT,
            horario TEXT,
            data_montagem TEXT,
            horario_montagem TEXT,
            complexo_local TEXT,
            aprovado REAL,
            val_extra REAL,
            faturamento_bruto REAL,
            imposto_nf REAL,
            resp_imposto TEXT,
            custos_operacionais REAL,
            custo_resolume REAL,
            custo_iluminacao REAL,
            custo_sonorizacao REAL,
            custo_diretor REAL,
            custo_logistica REAL,
            val_recebido REAL,
            val_pago_equipe REAL,
            status_recebimento TEXT,
            status_pagamento TEXT,
            lucro_real REAL,
            lucro_miguel REAL,
            lucro_antonio REAL,
            equipamentos TEXT,
            equipe_tecnica TEXT,
            observacoes TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def carregar_eventos_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eventos ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    eventos = []
    for r in rows:
        eventos.append({
            "id": r[0],
            "Cliente": r[1] or "",
            "Data Evento": r[2] or "",
            "Horário": r[3] or "",
            "Data Montagem": r[4] or "",
            "Horário Montagem": r[5] or "",
            "Complexo / Local": r[6] or "",
            "Aprovado": r[7] or 0.0,
            "Val. Extra": r[8] or 0.0,
            "Faturamento Bruto": r[9] or 0.0,
            "10% NF": r[10] or 0.0,
            "Responsável Imposto": r[11] or "Incluso no Valor",
            "Custos Operacionais + Logística": r[12] or 0.0,
            "Custo Resolume": r[13] or 0.0,
            "Custo Iluminação": r[14] or 0.0,
            "Custo Sonorização": r[15] or 0.0,
            "Custo Diretor": r[16] or 0.0,
            "Custo Logística": r[17] or 0.0,
            "Valor Recebido Cliente": r[18] or 0.0,
            "Valor Pago Equipe": r[19] or 0.0,
            "Status Recebimento": r[20] or "Pendente",
            "Status Pagamento": r[21] or "Pendente",
            "Lucro Real": r[22] or 0.0,
            "Lucro Miguel Araújo": r[23] or 0.0,
            "Lucro Antonio Carlos": r[24] or 0.0,
            "Equipamentos": r[25] or "",
            "Equipe Técnica": r[26] or "",
            "Observações": r[27] or ""
        })
    return eventos

def salvar_evento_db(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO eventos (
            cliente, data_evento, horario, data_montagem, horario_montagem,
            complexo_local, aprovado, val_extra, faturamento_bruto, imposto_nf,
            resp_imposto, custos_operacionais, custo_resolume, custo_iluminacao,
            custo_sonorizacao, custo_diretor, custo_logistica, val_recebido,
            val_pago_equipe, status_recebimento, status_pagamento, lucro_real,
            lucro_miguel, lucro_antonio, equipamentos, equipe_tecnica, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["Cliente"], data["Data Evento"], data["Horário"], data["Data Montagem"], data["Horário Montagem"],
        data["Complexo / Local"], data["Aprovado"], data["Val. Extra"], data["Faturamento Bruto"], data["10% NF"],
        data["Responsável Imposto"], data["Custos Operacionais + Logística"], data["Custo Resolume"], data["Custo Iluminação"],
        data["Custo Sonorização"], data["Custo Diretor"], data["Custo Logística"], data["Valor Recebido Cliente"],
        data["Valor Pago Equipe"], data["Status Recebimento"], data["Status Pagamento"], data["Lucro Real"],
        data["Lucro Miguel Araújo"], data["Lucro Antonio Carlos"], data["Equipamentos"], data["Equipe Técnica"], data["Observações"]
    ))
    conn.commit()
    conn.close()

def atualizar_evento_db(ev_id, data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE eventos SET
            cliente=?, data_evento=?, horario=?, data_montagem=?, horario_montagem=?,
            complexo_local=?, aprovado=?, val_extra=?, faturamento_bruto=?, imposto_nf=?,
            resp_imposto=?, custos_operacionais=?, custo_resolume=?, custo_iluminacao=?,
            custo_sonorizacao=?, custo_diretor=?, custo_logistica=?, val_recebido=?,
            val_pago_equipe=?, status_recebimento=?, status_pagamento=?, lucro_real=?,
            lucro_miguel=?, lucro_antonio=?, equipamentos=?, equipe_tecnica=?, observacoes=?
        WHERE id=?
    """, (
        data["Cliente"], data["Data Evento"], data["Horário"], data["Data Montagem"], data["Horário Montagem"],
        data["Complexo / Local"], data["Aprovado"], data["Val. Extra"], data["Faturamento Bruto"], data["10% NF"],
        data["Responsável Imposto"], data["Custos Operacionais + Logística"], data["Custo Resolume"], data["Custo Iluminação"],
        data["Custo Sonorização"], data["Custo Diretor"], data["Custo Logística"], data["Valor Recebido Cliente"],
        data["Valor Pago Equipe"], data["Status Recebimento"], data["Status Pagamento"], data["Lucro Real"],
        data["Lucro Miguel Araújo"], data["Lucro Antonio Carlos"], data["Equipamentos"], data["Equipe Técnica"], data["Observações"],
        ev_id
    ))
    conn.commit()
    conn.close()

def deletar_evento_db(ev_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eventos WHERE id=?", (ev_id,))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# 3. GERADORES DE PDF (ReportLab)
# ---------------------------------------------------------
def gerar_pdf_evento(evento, tipo_documento="ORCAMENTO"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1E293B'), spaceAfter=12)
    normal_style = styles['Normal']

    titulo_doc = "ORÇAMENTO COMERCIAL - AV & PRODUÇÃO" if tipo_documento == "ORCAMENTO" else "RELATÓRIO FINANCEIRO INTERNO"
    elements.append(Paragraph(f"<b>{titulo_doc}</b>", title_style))
    elements.append(Paragraph(f"<b>Cliente / Evento:</b> {evento['Cliente']}", normal_style))
    elements.append(Paragraph(f"<b>Data do Evento:</b> {evento['Data Evento']} ({evento['Horário']})", normal_style))
    elements.append(Paragraph(f"<b>Local:</b> {evento['Complexo / Local']}", normal_style))
    elements.append(Spacer(1, 12))

    if tipo_documento == "ORCAMENTO":
        table_data = [
            ["Item / Descrição", "Valor"],
            ["Escopo Base Aprovado", f"R$ {evento['Aprovado']:,.2f}"],
            ["Serviços / Itens Extras", f"R$ {evento['Val. Extra']:,.2f}"],
            ["Imposto (10% NF)", f"R$ {evento['10% NF']:,.2f} ({evento['Responsável Imposto']})"],
            ["VALOR TOTAL", f"R$ {evento['Faturamento Bruto']:,.2f}"]
        ]
    else:
        table_data = [
            ["Métrica Financeira", "Valor (R$)"],
            ["Faturamento Bruto", f"R$ {evento['Faturamento Bruto']:,.2f}"],
            ["(-) Custos Operacionais Totais", f"R$ {evento['Custos Operacionais + Logística']:,.2f}"],
            ["= LUCRO REAL LÍQUIDO", f"R$ {evento['Lucro Real']:,.2f}"],
            ["Divisão Miguel Araújo (50%)", f"R$ {evento['Lucro Miguel Araújo']:,.2f}"],
            ["Divisão Antonio Carlos (50%)", f"R$ {evento['Lucro Antonio Carlos']:,.2f}"]
        ]

    t = Table(table_data, colWidths=[3.5 * inch, 3.5 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    if evento.get('Equipamentos'):
        elements.append(Paragraph("<b>Equipamentos Alocados:</b>", styles['Heading3']))
        elements.append(Paragraph(evento['Equipamentos'].replace('\n', '<br/>'), normal_style))
        elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_recibo(favorecido, valor, descricao, cliente, data_ev):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('ReciboTitle', parent=styles['Heading1'], fontSize=20, alignment=1, spaceAfter=20)
    
    elements.append(Paragraph("<b>RECIBO DE PAGAMENTO</b>", title_style))
    elements.append(Spacer(1, 10))
    
    texto_recibo = f"""
    Recebi(emos) de <b>MIGUEL ARAÚJO PRODUÇÕES / EVENTOS</b> a quantia de <b>R$ {valor:,.2f}</b>, 
    referente a: <i>{descricao}</i> para o evento <b>{cliente}</b> realizado na data <b>{data_ev}</b>.
    <br/><br/>
    Por ser verdade, firmo(amos) o presente recibo dando plena e geral quitação.
    """
    elements.append(Paragraph(texto_recibo, styles['Normal']))
    elements.append(Spacer(1, 40))
    
    elements.append(Paragraph(f"Data de emissão: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 40))
    
    linha_ass = "_" * 40
    elements.append(Paragraph(f"{linha_ass}<br/><b>{favorecido}</b>", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_excel_backup(faturamentos):
    df = pd.DataFrame(faturamentos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Eventos', index=False)
    output.seek(0)
    return output.getvalue()

# ---------------------------------------------------------
# 4. INTERFACE PRINCIPAL & PAINEL DE CONTROLE
# ---------------------------------------------------------
st.title("🎬 Painel de Gestão Operacional & Financeira - AV Events")

faturamentos = carregar_eventos_db()
df_kpi_raw = pd.DataFrame(faturamentos)

if df_kpi_raw.empty:
    opcoes_filtro_cliente = ["Todos os Clientes (Consolidado Geral)"]
else:
    opcoes_filtro_cliente = ["Todos os Clientes (Consolidado Geral)"] + sorted(list(df_kpi_raw["Cliente"].unique()))

# --- FILTRO POR CLIENTE PARA OS KPIS ---
cliente_selecionado = st.selectbox("🔍 Filtrar Painel Geral por Cliente:", opcoes_filtro_cliente)

if not df_kpi_raw.empty:
    if cliente_selecionado != "Todos os Clientes (Consolidado Geral)":
        df_kpi = df_kpi_raw[df_kpi_raw["Cliente"] == cliente_selecionado]
    else:
        df_kpi = df_kpi_raw.copy()

    total_faturamento = df_kpi["Faturamento Bruto"].sum()
    total_custos = df_kpi["Custos Operacionais + Logística"].sum()
    total_lucro = df_kpi["Lucro Real"].sum()
    total_recebido = df_kpi["Valor Recebido Cliente"].sum()
    total_pago_equipe = df_kpi["Valor Pago Equipe"].sum()
else:
    total_faturamento = total_custos = total_lucro = total_recebido = total_pago_equipe = 0.0

st.markdown("### 📊 Indicadores Financeiros Consolidados")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Faturamento Bruto", f"R$ {total_faturamento:,.2f}")
c2.metric("Custos Totais", f"R$ {total_custos:,.2f}")
c3.metric("Lucro Real Líquido", f"R$ {total_lucro:,.2f}")
c4.metric("Recebido do Cliente", f"R$ {total_recebido:,.2f}")
c5.metric("Pago à Equipe / Forn.", f"R$ {total_pago_equipe:,.2f}")

st.markdown("---")

# --- ABAS DE NAVEGAÇÃO ---
tab_eventos, tab_novo, tab_recibo, tab_backup = st.tabs([
    "📅 Eventos e Fechamento", 
    "➕ Novo Evento / Edição", 
    "📄 Gerar Recibo Avulso", 
    "💾 Exportar Backup (Excel)"
])

# ---------------------------------------------------------
# ABA 1: LISTAGEM E AÇÕES DOS EVENTOS
# ---------------------------------------------------------
with tab_eventos:
    st.subheader("📋 Lista de Eventos Registrados")
    
    if not faturamentos:
        st.info("Nenhum evento cadastrado no momento. Acesse a aba **'Novo Evento / Edição'** para começar.")
    else:
        for ev in faturamentos:
            ev_id = ev["id"]
            titulo_expander = f"🔹 {ev['Cliente']} | Data: {ev['Data Evento']} | Bruto: R$ {ev['Faturamento Bruto']:,.2f} | Lucro: R$ {ev['Lucro Real']:,.2f}"
            
            with st.expander(titulo_expander):
                col_info1, col_info2, col_info3 = st.columns(3)
                
                with col_info1:
                    st.write(f"**Cliente:** {ev['Cliente']}")
                    st.write(f"**Data do Evento:** {ev['Data Evento']} ({ev['Horário']})")
                    st.write(f"**Montagem:** {ev['Data Montagem']} {ev['Horário Montagem']}")
                    st.write(f"**Local:** {ev['Complexo / Local']}")
                
                with col_info2:
                    st.write(f"**Escopo Base:** R$ {ev['Aprovado']:,.2f}")
                    st.write(f"**Extras Totais:** R$ {ev['Val. Extra']:,.2f}")
                    st.write(f"**Imposto NF (10%):** R$ {ev['10% NF']:,.2f} ({ev['Responsável Imposto']})")
                    st.write(f"**Custos Operacionais:** R$ {ev['Custos Operacionais + Logística']:,.2f}")
                
                with col_info3:
                    st.write(f"**Status Recebimento:** `{ev['Status Recebimento']}`")
                    st.write(f"**Status Pagamento:** `{ev['Status Pagamento']}`")
                    st.write(f"**Parte Miguel (50%):** R$ {ev['Lucro Miguel Araújo']:,.2f}")
                    st.write(f"**Parte Antonio (50%):** R$ {ev['Lucro Antonio Carlos']:,.2f}")

                st.markdown("---")
                st.markdown("**🛠️ Equipamentos:**")
                st.text(ev['Equipamentos'] if ev['Equipamentos'] else "Nenhum informado")

                st.markdown("**👥 Equipe Técnica:**")
                st.text(ev['Equipe Técnica'] if ev['Equipe Técnica'] else "Nenhuma informada")

                st.markdown("---")
                
                # --- BOTÕES DE GERAÇÃO DE DOCUMENTOS E AÇÕES ---
                col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                
                with col_b1:
                    pdf_orc = gerar_pdf_evento(ev, tipo_documento="ORCAMENTO")
                    st.download_button(
                        label="📄 PDF Orçamento Comercial",
                        data=pdf_orc,
                        file_name=f"Orcamento_{ev['Cliente'].replace(' ', '_')}_{ev['id']}.pdf",
                        mime="application/pdf",
                        key=f"btn_orc_{ev_id}"
                    )
                
                with col_b2:
                    pdf_fin = gerar_pdf_evento(ev, tipo_documento="FINANCEIRO")
                    st.download_button(
                        label="📊 PDF Controle Interno",
                        data=pdf_fin,
                        file_name=f"Financeiro_{ev['Cliente'].replace(' ', '_')}_{ev['id']}.pdf",
                        mime="application/pdf",
                        key=f"btn_fin_{ev_id}"
                    )
                
                with col_b3:
                    msg_wsp = f"*MIGUEL ARAÚJO PRODUÇÕES*\n\n" \
                              f"📌 *Evento:* {ev['Cliente']}\n" \
                              f"📅 *Data:* {ev['Data Evento']}\n" \
                              f"📍 *Local:* {ev['Complexo / Local']}\n\n" \
                              f"💰 *Faturamento Bruto:* R$ {ev['Faturamento Bruto']:,.2f}\n" \
                              f"📉 *Custos Operacionais:* R$ {ev['Custos Operacionais + Logística']:,.2f}\n" \
                              f"💵 *Lucro Real Líquido:* R$ {ev['Lucro Real']:,.2f}\n\n" \
                              f"• Miguel (50%): R$ {ev['Lucro Miguel Araújo']:,.2f}\n" \
                              f"• Antonio (50%): R$ {ev['Lucro Antonio Carlos']:,.2f}"
                    
                    url_wsp = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_wsp)}"
                    st.markdown(f"[📲 Enviar Resumo WhatsApp]({url_wsp})", unsafe_allow_html=True)
                
                with col_b4:
                    if st.button("🗑️ Deletar Evento", key=f"btn_del_{ev_id}"):
                        deletar_evento_db(ev_id)
                        st.success("Evento removido com sucesso!")
                        st.rerun()

# ---------------------------------------------------------
# ABA 2: FORMULÁRIO DE CADASTRO / EDIÇÃO
# ---------------------------------------------------------
with tab_novo:
    st.subheader("➕ Cadastrar ou Atualizar Evento")
    
    opcoes_edicao = ["-- Criar Novo Evento --"] + [f"ID {ev['id']} - {ev['Cliente']} ({ev['Data Evento']})" for ev in faturamentos]
    selecao_edit = st.selectbox("Selecione um evento existente para editar (ou crie um novo):", opcoes_edicao)
    
    dados_ev = {}
    if selecao_edit != "-- Criar Novo Evento --":
        ev_id_edit = int(selecao_edit.split(" - ")[0].replace("ID ", ""))
        dados_ev = next((item for item in faturamentos if item["id"] == ev_id_edit), {})

    with st.form("form_evento"):
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            cliente = st.text_input("Nome do Cliente / Empresa *", value=dados_ev.get("Cliente", ""))
            data_evento = st.text_input("Data do Evento *", value=dados_ev.get("Data Evento", ""))
            horario = st.text_input("Horário do Evento", value=dados_ev.get("Horário", ""))
            complexo = st.text_input("Local / Espaço / Complexo", value=dados_ev.get("Complexo / Local", ""))
        
        with c_f2:
            data_montagem = st.text_input("Data de Montagem", value=dados_ev.get("Data Montagem", ""))
            horario_montagem = st.text_input("Horário de Montagem", value=dados_ev.get("Horário Montagem", ""))
            status_rec = st.selectbox("Status Recebimento Cliente", ["Pendente", "Parcial", "Concluído"], index=["Pendente", "Parcial", "Concluído"].index(dados_ev.get("Status Recebimento", "Pendente")))
            status_pag = st.selectbox("Status Pagamento Equipe", ["Pendente", "Parcial", "Concluído"], index=["Pendente", "Parcial", "Concluído"].index(dados_ev.get("Status Pagamento", "Pendente")))

        st.markdown("---")
        st.markdown("### 💰 Valores & Financeiro")
        
        c_v1, c_v2, c_v3 = st.columns(3)
        with c_v1:
            aprovado = st.number_input("Valor Base Aprovado (R$)", value=float(dados_ev.get("Aprovado", 0.0)), step=100.0)
            val_extra = st.number_input("Soma de Extras (R$)", value=float(dados_ev.get("Val. Extra", 0.0)), step=50.0)
            val_recebido = st.number_input("Valor Recebido do Cliente (R$)", value=float(dados_ev.get("Valor Recebido Cliente", 0.0)), step=100.0)
            
        with c_v2:
            resp_imposto = st.selectbox("Responsável pelo Imposto (10% NF)", ["Incluso no Valor", "Por Conta do Cliente", "Isento / Sem NF"], index=["Incluso no Valor", "Por Conta do Cliente", "Isento / Sem NF"].index(dados_ev.get("Responsável Imposto", "Incluso no Valor")))
            if resp_imposto in ["Por Conta do Cliente", "Incluso no Valor"]:
                imposto_calculated = (aprovado + val_extra) * 0.10
            else:
                imposto_calculated = 0.0
                
            st.info(f"Imposto Estimado (10%): R$ {imposto_calculated:,.2f}")
            val_pago_equipe = st.number_input("Valor Pago à Equipe (R$)", value=float(dados_ev.get("Valor Pago Equipe", 0.0)), step=100.0)

        with c_v3:
            custo_resolume = st.number_input("Custo Resolume (R$)", value=float(dados_ev.get("Custo Resolume", 0.0)), step=50.0)
            custo_iluminacao = st.number_input("Custo Iluminação (R$)", value=float(dados_ev.get("Custo Iluminação", 0.0)), step=50.0)
            custo_sonorizacao = st.number_input("Custo Sonorização (R$)", value=float(dados_ev.get("Custo Sonorização", 0.0)), step=50.0)
            custo_diretor = st.number_input("Custo Direção / Produção (R$)", value=float(dados_ev.get("Custo Diretor", 0.0)), step=50.0)
            custo_logistica = st.number_input("Custo Logística / Frete (R$)", value=float(dados_ev.get("Custo Logística", 0.0)), step=50.0)

        st.markdown("---")
        st.markdown("### 🛠️ Equipamentos & Equipe Técnica")
        equipamentos = st.text_area("Lista de Equipamentos e Ativos Alocados", value=dados_ev.get("Equipamentos", ""), height=100)
        equipe_tecnica = st.text_area("Escala de Profissionais e Cachês", value=dados_ev.get("Equipe Técnica", ""), height=100)
        observacoes = st.text_area("Observações Internas", value=dados_ev.get("Observações", ""), height=80)

        btn_salvar = st.form_submit_button("💾 Salvar Evento no Banco de Dados")

        if btn_salvar:
            if not cliente or not data_evento:
                st.error("Por favor, preencha pelo menos os campos obrigatórios: **Cliente** e **Data do Evento**.")
            else:
                fat_bruto = aprovado + val_extra
                if resp_imposto == "Por Conta do Cliente":
                    fat_bruto += imposto_calculated

                custos_operacionais = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica
                custo_imposto_deducao = imposto_calculated if resp_imposto == "Incluso no Valor" else 0.0
                lucro_liquido = fat_bruto - custo_imposto_deducao - custos_operacionais

                novo_registro = {
                    "Cliente": cliente,
                    "Data Evento": data_evento,
                    "Horário": horario,
                    "Data Montagem": data_montagem,
                    "Horário Montagem": horario_montagem,
                    "Complexo / Local": complexo,
                    "Aprovado": aprovado,
                    "Val. Extra": val_extra,
                    "Faturamento Bruto": fat_bruto,
                    "10% NF": imposto_calculated,
                    "Responsável Imposto": resp_imposto,
                    "Custos Operacionais + Logística": custos_operacionais,
                    "Custo Resolume": custo_resolume,
                    "Custo Iluminação": custo_iluminacao,
                    "Custo Sonorização": custo_sonorizacao,
                    "Custo Diretor": custo_diretor,
                    "Custo Logística": custo_logistica,
                    "Valor Recebido Cliente": val_recebido,
                    "Valor Pago Equipe": val_pago_equipe,
                    "Status Recebimento": status_rec,
                    "Status Pagamento": status_pag,
                    "Lucro Real": lucro_liquido,
                    "Lucro Miguel Araújo": lucro_liquido * 0.50,
                    "Lucro Antonio Carlos": lucro_liquido * 0.50,
                    "Equipamentos": equipamentos,
                    "Equipe Técnica": equipe_tecnica,
                    "Observações": observacoes
                }

                if selecao_edit != "-- Criar Novo Evento --":
                    atualizar_evento_db(dados_ev["id"], novo_registro)
                    st.success(f"Evento '{cliente}' atualizado com sucesso!")
                else:
                    salvar_evento_db(novo_registro)
                    st.success(f"Novo evento '{cliente}' registrado com sucesso!")
                
                st.rerun()

# ---------------------------------------------------------
# ABA 3: EMISSOR DE RECIBOS EM PDF
# ---------------------------------------------------------
with tab_recibo:
    st.subheader("📄 Emissor de Recibo de Pagamento / Ressarcimento")
    st.write("Gere rapidamente recibos formais em formato PDF para prestadores de serviço ou reembolsos de equipe.")
    
    with st.form("form_recibo"):
        r_favorecido = st.text_input("Nome do Favorecido / Recebedor *")
        r_valor = st.number_input("Valor Total (R$) *", min_value=0.0, step=50.0)
        r_cliente = st.text_input("Cliente / Projeto de Referência *")
        r_data_ev = st.text_input("Data do Evento *")
        r_desc = st.text_area("Descrição do Serviço ou Despesas Reembolsadas *", height=100)
        
        btn_gerar_recibo = st.form_submit_button("📄 Gerar Recibo PDF")
        
        if btn_gerar_recibo:
            if not r_favorecido or r_valor <= 0 or not r_cliente or not r_desc:
                st.error("Preencha todos os campos do formulário para gerar o recibo.")
            else:
                pdf_recibo_buffer = gerar_pdf_recibo(r_favorecido, r_valor, r_desc, r_cliente, r_data_ev)
                st.download_button(
                    label="📥 Baixar Recibo Gerado (PDF)",
                    data=pdf_recibo_buffer,
                    file_name=f"Recibo_{r_favorecido.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

# ---------------------------------------------------------
# ABA 4: BACKUP E EXPORTAÇÃO EXCEL
# ---------------------------------------------------------
with tab_backup:
    st.subheader("💾 Exportação de Dados e Backup")
    st.write("Baixe a planilha completa de todos os eventos armazenados no banco de dados SQLite local.")
    
    if faturamentos:
        excel_buffer = gerar_excel_backup(faturamentos)
        st.download_button(
            label="📊 Download Backup Completo (.xlsx)",
            data=excel_buffer,
            file_name=f"Backup_Eventos_Miguel_Araujo_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Nenhum registro para exportar.")
