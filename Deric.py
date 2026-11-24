import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
import time
from streamlit_gsheets import GSheetsConnection

# =====================================================================
# 1. CONFIGURAÇÃO  (nada mudou na conexão com o Google Sheets)
# =====================================================================
st.set_page_config(page_title="Deric Relatorio 2026", layout="wide", page_icon="🛡️")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Bb9wK8dwRYjOJ5leTKxT9VQ0Ib7z-aD5MXCHJX0hNXs/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# =====================================================================
# 2. FUNÇÕES DE DADOS  (idênticas às originais — mesmas abas e colunas)
# =====================================================================
@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df_p = conn.read(spreadsheet=URL_PLANILHA, worksheet="Presencas")
        df_v = conn.read(spreadsheet=URL_PLANILHA, worksheet="Visitantes")
        df_m = conn.read(spreadsheet=URL_PLANILHA, worksheet="Membros")

        if df_p is None or df_p.empty: df_p = pd.DataFrame(columns=['Data', 'Líder', 'Nome', 'Tipo', 'Célula', 'Culto'])
        if df_v is None or df_v.empty: df_v = pd.DataFrame(columns=['Data', 'Líder', 'Vis_Celula', 'Vis_Culto'])

        def padronizar(df):
            df['Data_Obj'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df['Data_Ref'] = df['Data_Obj'].dt.strftime('%Y-%m-%d')
            df['MesNum'] = df['Data_Obj'].dt.month
            return df

        df_p = padronizar(df_p)
        df_v = padronizar(df_v)

        for col in ['Célula', 'Culto']: df_p[col] = pd.to_numeric(df_p[col], errors='coerce').fillna(0).astype(int)
        for col in ['Vis_Celula', 'Vis_Culto']: df_v[col] = pd.to_numeric(df_v[col], errors='coerce').fillna(0).astype(int)

        m_dict = {}
        if df_m is not None and not df_m.empty:
            for _, row in df_m.iterrows():
                l = row.get('Líder')
                if l and l not in m_dict: m_dict[l] = {}
                if l and row.get('Nome') != "LIDER_INICIAL": m_dict[l][row['Nome']] = row.get('Tipo', 'Membro')
        return df_p.dropna(subset=['Data_Obj']), df_v.dropna(subset=['Data_Obj']), m_dict
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame(), pd.DataFrame(), {}


def salvar_seguro(worksheet, df):
    try:
        df_save = df.copy()
        cols_limpar = ['Data_Obj', 'Data_Ref', 'MesNum']
        df_save = df_save.drop(columns=[c for c in cols_limpar if c in df_save.columns])
        if 'Data' in df_save.columns: df_save['Data'] = df_save['Data'].astype(str)
        conn.update(spreadsheet=URL_PLANILHA, worksheet=worksheet, data=df_save)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}"); return False


# =====================================================================
# 3. INICIALIZAÇÃO
# =====================================================================
db_p, db_v, m_dict = carregar_dados()
st.session_state.db = db_p
st.session_state.db_visitantes = db_v
st.session_state.membros_cadastrados = m_dict

