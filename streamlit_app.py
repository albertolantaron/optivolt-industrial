import streamlit as st
import datetime
import math
import os
import pandas as pd
import plotly.graph_objects as go

# Carga segura de Stripe
try:
    import stripe
except ImportError:
    stripe = None

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="OptiVolt Workbench | CNMC Power Engineering",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CLAVE SECRETA DE STRIPE (SEGURA EN LOCAL Y CLOUD) ---
try:
    stripe_key = st.secrets.get("STRIPE_SECRET_KEY", None)
except Exception:
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", None)

if stripe_key and stripe:
    stripe.api_key = stripe_key

ADMIN_EMAILS = ["alberto.lantaron@gmail.com", "albertterre.lantaron@gmail.com"]

# 👉 PEGA AQUÍ TU ENLACE DE PAGO DE STRIPE (39,00 €):
URL_STRIPE_39 = "https://buy.stripe.com/4gM9AV8hw6mG1dxaEC0Ny04"

# --- CONSTANTES TÉCNICAS (BOE / CIRCULAR 3/2020 CNMC) ---
PRECIOS_PEAJES = {
    "3.0TD (Baja Tensión Industrial > 15 kW)": [15.42, 11.78, 5.26, 4.48, 3.19, 1.82],
    "6.1TD (Media Tensión / Nave Fabril)": [21.84, 17.52, 9.35, 7.82, 4.12, 2.38]
}

PRESETS_DATA = {
    "Taller de Mecanizado y Estampación": {
        "tarifa": "3.0TD (Baja Tensión Industrial > 15 kW)",
        "p_act": [90.0, 90.0, 90.0, 90.0, 90.0, 90.0],
        "p_max": [54.0, 58.0, 44.0, 36.0, 26.0, 22.0],
        "cos_phi": 0.78, "p_media": 48.0, "multa_mes": 240.0,
        "cups": "ES0021000045127891QZ1P"
    },
    "Planta de Inyección de Plásticos": {
        "tarifa": "3.0TD (Baja Tensión Industrial > 15 kW)",
        "p_act": [140.0, 140.0, 140.0, 140.0, 140.0, 140.0],
        "p_max": [102.0, 108.0, 88.0, 78.0, 62.0, 50.0],
        "cos_phi": 0.81, "p_media": 85.0, "multa_mes": 310.0,
        "cups": "ES0031000088992211MN1P"
    },
    "Personalizado (Mis datos / Custom)": {
        "tarifa": "3.0TD (Baja Tensión Industrial > 15 kW)",
        "p_act": [60.0, 60.0, 60.0, 60.0, 60.0, 60.0],
        "p_max": [38.0, 42.0, 32.0, 28.0, 20.0, 16.0],
        "cos_phi": 0.84, "p_media": 32.0, "multa_mes": 130.0,
        "cups": "ES0022000033445566CD1P"
    }
}

