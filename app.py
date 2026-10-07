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
            val_recebido_cliente REAL,
            val_pago_equipe REAL,
            status_recebimento TEXT,
            status_pagamento TEXT,
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
            "Valor Recebido Cliente": row[17] if len(row) > 17 and row[17] is not None else 0.0,
            "Valor Pago Equipe": row[18] if len(row) > 18 and row[18] is not None else 0.0,
            "Status Recebimento": row[19] if len(row) > 19 and row[19] else "Pendente",
            "Status Pagamento": row[20] if len(row) > 20 and row[20] else "Pendente",
            "Lucro Real": row[21] if len(row) > 21 else 0.0,
            "Lucro Miguel Araújo": row[22] if len(row) > 22 else 0.0,
            "Lucro Antonio Carlos": row[23] if len(row) > 23 else 0.0,
            "Pag. Operacional": row[24] if len(row) > 24 else "",
            "Rec. Champions": row[25] if len(row) > 25 else "",
            "Equipamentos": row[26] if len(row) > 26 else "",
            "Equipe Técnica": row[27] if len(row) > 27 else "",
            "Observações": row[28] if len(row) > 28 else ""
        })
    return eventos

def salvar_evento_db(reg):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO eventos (
            cliente, data_evento, horario, complexo, transmissao, aprovado, val_extra, itens_extras,
            faturamento_bruto, imposto_nf, custos_total, custo_resolume, custo_iluminacao, custo_sonorizacao,
            custo_diretor, custo_logistica, val_recebido_cliente, val_pago_equipe, status_recebimento, status_pagamento,
            lucro_real, lucro_miguel, lucro_antonio, pag_operacional, rec_champions, equipamentos, equipe_tecnica, observacoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Complexo Champions"], reg["Transmissão TVs"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Valor Recebido Cliente"],
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
            cliente=?, data_evento=?, horario=?, complexo=?, transmissao=?, aprovado=?, val_extra=?,
            itens_extras=?, faturamento_bruto=?, imposto_nf=?, custos_total=?, custo_resolume=?,
            custo_iluminacao=?, custo_sonorizacao=?, custo_diretor=?, custo_logistica=?, val_recebido_cliente=?,
            val_pago_equipe=?, status_recebimento=?, status_pagamento=?, lucro_real=?, lucro_miguel=?,
            lucro_antonio=?, pag_operacional=?, rec_champions=?, equipamentos=?, equipe_tecnica=?, observacoes=?
        WHERE id=?
    ''', (
        reg["Cliente"], reg["Data Evento"], reg["Horário"], reg["Complexo Champions"], reg["Transmissão TVs"],
        reg["Aprovado"], reg["Val. Extra"], json.dumps(reg["Itens Extras"]), reg["Faturamento Bruto"],
        reg["10% NF"], reg["Custos Operacionais + Logística"], reg["Custo Resolume"], reg["Custo Iluminação"],
        reg["Custo Sonorização"], reg["Custo Diretor"], reg["Custo Logística"], reg["Valor Recebido Cliente"],
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

# Inicializa Banco de Dados
init_db()

# --- CONFIGURAÇÃO DA PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Miguel Araújo Produções - Gestão Financeira Unificada",
    page_icon="💰",
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
    st.subheader("Painel de Controle Financeiro, Recebimentos e Pagamentos")

st.markdown("---")

faturamentos = carregar_eventos()

# --- PAINEL GERAL DE INDICADORES (KPIs) ---
if faturamentos:
    df_kpi = pd.DataFrame(faturamentos)
    
    total_faturado = df_kpi["Faturamento Bruto"].sum()
    total_custos_equipe = df_kpi["Custos Operacionais + Logística"].sum()
    total_impostos = df_kpi["10% NF"].sum()
    
    total_recebido = df_kpi["Valor Recebido Cliente"].sum()
    total_falta_receber = total_faturado - total_recebido
    
    total_pago_equipe = df_kpi["Valor Pago Equipe"].sum()
    total_falta_pagar_equipe = total_custos_equipe - total_pago_equipe
    
    lucro_liquido_total = df_kpi["Lucro Real"].sum()

    st.markdown("## 📊 Controle Financeiro Consolidado")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric("💵 Faturamento Bruto", f"R$ {total_faturado:,.2f}")
    kpi_col2.metric("✅ Total Recebido (Cliente)", f"R$ {total_recebido:,.2f}")
    kpi_col3.metric("⏳ A Receber (Cliente)", f"R$ {total_falta_receber:,.2f}", delta_color="inverse")
    kpi_col4.metric("📈 Lucro Líquido Real", f"R$ {lucro_liquido_total:,.2f}")

    kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)
    kpi_col5.metric("👥 Custo Total c/ Profissionais", f"R$ {total_custos_equipe:,.2f}")
    kpi_col6.metric("💸 Total Já Pago à Equipe", f"R$ {total_pago_equipe:,.2f}")
    kpi_col7.metric("⚠️ A Pagar (Devo à Equipe)", f"R$ {total_falta_pagar_equipe:,.2f}", delta_color="inverse")
    kpi_col8.metric("🧾 Impostos Reservados (10% NF)", f"R$ {total_impostos:,.2f}")

    st.markdown("---")

aba1, aba2, aba3 = st.tabs(["➕ Novo Evento / Lançamento", "✏️ Baixas & Edição Financeira", "📊 Relatórios & PDFs"])

# --- ABA 1: NOVO EVENTO ---
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

        st.markdown("### 👥 5. Pagamentos Devidos a Profissionais / Logística")
        col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)
        with col_c1: custo_resolume = st.number_input("Técnico Resolume (R$)", min_value=0.0, step=50.0)
        with col_c2: custo_iluminacao = st.number_input("Técnico Iluminação (R$)", min_value=0.0, step=50.0)
        with col_c3: custo_sonorizacao = st.number_input("Técnico Som (R$)", min_value=0.0, step=50.0)
        with col_c4: custo_diretor = st.number_input("Direção Técnica (R$)", min_value=0.0, step=50.0)
        with col_c5: custo_logistica = st.number_input("Logística / Frete (R$)", min_value=0.0, step=20.0)

        st.markdown("### 💳 6. Status Inicial de Caixa")
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            val_recebido_init = st.number_input("Quanto o cliente JÁ PAGOU? (R$)", min_value=0.0, step=100.0)
        with col_st2:
            val_pago_equipe_init = st.number_input("Quanto você JÁ PAGOU à equipe? (R$)", min_value=0.0, step=100.0)

        col_d1, col_d2 = st.columns(2)
        with col_d1: dt_pag_operacional = st.date_input("Previsão Pagamento Operacional")
        with col_d2: dt_rec_champions = st.date_input("Previsão Recebimento Cliente")

        obs_gerais = st.text_area("Observações Financeiras / Gerais")

        faturamento_bruto = val_aprovado + val_extra_total
        imposto_nf = faturamento_bruto * 0.10
        total_custos_op = custo_resolume + custo_iluminacao + custo_sonorizacao + custo_diretor + custo_logistica
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
                "Valor Recebido Cliente": val_recebido_init, "Valor Pago Equipe": val_pago_equipe_init,
                "Status Recebimento": status_rec, "Status Pagamento": status_pag,
                "Lucro Real": lucro_real, "Lucro Miguel Araújo": lucro_real * 0.50, "Lucro Antonio Carlos": lucro_real * 0.50,
                "Pag. Operacional": dt_pag_operacional.strftime("%d/%m/%Y"), "Rec. Champions": dt_rec_champions.strftime("%d/%m/%Y"),
                "Equipamentos": equipamentos_contrato if equipamentos_contrato else "Não especificado",
                "Equipe Técnica": equipe_tecnica if equipe_tecnica else "Não especificado",
                "Observações": obs_gerais if obs_gerais else "Nenhuma observação."
            }
            salvar_evento_db(novo_registro)
            st.success("✅ Evento cadastrado e métricas atualizadas!")
            st.rerun()

# --- ABA 2: EDITAR E DAR BAIXA DE PAGAMENTOS/RECEBIMENTOS ---
with aba2:
    st.subheader("✏️ Dar Baixa em Recebimentos e Pagamentos de Profissionais")
    if not faturamentos:
        st.info("Nenhum evento registrado no banco de dados.")
    else:
        idx_edit = st.selectbox(
            "Selecione o Evento para Atualizar Baixas Financeiras:", range(len(faturamentos)),
            format_func=lambda x: f"ID #{faturamentos[x]['id']} - {faturamentos[x]['Cliente']} | Data: {faturamentos[x]['Data Evento']} | Fat: R$ {faturamentos[x]['Faturamento Bruto']:,.2f}"
        )
        
        reg = faturamentos[idx_edit]
        
        with st.form("form_baixa_financeira"):
            st.markdown(f"### 📍 Evento: **{reg['Cliente']}** ({reg['Data Evento']})")
            
            c_rec1, c_rec2, c_rec3 = st.columns(3)
            with c_rec1:
                e_fat_bruto = st.number_input("Faturamento Bruto Total (R$)", value=float(reg["Faturamento Bruto"]))
            with c_rec2:
                e_val_rec = st.number_input("Valor JÁ RECEBIDO do Cliente (R$)", value=float(reg["Valor Recebido Cliente"]))
            with c_rec3:
                falta_rec = e_fat_bruto - e_val_rec
                st.warning(f"**Falta Receber do Cliente:** R$ {falta_rec:,.2f}")

            st.markdown("---")
            st.markdown("### 👥 Custos e Pagamentos de Profissionais")
            
            c_pag1, c_pag2, c_pag3 = st.columns(3)
            with c_pag1:
                e_custo_total = st.number_input("Custo Total c/ Equipe (R$)", value=float(reg["Custos Operacionais + Logística"]))
            with c_pag2:
                e_val_pago = st.number_input("Valor JÁ PAGO para a Equipe (R$)", value=float(reg["Valor Pago Equipe"]))
            with c_pag3:
                falta_pag = e_custo_total - e_val_pago
                st.error(f"**Você ainda Deve à Equipe:** R$ {falta_pag:,.2f}")

            st.markdown("---")
            st.markdown("### 🛠️ Ajuste Individual dos Cachês por Profissional")
            col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
            with col_p1: e_resolume = st.number_input("Resolume (R$)", value=float(reg["Custo Resolume"]))
            with col_p2: e_iluminacao = st.number_input("Iluminação (R$)", value=float(reg["Custo Iluminação"]))
            with col_p3: e_sonorizacao = st.number_input("Som (R$)", value=float(reg["Custo Sonorização"]))
            with col_p4: e_diretor = st.number_input("Diretor (R$)", value=float(reg["Custo Diretor"]))
            with col_p5: e_logistica = st.number_input("Logística (R$)", value=float(reg["Custo Logística"]))

            e_obs = st.text_area("Observações de Pagamento / Transação", value=reg["Observações"])

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                btn_salvar_baixa = st.form_submit_button("🔄 Salvar Baixa e Recalcular")
            with col_btn2:
                btn_excluir_eve = st.form_submit_button("❌ Excluir Evento")

            if btn_salvar_baixa:
                novos_custos = e_resolume + e_iluminacao + e_sonorizacao + e_diretor + e_logistica
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
                    "Valor Recebido Cliente": e_val_rec, "Valor Pago Equipe": e_val_pago,
                    "Status Recebimento": st_rec, "Status Pagamento": st_pag,
                    "Lucro Real": novo_lucro, "Lucro Miguel Araújo": novo_lucro * 0.50, "Lucro Antonio Carlos": novo_lucro * 0.50,
                    "Pag. Operacional": reg["Pag. Operacional"], "Rec. Champions": reg["Rec. Champions"],
                    "Equipamentos": reg["Equipamentos"], "Equipe Técnica": reg["Equipe Técnica"], "Observações": e_obs
                }
                atualizar_evento_db(reg['id'], reg_atualizado)
                st.success("✅ Baixa registrada com sucesso!")
                st.rerun()

            if btn_excluir_eve:
                deletar_evento_db(reg['id'])
                st.warning("🗑️ Registro excluído!")
                st.rerun()

# --- ABA 3: TABELA DETALHADA E EXPORTAÇÃO ---
with aba3:
    st.subheader("📋 Tabela Completa do Financeiro")
    if faturamentos:
        df_full = pd.DataFrame(faturamentos)
        
        # Colunas Calculadas
        df_full["Falta Receber (Cliente)"] = df_full["Faturamento Bruto"] - df_full["Valor Recebido Cliente"]
        df_full["Falta Pagar (Equipe)"] = df_full["Custos Operacionais + Logística"] - df_full["Valor Pago Equipe"]

        st.dataframe(
            df_full[[
                "id", "Cliente", "Data Evento", "Faturamento Bruto", "Valor Recebido Cliente", "Falta Receber (Cliente)",
                "Custos Operacionais + Logística", "Valor Pago Equipe", "Falta Pagar (Equipe)", "Lucro Real",
                "Lucro Miguel Araújo", "Lucro Antonio Carlos"
            ]],
            use_container_width=True
        )