# =====================================================================
# 4. ESTILO (visual novo)
# =====================================================================
COR_FUNDO = "#0B1120"
COR_CARD = "#131C31"
COR_BORDA = "#1F2A44"
COR_TEXTO = "#E2E8F0"
COR_SUAVE = "#94A3B8"
COR_PRIMARIA = "#38BDF8"   # Membros
COR_FA = "#A78BFA"         # FA
COR_VIS = "#34D399"        # Visitantes
COR_ALERTA = "#F87171"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: radial-gradient(1200px 600px at 10% -10%, #12234a 0%, {COR_FUNDO} 55%); color: {COR_TEXTO}; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1300px; }}

/* Cabeçalho */
.hero {{
    background: linear-gradient(135deg, #0EA5E9 0%, #6366F1 60%, #8B5CF6 100%);
    border-radius: 18px; padding: 22px 28px; margin-bottom: 18px;
    box-shadow: 0 10px 30px rgba(14,165,233,.18);
}}
.hero h1 {{ color: white; font-size: 1.9rem; font-weight: 800; margin: 0; line-height: 1.2; }}
.hero p  {{ color: rgba(255,255,255,.85); margin: 4px 0 0 0; font-size: .95rem; }}

/* Abas */
.stTabs [data-baseweb="tab-list"] {{ gap: 6px; background: {COR_CARD}; padding: 6px; border-radius: 12px; border: 1px solid {COR_BORDA}; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 8px; padding: 8px 16px; color: {COR_SUAVE}; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ background: #1E3A5F !important; color: white !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* Cards de métrica */
.kpi {{
    background: {COR_CARD}; border: 1px solid {COR_BORDA}; border-radius: 14px;
    padding: 14px 16px; margin-bottom: 12px; position: relative; overflow: hidden;
}}
.kpi::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--c); }}
.kpi-label {{ font-size: .78rem; color: {COR_SUAVE}; text-transform: uppercase; letter-spacing: .05em; font-weight: 600; }}
.kpi-value {{ font-size: 1.7rem; font-weight: 800; color: white; margin-top: 2px; }}
.kpi-sub   {{ font-size: .78rem; color: {COR_SUAVE}; }}
.kpi-bar   {{ height: 6px; background: #0F172A; border-radius: 99px; margin-top: 8px; overflow: hidden; }}
.kpi-bar > div {{ height: 100%; background: var(--c); border-radius: 99px; }}

/* Títulos de seção */
.sec {{ font-size: 1.15rem; font-weight: 700; color: white; margin: 18px 0 10px 0; display: flex; align-items: center; gap: 8px; }}
.sec small {{ color: {COR_SUAVE}; font-weight: 500; font-size: .85rem; }}

/* Alertas */
.alerta {{
    background: rgba(248,113,113,.08); border: 1px solid rgba(248,113,113,.35);
    border-radius: 10px; padding: 8px 12px; margin-bottom: 6px; font-size: .9rem; color: #FECACA;
}}
.alerta b {{ color: white; }}
.ok {{
    background: rgba(52,211,153,.08); border: 1px solid rgba(52,211,153,.35);
    border-radius: 10px; padding: 10px 14px; color: #A7F3D0;
}}

/* Lançamento - linha de pessoa */
.pessoa {{ display: flex; align-items: center; gap: 12px; padding: 4px 0; }}
.avatar {{
    width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-weight: 800; color: white; font-size: .95rem; flex-shrink: 0;
}}
.pessoa-nome {{ font-weight: 700; color: white; font-size: 1rem; line-height: 1.1; }}
.badge {{ display: inline-block; font-size: .7rem; font-weight: 700; padding: 2px 8px; border-radius: 99px; margin-top: 3px; }}

/* Botões */
.stButton > button {{ border-radius: 10px; font-weight: 600; border: 1px solid {COR_BORDA}; transition: all .15s; }}
.stButton > button:hover {{ transform: translateY(-1px); }}
.stButton > button[kind="primary"] {{ background: linear-gradient(135deg, #0EA5E9, #6366F1); border: none; }}

/* Contêineres com borda */
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px !important; border-color: {COR_BORDA} !important; background: {COR_CARD}; }}

/* Sidebar */
section[data-testid="stSidebar"] {{ background: #0A0F1C; border-right: 1px solid {COR_BORDA}; }}

/* Mobile */
@media (max-width: 640px) {{
    .hero h1 {{ font-size: 1.4rem; }}
    .kpi-value {{ font-size: 1.35rem; }}
    .block-container {{ padding-left: .8rem; padding-right: .8rem; }}
}}
</style>
""", unsafe_allow_html=True)

MESES_NOMES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
MESES_MAP = {n: i+1 for i, n in enumerate(MESES_NOMES)}

CORES_TIPO = {"Liderança": "#F59E0B", "Membro": COR_PRIMARIA, "FA": COR_FA}


# ---------- Helpers visuais ----------
def secao(titulo, sub=""):
    st.markdown(f'<div class="sec">{titulo} <small>{sub}</small></div>', unsafe_allow_html=True)


def kpi(col, label, valor, cor, sub="", pct=None):
    barra = f'<div class="kpi-bar"><div style="width:{max(0, min(pct, 100)):.0f}%"></div></div>' if pct is not None else ""
    col.markdown(
        f'<div class="kpi" style="--c:{cor}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{valor}</div><div class="kpi-sub">{sub}</div>{barra}</div>',
        unsafe_allow_html=True,
    )


def iniciais(nome):
    partes = str(nome).split()
    return (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper() if partes else "?"


def estilo_grafico(fig, altura=320):
    fig.update_layout(
        height=altura, template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=COR_TEXTO),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, linecolor=COR_BORDA)
    fig.update_yaxes(gridcolor="#1E293B", zeroline=False)
    return fig


# =====================================================================
# CABEÇALHO
# =====================================================================
st.markdown(
    f'<div class="hero"><h1>🛡️ Deric e Nayara</h1>'
    f'<p>Relatório de Células e Culto · {datetime.now().strftime("%d/%m/%Y")}</p></div>',
    unsafe_allow_html=True,
)

# =====================================================================
# 5. CONTROLE DE ACESSO
# =====================================================================
st.sidebar.title("🔐 Área Restrita")
acesso_admin = st.sidebar.text_input("Senha de Gestão:", type="password")
SENHA_CORRETA = "Videira@1020"

# Lógica das Abas
if acesso_admin == SENHA_CORRETA:
    tab_dash, tab_lanc, tab_gestao, tab_ob = st.tabs(["📊 Dashboard", "📝 Relatório do Líder", "⚙️ Gestão de Células", "📋 Relatório OB"])
else:
    tab_lanc = st.tabs(["📝 Relatório do Líder"])[0]
    tab_dash, tab_gestao, tab_ob = None, None, None
    if acesso_admin != "":
        st.sidebar.error("Senha incorreta!")

# =====================================================================
# ABA DASHBOARD
# =====================================================================
if tab_dash:
    with tab_dash:
        top1, top2 = st.columns([5, 1])
        with top2:
            if st.button("🔄 Sincronizar", use_container_width=True): st.cache_data.clear(); st.rerun()

        if st.session_state.db.empty:
            st.info("Ainda não há lançamentos na planilha.")
        else:
            lids_atuais = sorted(list(st.session_state.membros_cadastrados.keys()))
            with top1:
                lids_f = st.multiselect("Filtrar Células:", lids_atuais, default=lids_atuais)

            # ---- Filtros de período ----
            f1, f2 = st.columns(2)
            m_s = f1.selectbox("Mês de Análise:", MESES_NOMES, index=datetime.now().month-1)
            df_m = st.session_state.db[st.session_state.db['MesNum'] == MESES_MAP[m_s]]

            if df_m.empty:
                st.info(f"Nenhum lançamento em {m_s}.")
            else:
                d_m = sorted(df_m['Data_Ref'].unique(), reverse=True)
                s_r = f2.selectbox("Semana Selecionada:", d_m, format_func=lambda x: datetime.strptime(x, '%Y-%m-%d').strftime('%d/%m/%Y'))
                df_s = df_m[(df_m['Data_Ref'] == s_r) & (df_m['Líder'].isin(lids_f))]
                dv_s = st.session_state.db_visitantes[(st.session_state.db_visitantes['Data_Ref'] == s_r) & (st.session_state.db_visitantes['Líder'].isin(lids_f))]

                def get_vals(tipo, modo):
                    if tipo == "M":
                        total = sum([1 for l in lids_f for n, t in st.session_state.membros_cadastrados.get(l, {}).items() if t == "Membro"]) + len(lids_f)
                        pres = int(df_s[df_s['Tipo'].isin(['Membro', 'Liderança'])][modo].sum())
                        return pres, total
                    elif tipo == "FA":
                        total = sum([1 for l in lids_f for n, t in st.session_state.membros_cadastrados.get(l, {}).items() if t == "FA"])
                        pres = int(df_s[df_s['Tipo'] == "FA"][modo].sum())
                        return pres, total
                    else:
                        return (int(dv_s['Vis_Celula' if modo == 'Célula' else 'Vis_Culto'].sum()) if not dv_s.empty else 0), None

                secao("🏠 Célula", f"semana de {datetime.strptime(s_r, '%Y-%m-%d').strftime('%d/%m')}")
                c1, c2, c3 = st.columns(3)
                for col, (tp, lbl, cor) in zip([c1, c2, c3], [("M", "Membros", COR_PRIMARIA), ("FA", "FA", COR_FA), ("V", "Visitantes", COR_VIS)]):
                    p, t = get_vals(tp, "Célula")
                    if t is None: kpi(col, lbl, p, cor, "nesta semana")
                    else: kpi(col, lbl, f"{p}/{t}", cor, f"{(p/t*100 if t else 0):.0f}% de presença", (p/t*100 if t else 0))

                secao("⛪ Culto")
                c4, c5, c6 = st.columns(3)
                for col, (tp, lbl, cor) in zip([c4, c5, c6], [("M", "Membros", COR_PRIMARIA), ("FA", "FA", COR_FA), ("V", "Visitantes", COR_VIS)]):
                    p, t = get_vals(tp, "Culto")
                    if t is None: kpi(col, lbl, p, cor, "nesta semana")
                    else: kpi(col, lbl, f"{p}/{t}", cor, f"{(p/t*100 if t else 0):.0f}% de presença", (p/t*100 if t else 0))

                # ---- Gráficos semanais ----
                secao("📈 Evolução semanal", m_s)
                cg1, cg2 = st.columns(2)
                for col, modo, k, tit in zip([cg1, cg2], ['Célula', 'Culto'], ['chart_cel', 'chart_cul'], ["Célula", "Culto"]):
                    g_d = df_m[df_m['Líder'].isin(lids_f)].groupby('Data_Ref')[modo].sum().reset_index()
                    g_v = st.session_state.db_visitantes[(st.session_state.db_visitantes['MesNum'] == MESES_MAP[m_s]) & (st.session_state.db_visitantes['Líder'].isin(lids_f))].groupby('Data_Ref')['Vis_Celula' if modo == 'Célula' else 'Vis_Culto'].sum().reset_index()
                    mrg = pd.merge(g_d, g_v, on='Data_Ref', how='outer').fillna(0).sort_values('Data_Ref')
                    mrg['D'] = mrg['Data_Ref'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d').strftime('%d/%m'))
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=mrg['D'], y=mrg[modo], name='Membros + FA', mode='lines+markers+text',
                                             text=mrg[modo].astype(int), textposition="top center",
                                             line=dict(color=COR_PRIMARIA, width=3, shape="spline"), marker=dict(size=9),
                                             fill="tozeroy", fillcolor="rgba(56,189,248,.10)"))
                    fig.add_trace(go.Scatter(x=mrg['D'], y=mrg.iloc[:, 2], name='Visitantes', mode='lines+markers+text',
                                             text=mrg.iloc[:, 2].astype(int), textposition="bottom center",
                                             line=dict(color=COR_VIS, width=3, shape="spline"), marker=dict(size=9)))
                    estilo_grafico(fig, 300).update_layout(title=dict(text=tit, x=0, font=dict(size=15)))
                    with col:
                        with st.container(border=True):
                            st.plotly_chart(fig, use_container_width=True, key=k)

                # ---- Comparativo de meses ----
                secao("📊 Comparativo mensal (Célula)", f"{m_s} e 2 meses anteriores")
                idx_analise = MESES_MAP[m_s]
                dados_comp = []
                for idx in [idx_analise - 2, idx_analise - 1, idx_analise]:
                    if idx > 0:
                        nome_m = MESES_NOMES[idx-1]
                        d_mes = st.session_state.db[(st.session_state.db['MesNum'] == idx) & (st.session_state.db['Líder'].isin(lids_f))]
                        v_mes = st.session_state.db_visitantes[(st.session_state.db_visitantes['MesNum'] == idx) & (st.session_state.db_visitantes['Líder'].isin(lids_f))]
                        val_fa = int(d_mes[d_mes['Tipo'] == "FA"]['Célula'].sum())
                        val_mem = int(d_mes[d_mes['Tipo'].isin(['Membro', 'Liderança'])]['Célula'].sum())
                        val_vis = int(v_mes['Vis_Celula'].sum())
                        dados_comp.append({"Mês": nome_m, "Métrica": "Membro + FA", "Valor": val_mem + val_fa})
                        dados_comp.append({"Mês": nome_m, "Métrica": "Visitante", "Valor": val_vis})
                        dados_comp.append({"Mês": nome_m, "Métrica": "Total Geral", "Valor": val_mem + val_fa + val_vis})
                if dados_comp:
                    fig_bar = px.bar(pd.DataFrame(dados_comp), x="Mês", y="Valor", color="Métrica", barmode="group", text_auto=True,
                                     color_discrete_map={"Membro + FA": COR_PRIMARIA, "Visitante": COR_VIS, "Total Geral": "#64748B"})
                    fig_bar.update_traces(marker_line_width=0, textposition="outside")
                    estilo_grafico(fig_bar, 380).update_layout(legend=dict(xanchor="center", x=0.5), bargap=0.25)
                    with st.container(border=True):
                        st.plotly_chart(fig_bar, use_container_width=True)

            # ---- Alertas (agrupados por célula) ----
            datas_u = sorted(st.session_state.db['Data_Ref'].unique(), reverse=True)
            if len(datas_u) >= 2:
                d1, d2 = datas_u[0], datas_u[1]
                alertas = {}
                for lid in lids_f:
                    itens = []
                    v1 = st.session_state.db_visitantes[(st.session_state.db_visitantes['Data_Ref'] == d1) & (st.session_state.db_visitantes['Líder'] == lid)]['Vis_Celula'].sum()
                    v2 = st.session_state.db_visitantes[(st.session_state.db_visitantes['Data_Ref'] == d2) & (st.session_state.db_visitantes['Líder'] == lid)]['Vis_Celula'].sum()
                    if v1 == 0 and v2 == 0: itens.append("🚩 <b>Sem visitantes</b> nas últimas 2 semanas")
                    for n, t in st.session_state.membros_cadastrados.get(lid, {}).items():
                        p1 = st.session_state.db[(st.session_state.db['Data_Ref'] == d1) & (st.session_state.db['Líder'] == lid) & (st.session_state.db['Nome'] == n)]['Célula'].sum()
                        p2 = st.session_state.db[(st.session_state.db['Data_Ref'] == d2) & (st.session_state.db['Líder'] == lid) & (st.session_state.db['Nome'] == n)]['Célula'].sum()
                        if p1 == 0 and p2 == 0: itens.append(f"👤 <b>{n}</b> ausente nas últimas 2 reuniões")
                    if itens: alertas[lid] = itens

                total_alertas = sum(len(v) for v in alertas.values())
                secao("⚠️ Alertas de frequência",
                      f"{datetime.strptime(d2, '%Y-%m-%d').strftime('%d/%m')} e {datetime.strptime(d1, '%Y-%m-%d').strftime('%d/%m')}")
                if not alertas:
                    st.markdown('<div class="ok">✅ Nenhum alerta. Todos presentes e com visitantes!</div>', unsafe_allow_html=True)
                else:
                    cols_al = st.columns(2)
                    for i, (lid, itens) in enumerate(alertas.items()):
                        with cols_al[i % 2]:
                            with st.expander(f"{lid} · {len(itens)} alerta(s)", expanded=False):
                                for it in itens:
                                    st.markdown(f'<div class="alerta">{it}</div>', unsafe_allow_html=True)

# =====================================================================
# ABA LANÇAR
# =====================================================================
with tab_lanc:
    if not st.session_state.membros_cadastrados:
        st.info("Nenhuma célula cadastrada ainda.")
    else:
        with st.container(border=True):
            c_m, c_d, c_c = st.columns(3)
            l_m = c_m.selectbox("📅 Mês", MESES_NOMES, index=datetime.now().month-1)
            datas_s = [date(2026, MESES_MAP[l_m], d) for d in range(1, 32) if (date(2026, MESES_MAP[l_m], 1) + timedelta(days=d-1)).month == MESES_MAP[l_m] and (date(2026, MESES_MAP[l_m], 1) + timedelta(days=d-1)).weekday() == 5]
            d_l = c_d.selectbox("🗓️ Sábado", datas_s, format_func=lambda x: x.strftime('%d/%m'))
            l_l = c_c.selectbox("🏠 Sua Célula", sorted(st.session_state.membros_cadastrados.keys()))

        if "presencas_bt" not in st.session_state: st.session_state.presencas_bt = {}

        pessoas = [(l_l, "Liderança")] + list(st.session_state.membros_cadastrados.get(l_l, {}).items())
        for nome, tipo in pessoas:
            for pref in ("bt_cel_", "bt_cul_"):
                if f"{pref}{nome}" not in st.session_state.presencas_bt:
                    st.session_state.presencas_bt[f"{pref}{nome}"] = (tipo == "Liderança")

        tot_cel = sum(1 for n, _ in pessoas if st.session_state.presencas_bt[f"bt_cel_{n}"])
        tot_cul = sum(1 for n, _ in pessoas if st.session_state.presencas_bt[f"bt_cul_{n}"])
        r1, r2, r3 = st.columns(3)
        kpi(r1, "Pessoas na célula", len(pessoas), "#64748B")
        kpi(r2, "Presentes na célula", f"{tot_cel}/{len(pessoas)}", COR_PRIMARIA, pct=tot_cel/len(pessoas)*100)
        kpi(r3, "Presentes no culto", f"{tot_cul}/{len(pessoas)}", COR_FA, pct=tot_cul/len(pessoas)*100)

        secao("✅ Chamada", "toque para marcar presença")

        def criar_linha_mobile(nome, tipo):
            k_cel = f"bt_cel_{nome}"
            k_cul = f"bt_cul_{nome}"
            cor = CORES_TIPO.get(tipo, COR_PRIMARIA)
            with st.container(border=True):
                info, b_cel, b_cul = st.columns([3, 2, 2], vertical_alignment="center")
                info.markdown(
                    f'<div class="pessoa"><div class="avatar" style="background:{cor}">{iniciais(nome)}</div>'
                    f'<div><div class="pessoa-nome">{nome}</div>'
                    f'<span class="badge" style="background:{cor}22;color:{cor}">{tipo}</span></div></div>',
                    unsafe_allow_html=True,
                )
                on_cel = st.session_state.presencas_bt[k_cel]
                if b_cel.button("🏠 Célula ✓" if on_cel else "🏠 Célula", key=f"btn_{k_cel}",
                                type="primary" if on_cel else "secondary", use_container_width=True):
                    st.session_state.presencas_bt[k_cel] = not on_cel
                    st.rerun()
                on_cul = st.session_state.presencas_bt[k_cul]
                if b_cul.button("⛪ Culto ✓" if on_cul else "⛪ Culto", key=f"btn_{k_cul}",
                                type="primary" if on_cul else "secondary", use_container_width=True):
                    st.session_state.presencas_bt[k_cul] = not on_cul
                    st.rerun()

        for nome, tipo in pessoas:
            criar_linha_mobile(nome, tipo)

        secao("✨ Visitantes")
        with st.container(border=True):
            col_v1, col_v2 = st.columns(2)
            vce = col_v1.number_input("🏠 Visitantes na Célula", 0)
            vcu = col_v2.number_input("⛪ Visitantes no Culto", 0)

        if st.button("💾 SALVAR LANÇAMENTO", use_container_width=True, type="primary"):
            novos = []
            novos.append({
                "Data": d_l.strftime('%d/%m/%Y'), "Líder": l_l, "Nome": l_l, "Tipo": "Liderança",
                "Célula": 1 if st.session_state.presencas_bt[f"bt_cel_{l_l}"] else 0,
                "Culto": 1 if st.session_state.presencas_bt[f"bt_cul_{l_l}"] else 0
            })
            for n, t in st.session_state.membros_cadastrados.get(l_l, {}).items():
                novos.append({
                    "Data": d_l.strftime('%d/%m/%Y'), "Líder": l_l, "Nome": n, "Tipo": t,
                    "Célula": 1 if st.session_state.presencas_bt[f"bt_cel_{n}"] else 0,
                    "Culto": 1 if st.session_state.presencas_bt[f"bt_cul_{n}"] else 0
                })

            dt_ref = d_l.strftime('%d/%m/%Y')
            dfp = pd.concat([st.session_state.db[~((st.session_state.db['Data'] == dt_ref) & (st.session_state.db['Líder'] == l_l))], pd.DataFrame(novos)])
            dfv = pd.concat([st.session_state.db_visitantes[~((st.session_state.db_visitantes['Data'] == dt_ref) & (st.session_state.db_visitantes['Líder'] == l_l))], pd.DataFrame([{"Data": dt_ref, "Líder": l_l, "Vis_Celula": vce, "Vis_Culto": vcu}])])

            with st.spinner("Salvando na planilha..."):
                ok = salvar_seguro("Presencas", dfp) and salvar_seguro("Visitantes", dfv)
            if ok:
                st.success("Salvo com sucesso!")
                st.balloons()
                st.session_state.presencas_bt = {}
                time.sleep(1)
                st.cache_data.clear(); st.rerun()

# =====================================================================
# ABA GESTÃO
# =====================================================================
if tab_gestao:
    with tab_gestao:
        def sync_membros():
            lista = []
            for ld, ps in st.session_state.membros_cadastrados.items():
                if not ps: lista.append({"Líder": ld, "Nome": "LIDER_INICIAL", "Tipo": "Liderança"})
                else: [lista.append({"Líder": ld, "Nome": n, "Tipo": t}) for n, t in ps.items()]
            salvar_seguro("Membros", pd.DataFrame(lista))

        # Resumo
        cad = st.session_state.membros_cadastrados
        g1, g2, g3 = st.columns(3)
        kpi(g1, "Células", len(cad), "#F59E0B")
        kpi(g2, "Membros", sum(1 for ps in cad.values() for t in ps.values() if t == "Membro"), COR_PRIMARIA)
        kpi(g3, "FA", sum(1 for ps in cad.values() for t in ps.values() if t == "FA"), COR_FA)

        secao("➕ Adicionar novo")
        c_add1, c_add2 = st.columns(2)
        with c_add1:
            with st.container(border=True):
                st.markdown("**Nova célula**")
                nl = st.text_input("Nome do novo líder")
                if st.button("Criar Célula", use_container_width=True):
                    if nl and nl not in st.session_state.membros_cadastrados:
                        st.session_state.membros_cadastrados[nl] = {}; sync_membros(); st.rerun()
        with c_add2:
            with st.container(border=True):
                st.markdown("**Nova pessoa**")
                if st.session_state.membros_cadastrados:
                    cs = st.selectbox("Célula:", sorted(st.session_state.membros_cadastrados.keys()))
                    nm = st.text_input("Nome da Pessoa")
                    tm = st.radio("Tipo Inicial", ["Membro", "FA"], horizontal=True)
                    if st.button("Adicionar Pessoa", use_container_width=True):
                        if nm: st.session_state.membros_cadastrados[cs][nm] = tm; sync_membros(); st.rerun()

        secao("🚀 Multiplicação e transferência")
        if st.session_state.membros_cadastrados:
            with st.container(border=True):
                o1, o2 = st.columns(2)
                cel_origem = o1.selectbox("Célula de Origem:", sorted(st.session_state.membros_cadastrados.keys()), key="orig")
                membros_orig = list(st.session_state.membros_cadastrados[cel_origem].keys())
                if not membros_orig:
                    st.caption("Essa célula ainda não tem pessoas cadastradas.")
                else:
                    membro_transf = o2.selectbox("Pessoa:", membros_orig)
                    tipo_membro = st.session_state.membros_cadastrados[cel_origem][membro_transf]
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        st.caption("Promover a líder de uma nova célula")
                        if st.button(f"🌟 Tornar Líder: {membro_transf}", use_container_width=True):
                            del st.session_state.membros_cadastrados[cel_origem][membro_transf]
                            st.session_state.membros_cadastrados[membro_transf] = {}
                            sync_membros(); st.rerun()
                    with col_t2:
                        cel_dest = [c for c in st.session_state.membros_cadastrados.keys() if c != cel_origem]
                        if cel_dest:
                            cel_destino = st.selectbox("Transferir para:", cel_dest)
                            if st.button("Confirmar Transferência", use_container_width=True):
                                st.session_state.membros_cadastrados[cel_destino][membro_transf] = tipo_membro
                                del st.session_state.membros_cadastrados[cel_origem][membro_transf]
                                sync_membros(); st.rerun()

        secao("🗂️ Gerenciar e excluir")
        if st.session_state.membros_cadastrados:
            with st.container(border=True):
                cel_edit = st.selectbox("Célula:", sorted(st.session_state.membros_cadastrados.keys()))
                membros_da_cel = st.session_state.membros_cadastrados.get(cel_edit, {})
                for nome, tipo in list(membros_da_cel.items()):
                    cor = CORES_TIPO.get(tipo, COR_PRIMARIA)
                    c_n, c_b1, c_b2 = st.columns([5, 3, 1], vertical_alignment="center")
                    c_n.markdown(
                        f'<div class="pessoa"><div class="avatar" style="background:{cor};width:32px;height:32px;font-size:.8rem">{iniciais(nome)}</div>'
                        f'<div class="pessoa-nome">{nome} <span class="badge" style="background:{cor}22;color:{cor}">{tipo}</span></div></div>',
                        unsafe_allow_html=True,
                    )
                    novo_t = "FA" if tipo == "Membro" else "Membro"
                    if c_b1.button(f"Mudar para {novo_t}", key=f"t_{nome}", use_container_width=True):
                        st.session_state.membros_cadastrados[cel_edit][nome] = novo_t; sync_membros(); st.rerun()
                    if c_b2.button("🗑️", key=f"x_{nome}", help=f"Remover {nome}", use_container_width=True):
                        del st.session_state.membros_cadastrados[cel_edit][nome]; sync_membros(); st.rerun()

                st.divider()
                if st.button(f"Excluir Célula de {cel_edit}"):
                    del st.session_state.membros_cadastrados[cel_edit]; sync_membros(); st.rerun()

# =====================================================================
# ABA RELATÓRIO OB
# =====================================================================
if tab_ob:
    with tab_ob:
        m_ob = st.selectbox("Mês:", MESES_NOMES, index=datetime.now().month-1, key="ob_m_final")
        df_ob = st.session_state.db[st.session_state.db['MesNum'] == MESES_MAP[m_ob]]
        df_v_ob = st.session_state.db_visitantes[st.session_state.db_visitantes['MesNum'] == MESES_MAP[m_ob]]

        if df_ob.empty:
            st.info(f"Nenhum lançamento em {m_ob}.")
        else:
            secao("📊 Totais semanais da rede", "Célula / Culto")
            res_sem = []
            for d_r in sorted(df_ob['Data_Ref'].unique()):
                d_f = datetime.strptime(d_r, '%Y-%m-%d').strftime('%d/%m')
                df_s = df_ob[df_ob['Data_Ref'] == d_r]
                m_ce = df_s[df_s['Tipo'].isin(['Membro', 'Liderança'])]['Célula'].sum()
                m_cu = df_s[df_s['Tipo'].isin(['Membro', 'Liderança'])]['Culto'].sum()
                f_ce, f_cu = df_s[df_s['Tipo'] == "FA"]['Célula'].sum(), df_s[df_s['Tipo'] == "FA"]['Culto'].sum()
                v_ce, v_cu = df_v_ob[df_v_ob['Data_Ref'] == d_r]['Vis_Celula'].sum(), df_v_ob[df_v_ob['Data_Ref'] == d_r]['Vis_Culto'].sum()
                res_sem.append({"Data": d_f, "Membros": f"{m_ce} / {m_cu}", "FA": f"{f_ce} / {f_cu}",
                                "Visitantes": f"{v_ce} / {v_cu}", "Total": f"{m_ce+f_ce+v_ce} / {m_cu+f_cu+v_cu}"})
            st.dataframe(pd.DataFrame(res_sem), use_container_width=True, hide_index=True)

            secao("🕵️ Chamada detalhada", "Célula | Culto")
            cel_sel_ob = st.selectbox("Selecionar Célula:", sorted(st.session_state.membros_cadastrados.keys()), key="ob_c_final")
            m_cel = [{"Nome": cel_sel_ob, "Tipo": "Liderança"}] + [{"Nome": n, "Tipo": t} for n, t in st.session_state.membros_cadastrados.get(cel_sel_ob, {}).items()]
            d_mes = sorted(df_ob['Data_Ref'].unique()); cham_d = []
            for p in m_cel:
                ln = {"Pessoa": f"{p['Nome']} ({p['Tipo']})"}
                for d in d_mes:
                    df_c = df_ob[(df_ob['Data_Ref'] == d) & (df_ob['Nome'] == p['Nome']) & (df_ob['Líder'] == cel_sel_ob)]
                    if not df_c.empty:
                        p_ce = "✅" if df_c['Célula'].sum() > 0 else "❌"
                        p_cu = "✅" if df_c['Culto'].sum() > 0 else "❌"
                        ln[datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m')] = f"{p_ce} | {p_cu}"
                    else: ln[datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m')] = "❌ | ❌"
                cham_d.append(ln)
            st.dataframe(pd.DataFrame(cham_d), use_container_width=True, hide_index=True)