# --- ESTILOS VISUALES: TITANIUM WORKBENCH (MÁXIMA LEGIBILIDAD) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    .stApp {
        background-color: #f1f5f9;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Inputs de alto contraste absoluto: fondo blanco, letras oscuras y bordes firmes */
    input, select, textarea, div[data-baseweb="input"] input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border: 2px solid #94a3b8 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
    
    .top-workbench-bar {
        background: #0f172a;
        color: #f8fafc;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 20px;
        border-left: 6px solid #2563eb;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }
    
    .metric-panel {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    .stat-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    
    .stat-danger { background: #fee2e2; color: #b91c1c; border: 1px solid #f87171; }
    .stat-success { background: #dcfce7; color: #15803d; border: 1px solid #4ade80; }
    
    .big-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 6px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- SELECTOR DE IDIOMA EN CABECERA ---
c_top1, c_top2 = st.columns([4, 1])
with c_top2:
    idioma = st.radio("Language / Idioma:", ["🇪🇸 Español", "🇬🇧 English"], horizontal=True, label_visibility="collapsed")
es_espanol = "Español" in idioma

# Textos bilingües
T_BADGE = "MOTOR MATEMÁTICO CNMC CIRCULAR 3/2020 ACTIVO" if es_espanol else "CNMC CIRCULAR 3/2020 MATHEMATICAL CORE ACTIVE"
T_TITULO = "⚡ OptiVolt Industrial | Energy Workbench"
T_SUB = "Auditoría Pericial de Término de Potencia, Maxímetros y Reactiva con Filtro de Armónicos" if es_espanol else "Power Capacity Optimization & Reactive Energy Harmonic Filtering Platform"
T_SOBRECOSTE = "SOBRECOSTE ACTUAL" if es_espanol else "CURRENT INVOICED COST"
T_OPTIMO = "COSTE TÉCNICO ÓPTIMO" if es_espanol else "OPTIMAL BOE CAPACITY COST"
T_AHORRO = "AHORRO NETO AUDITADO" if es_espanol else "NET AUDITED ANNUAL SAVINGS"

# --- VERIFICACIÓN DE LICENCIA ---
if "tipo_licencia" not in st.session_state:
    st.session_state.tipo_licencia = "ninguna"
if "cliente_email" not in st.session_state:
    st.session_state.cliente_email = ""

session_id_param = st.query_params.get("session_id")
if session_id_param and st.session_state.tipo_licencia == "ninguna":
    if stripe and stripe_key:
        try:
            sesion = stripe.checkout.Session.retrieve(session_id_param)
            if sesion.payment_status == "paid":
                st.session_state.tipo_licencia = "pagada"
                st.session_state.cliente_email = sesion.customer_details.email if sesion.customer_details else "Cliente Verificado"
                st.balloons()
                st.toast("🎉 Dictamen Oficial Desbloqueado." if es_espanol else "🎉 Official Dossier Unlocked.", icon="💎")
        except Exception:
            pass

def comprobar_email_stripe(email_test):
    limpio = email_test.strip().lower()
    if limpio in [e.lower() for e in ADMIN_EMAILS]:
        return True, "Acceso Maestro de Ingeniería Concedido"
    if not stripe or not stripe_key:
        return False, "Conexión a Stripe no configurada."
    try:
        clientes = stripe.Customer.list(email=limpio)
        if not clientes.data:
            return False, "Correo no registrado en Stripe."
        for c in clientes.data:
            cargos = stripe.Charge.list(customer=c.id, limit=5)
            for cargo in cargos.data:
                if cargo.paid and not cargo.refunded:
                    return True, "Licencia Dictamen CNMC Activa (39€)"
        return False, "No consta pago completado."
    except Exception as e:
        return False, f"Error: {e}"

# --- SINCRONIZACIÓN DE PRESETS ---
def cambiar_perfil():
    elec = st.session_state.selector_perfil
    d = PRESETS_DATA[elec]
    st.session_state.cups_in = d["cups"]
    st.session_state.tarifa_in = d["tarifa"]
    st.session_state.cos_phi_in = d["cos_phi"]
    st.session_state.p_media_in = d["p_media"]
    st.session_state.multa_in = d["multa_mes"]
    for i in range(6):
        st.session_state[f"p_act_{i}"] = float(d["p_act"][i])
        st.session_state[f"p_max_{i}"] = float(d["p_max"][i])

if "selector_perfil" not in st.session_state:
    st.session_state.selector_perfil = "Taller de Mecanizado y Estampación"
    cambiar_perfil()

# --- TOP WORKBENCH BAR ---
col_logo, col_preset = st.columns([2.6, 1.4])
with col_logo:
    st.markdown(f"""
    <div class="top-workbench-bar">
        <span class="stat-badge stat-success">{T_BADGE}</span>
        <h1 style="font-size: 2.2rem; margin: 8px 0 2px 0; color: #ffffff;">{T_TITULO}</h1>
        <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">{T_SUB}</p>
    </div>
    """, unsafe_allow_html=True)

with col_preset:
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.markdown("**📂 Cargar Escenario / Load Preset:**" if es_espanol else "**📂 Load Industrial Facility Preset:**")
    st.selectbox("Perfil de consumo:", list(PRESETS_DATA.keys()), key="selector_perfil", on_change=cambiar_perfil, label_visibility="collapsed")
    
    if st.session_state.tipo_licencia != "ninguna":
        st.markdown(f'<span class="stat-badge stat-success">🟢 EXPEDIENTE DESBLOQUEADO ({st.session_state.cliente_email})</span>', unsafe_allow_html=True)
    else:
        btn_txt = "⚡ Adquirir Dictamen Oficial (39 €)" if es_espanol else "⚡ Unlock Official Dossier (39 €)"
        st.markdown(f'<a href="{URL_STRIPE_39}" target="_blank" style="background:#2563eb; color:white; display:block; text-align:center; padding:8px; border-radius:6px; font-weight:bold; font-size:13px; text-decoration:none; margin-top:8px;">{btn_txt}</a>', unsafe_allow_html=True)
        with st.expander("¿Ya pagaste? Valida tu email" if es_espanol else "Already paid? Validate email"):
            mail_val = st.text_input("Email Stripe:")
            if st.button("Validar Licencia" if es_espanol else "Validate"):
                ok, msg = comprobar_email_stripe(mail_val)
                if ok:
                    st.session_state.tipo_licencia = "pagada"
                    st.session_state.cliente_email = mail_val.strip().lower()
                    st.rerun()
                else:
                    st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL CENTRAL DE DATOS Y GRÁFICAS ---
col_config, col_analisis = st.columns([1.1, 1.9])

with col_config:
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.subheader("1. Parámetros de Factura" if es_espanol else "1. Electricity Bill Parameters")
    
    cups = st.text_input("Código CUPS / Supply Point ID:", key="cups_in")
    tarifa = st.selectbox("Tarifa de Acceso / Grid Tariff:", list(PRECIOS_PEAJES.keys()), key="tarifa_in")
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        cos_phi = st.number_input("Factor Potencia (cos φ):", 0.50, 0.99, key="cos_phi_in", step=0.01)
        p_media = st.number_input("P. Activa Media (kW):" if es_espanol else "Mean Active Power (kW):", 5.0, 2000.0, key="p_media_in", step=5.0)
    with c_m2:
        multa_mes = st.number_input("Multa Reactiva (€/mes):" if es_espanol else "Reactive Surcharge (€/mo):", 0.0, 10000.0, key="multa_in", step=10.0)
        tension_sel = st.selectbox("Tensión Red / Voltage:", ["400 V (Baja Tensión)", "20 kV (Media Tensión)"])
    
    st.markdown("---")
    st.markdown("**Matriz de Potencias P1 a P6 (kW):**" if es_espanol else "**Capacity Matrix P1 to P6 (kW):**")
    
    p_act = []
    p_max = []
    for i in range(6):
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            p_act.append(st.number_input(f"P{i+1} Contratada", min_value=1.0, key=f"p_act_{i}", step=2.0))
        with c_p2:
            p_max.append(st.number_input(f"P{i+1} Maxímetro", min_value=1.0, key=f"p_max_{i}", step=1.0))
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- ALGORITMO BOE ---
def optimizar_potencias(maximetros, p_min=15.001):
    n = len(maximetros)
    p_res = [max(float(m), p_min) for m in maximetros]
    for i in range(1, n):
        if p_res[i] < p_res[i - 1]:
            p_res[i] = p_res[i - 1]
    return [round(p, 1) for p in p_res]

precios = PRECIOS_PEAJES[tarifa]
p_opt = optimizar_potencias(p_max, p_min=15.001 if "3.0TD" in tarifa else 450.0)

coste_act = sum([p * pr for p, pr in zip(p_act, precios)])
coste_opt = sum([p * pr for p, pr in zip(p_opt, precios)])
ahorro_pot = max(0.0, coste_act - coste_opt)
ahorro_react = multa_mes * 12
ahorro_total = ahorro_pot + ahorro_react

qc_kvar = 0.0
if cos_phi < 0.98:
    qc_kvar = round(p_media * (math.tan(math.acos(cos_phi)) - math.tan(math.acos(0.98))), 1)

with col_analisis:
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #dc2626;">
            <span class="stat-badge stat-danger">{T_SOBRECOSTE}</span>
            <div class="big-value" style="color:#dc2626;">{coste_act:,.2f} €</div>
            <span style="font-size:0.8rem; color:#64748b;">Gasto fijo anual sin auditar</span>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #2563eb;">
            <span class="stat-badge" style="background:#dbeafe; color:#1e40af;">{T_OPTIMO}</span>
            <div class="big-value" style="color:#2563eb;">{coste_opt:,.2f} €</div>
            <span style="font-size:0.8rem; color:#64748b;">Ajuste seguro con regla CNMC</span>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #16a34a;">
            <span class="stat-badge stat-success">{T_AHORRO}</span>
            <div class="big-value" style="color:#16a34a;">{ahorro_total:,.2f} €/año</div>
            <span style="font-size:0.8rem; color:#64748b;">Recuperación en primer trimestre</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.markdown("#### Balance de Curva de Potencias (P1 a P6)" if es_espanol else "#### Power Capacity Balance (P1 to P6)")
    
    tramos = ["P1", "P2", "P3", "P4", "P5", "P6"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tramos, y=p_act, name="Potencia Contratada Actual" if es_espanol else "Current Contracted Capacity", marker_color="#dc2626"))
    fig.add_trace(go.Bar(x=tramos, y=p_opt, name="Potencia Óptima (Regla BOE)" if es_espanol else "Optimal BOE Capacity", marker_color="#16a34a"))
    fig.add_trace(go.Scatter(x=tramos, y=p_max, name="Pico Real (Maxímetro)" if es_espanol else "Peak Recorded Demand", mode="lines+markers", line=dict(color="#0284c7", width=3, dash="dot")))
    
    fig.update_layout(
        barmode="group", height=300,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    meses = [f"Mes {m}" if es_espanol else f"Month {m}" for m in range(1, 13)]
    ahorro_mensual = ahorro_total / 12.0
    flujo_acumulado = [ahorro_mensual * m for m in range(1, 13)]
    
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Scatter(x=meses, y=flujo_acumulado, mode="lines+markers", name="Ahorro Acumulado en Caja (€)", line=dict(color="#16a34a", width=3), fill='tozeroy', fillcolor="rgba(22, 163, 74, 0.1)"))
    fig_roi.update_layout(
        title="Flujo de Caja Recuperado Acumulado a 12 Meses (€)" if es_espanol else "Cumulative 12-Month Cashflow Savings (€)",
        height=220, margin=dict(l=10, r=10, t=35, b=10)
    )
    st.plotly_chart(fig_roi, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- EXPEDIENTE DE 3 PÁGINAS ---
st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
st.subheader("2. Expediente Técnico Oficial de Reclamación (3 Páginas)" if es_espanol else "2. Official 3-Page Technical Claim Dossier")

es_pagado = st.session_state.tipo_licencia != "ninguna"

def compilar_informe_html(licenciado, en_espanol=True):
    blur = "" if licenciado else "filter: blur(6px); user-select: none; pointer-events: none;"
    
    filas_tabla = ""
    for i in range(6):
        ah = max(0.0, (p_act[i] - p_opt[i]) * precios[i])
        val_opt_str = f"{p_opt[i]:.1f} kW" if licenciado else "🔒 [BLOQUEADO / LOCKED]"
        filas_tabla += f"""
        <tr>
            <td style="padding:6px; border:1px solid #94a3b8; text-align:center;"><strong>P{i+1}</strong></td>
            <td style="padding:6px; border:1px solid #94a3b8; text-align:center;">{p_act[i]:.1f} kW</td>
            <td style="padding:6px; border:1px solid #94a3b8; text-align:center;">{p_max[i]:.1f} kW</td>
            <td style="padding:6px; border:1px solid #94a3b8; text-align:center; font-weight:bold; color:#0284c7;">{val_opt_str}</td>
            <td style="padding:6px; border:1px solid #94a3b8; text-align:center;">{precios[i]:.2f} €</td>
            <td style="padding:6px; border:1px solid #94a3b8; text-align:center; font-weight:bold; color:#16a34a;">{ah:,.2f} €</td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Expediente Pericial CNMC - {cups}</title>
        <style>
            @media print {{
                .no-print {{ display: none !important; }}
                body {{ font-size: 9.5pt; color: #000; }}
                .page-break {{ page-break-after: always; }}
                @page {{ margin: 15mm; size: A4 portrait; }}
            }}
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; max-width: 850px; margin: 10px auto; padding: 25px; color: #0f172a; line-height: 1.45; }}
            .header-exp {{ border-bottom: 2px solid #0f172a; padding-bottom: 8px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 8.5pt; }}
            th {{ background: #f1f5f9; padding: 7px; border: 1px solid #94a3b8; text-align: center; }}
            .btn-print {{ background: #2563eb; color: white; padding: 12px 24px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }}
            .box-legal {{ background: #f8fafc; border: 1.5px solid #cbd5e1; padding: 14px; border-radius: 6px; font-size: 8.5pt; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align:center; margin-bottom:20px; background:#f8fafc; padding:15px; border-radius:8px; border:1px solid #cbd5e1;">
            <button class="btn-print" onclick="window.print()">🖨️ {'Imprimir / Guardar Dictamen en PDF Oficial' if en_espanol else 'Print / Save Official PDF Dossier'}</button>
            <p style="font-size:12px; color:#64748b; margin-top:5px;">{'Destino en opciones de impresión: Guardar como PDF.' if en_espanol else 'Printer destination: Save as PDF.'}</p>
        </div>

        <!-- PÁGINA 1 -->
        <div class="header-exp">
            <h2 style="margin:0; font-size:15pt; color:#0f172a;">{'DICTAMEN PERICIAL DE ADECUACIÓN DE POTENCIAS DE ACCESO' if en_espanol else 'OFFICIAL EXPERT OPINION ON POWER CAPACITY ALLOCATION'}</h2>
            <p style="margin:2px 0; font-size:8.5pt; color:#64748b;">CONFORME A CIRCULAR 3/2020 CNMC, R.D. 1164/2001 Y LEY 24/2013 DEL SECTOR ELÉCTRICO</p>
            <p style="margin:2px 0; font-size:8pt; font-weight:bold;">REF REGISTRO: EXP-OPT-{cups[-6:]}-{datetime.date.today().strftime('%Y%m%d')}</p>
        </div>

        <p style="font-size:9pt;"><strong>{'PUNTO DE SUMINISTRO (CUPS)' if en_espanol else 'SUPPLY POINT ID (CUPS)'}:</strong> {cups}<br>
        <strong>{'TARIFA VIGENTE AUDITADA' if en_espanol else 'AUDITED TARIFF'}:</strong> {tarifa} | <strong>VOLTAGE:</strong> {tension_sel}</p>

        <h3 style="font-size:10.5pt; border-bottom: 1px solid #2563eb; padding-bottom: 2px;">1. {'REAJUSTE DE ESCALONES DE POTENCIA (P1 A P6)' if en_espanol else 'MONOTONIC CAPACITY ALLOCATION (P1 TO P6)'}</h3>
        <table>
            <thead>
                <tr><th>Tramo</th><th>P. Actual</th><th>Pico Registrado</th><th>P. Óptima CNMC</th><th>Peaje Acceso</th><th>Ahorro Anual</th></tr>
            </thead>
            <tbody>
                {filas_tabla}
            </tbody>
        </table>

        <div style="{blur}">
            <h3 style="font-size:10.5pt; border-bottom: 1px solid #2563eb; padding-bottom: 2px;">2. {'LIQUIDACIÓN ECONÓMICA DE AHORRO' if en_espanol else 'ECONOMIC SAVINGS BALANCE'}</h3>
            <p style="font-size:9pt;">
                - {'Reducción en Término Fijo de Potencia' if en_espanol else 'Annual Capacity Surcharges Reduction'}: <strong>{ahorro_pot:,.2f} €/año</strong><br>
                - {'Supresión íntegra del recargo por Reactiva' if en_espanol else 'Complete elimination of Reactive Power Penalties'}: <strong>{ahorro_react:,.2f} €/año</strong><br>
                <span style="font-size:11pt; color:#16a34a;"><strong>{'AHORRO TOTAL ANUAL CONSOLIDADO' if en_espanol else 'TOTAL NET ANNUAL SAVINGS'}: {ahorro_total:,.2f} €/año</strong></span>
            </p>

            <div class="page-break"></div>

            <!-- PÁGINA 2 -->
            <div class="header-exp">
                <h2 style="margin:0; font-size:14pt;">{'MEMORIA TÉCNICA DE COMPENSACIÓN REACTIVA Y FILTRADO' if en_espanol else 'REACTIVE POWER COMPENSATION & HARMONIC FILTER SPECIFICATION'}</h2>
                <p style="margin:2px 0; font-size:8pt; color:#64748b;">ANÁLISIS DE FACTOR DE POTENCIA Y PROTECCIÓN DE MÁQUINAS</p>
            </div>
            <p style="font-size:8.5pt; text-align:justify;">
                {'La instalación registra un factor de potencia de' if en_espanol else 'The plant operates at a power factor of'} <strong>cos φ = {cos_phi:.2f}</strong>, {'por debajo del límite reglamentario de 0,95 fijado por el Ministerio de Industria.' if en_espanol else 'triggering legal penalty surcharges under CNMC regulations.'}
            </p>
            <div class="box-legal">
                <strong>{'PRESCRIPCIÓN DE BATERÍA AUTOMÁTICA DE CONDENSADORES' if en_espanol else 'AUTOMATIC CAPACITOR BANK PRESCRIPTION'}:</strong><br>
                • <strong>{'Potencia Reactiva Requerida' if en_espanol else 'Required Reactive Power'}:</strong> {qc_kvar} kVAr (5 x {round(qc_kvar/5, 1) if qc_kvar > 0 else 0} kVAr).<br>
                • <strong>{'Filtro Anti-Armónicos Obligatorio' if en_espanol else 'Mandatory Anti-Harmonic Filter'}:</strong> {'Reactancias de Rechazo sintonizadas a 189 Hz (p = 7%) para blindar la instalación contra armónicos de 5º orden.' if en_espanol else 'Detuned reactors tuned at 189 Hz (p = 7%) to prevent destructive resonance from 5th harmonics.'}<br>
                • <strong>Factor de Potencia Final:</strong> cos φ = 0,98.
            </div>

            <div class="page-break"></div>

            <!-- PÁGINA 3 -->
            <div class="header-exp">
                <h2 style="margin:0; font-size:14pt;">{'SOLICITUD FORMAL VINCULANTE DE MODIFICACIÓN CONTRACTUAL' if en_espanol else 'FORMAL BINDING CAPACITY MODIFICATION PETITION'}</h2>
                <p style="margin:2px 0; font-size:8pt; color:#64748b;">DIRIGIDA AL DEPARTAMENTO DE CONTRATACIÓN Y PEAJES DE LA COMERCIALIZADORA</p>
            </div>
            <p style="font-size:8.5pt; text-align:justify;">
                {'A la atención del Departamento de Contratación de la Comercializadora del CUPS' if en_espanol else 'To the Contracting and Grid Tariffs Department of the Utility for CUPS'} <strong>{cups}</strong>:<br><br>
                {'El titular del contrato, al amparo de la Ley 24/2013 del Sector Eléctrico y la Circular 3/2020 de la CNMC, SOLICITA FORMALMENTE la adecuación inmediata de las potencias contratadas en el sistema de peajes a los siguientes escalones técnicos periciales:' if en_espanol else 'Pursuant to Spanish Electricity Act 24/2013 and CNMC Circular 3/2020, the contract holder formally petitions the immediate adjustment of contracted capacities to the following certified values:'}<br><br>
                <strong>P1: {p_opt[0]} kW | P2: {p_opt[1]} kW | P3: {p_opt[2]} kW | P4: {p_opt[3]} kW | P5: {p_opt[4]} kW | P6: {p_opt[5]} kW</strong>.<br><br>
                {'Se advierte que la empresa Distribuidora viene obligada por imperativo legal a admitir cualquier reajuste de potencia que cumpla la regla no decreciente, debiendo quedar regularizado en el siguiente ciclo de facturación.' if en_espanol else 'The grid distributor is legally bound to execute this capacity reallocation on the following billing cycle.'}
            </p>
            <div style="margin-top:50px; display:flex; justify-content:space-between;">
                <div style="width:45%; border-top:1px solid #000; padding-top:6px; text-align:center; font-size:8.5pt;">
                    <strong>{'Firma del Titular / Apoderado Legal' if en_espanol else 'Authorized Legal Representative Signature'}</strong>
                </div>
                <div style="width:45%; border-top:1px solid #000; padding-top:6px; text-align:center; font-size:8.5pt;">
                    <strong>{'Firma y Sello Auditor Energético' if en_espanol else 'Certified Energy Auditor Stamp'}</strong>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

html_expediente = compilar_informe_html(es_pagado, es_espanol)

col_exp1, col_exp2 = st.columns([1, 1])
with col_exp1:
    if es_pagado:
        st.success("✅ EXPEDIENTE TÉCNICO COMPLETO DESBLOQUEADO (3 PÁGINAS)" if es_espanol else "✅ FULL 3-PAGE OFFICIAL DOSSIER UNLOCKED")
        st.download_button(
            label="📥 Descargar Dictamen Oficial Completo (PDF / HTML)" if es_espanol else "📥 Download Official Claim Dossier (PDF / HTML)",
            data=html_expediente,
            file_name=f"Dictamen_Pericial_CNMC_{cups[-6:]}.html",
            mime="text/html",
            type="primary",
            use_container_width=True
        )
    else:
        st.warning("🔒 VISTA PREVIA PROTEGIDA: Los valores óptimos y el escrito formal están bloqueados." if es_espanol else "🔒 PREVIEW PROTECTED: Optimal capacity values and legal claims are locked.")
        st.markdown(f"""
        **{'¿Por qué abonar el dictamen de 39,00 €?' if es_espanol else 'Why purchase the 39.00 € technical opinion?'}**
        - {'Obtienes los 6 valores exactos de kW (P1 a P6) optimizados.' if es_espanol else 'Instant access to all 6 exact optimal capacities (P1 to P6).'}
        - {'Memoria técnica de la batería de condensadores de' if es_espanol else 'Engineering specification sheet for the'} **{qc_kvar} kVAr** {'con filtro de armónicos.' if es_espanol else 'capacitor bank with harmonic filtering.'}
        - {'Escrito legal listo para firmar ante Comercializadoras.' if es_espanol else 'Signable legal notification enforceable before power utilities.'}
        - **{'Garantía:' if es_espanol else 'ROI Guarantee:'}** {'Amortizado en menos de 5 días con el ahorro de' if es_espanol else 'Amortized in less than 5 days with the'} **{ahorro_total:,.2f} €/año**.
        """)
        btn_buy_txt = "💳 Desbloquear Dictamen Oficial Completo (39,00 €)" if es_espanol else "💳 Unlock Official Technical Dossier (39.00 €)"
        st.markdown(f'<a href="{URL_STRIPE_39}" target="_blank" style="background:#2563eb; color:white; display:block; text-align:center; padding:12px; border-radius:6px; font-weight:bold; font-size:15px; text-decoration:none; margin:10px 0;">{btn_buy_txt}</a>', unsafe_allow_html=True)
        st.caption("🔒 Transacción segura procesada mediante Stripe Checkout.")

with col_exp2:
    st.markdown("#### Estado del Expediente Pericial:" if es_espanol else "#### Technical Dossier Status:")
    st.metric("Ahorro Anual Proyectado" if es_espanol else "Projected Annual Savings", f"{ahorro_total:,.2f} €", delta=f"{ahorro_total/12:,.2f} € / mes")
    st.metric("Circular CNMC 3/2020", "AUDITORÍA CONFORME" if es_espanol else "COMPLIANT AUDIT", delta="Apto para tramitación" if es_espanol else "Ready for filing")

st.divider()
st.markdown("#### Vista Previa del Documento Oficial (Modo Teaser Anti-Copia Activo):" if es_espanol else "#### Official Document Preview (Anti-Copy Teaser Mode):")
st.components.v1.html(html_expediente, height=650, scrolling=True)
st.markdown('</div>', unsafe_allow_html=True)