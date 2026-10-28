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

# --- CLAVE SECRETA DE STRIPE SEGURA (LOCAL Y CLOUD) ---
try:
    stripe_key = st.secrets.get("STRIPE_SECRET_KEY", None)
except Exception:
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", None)

if stripe_key and stripe:
    stripe.api_key = stripe_key

ADMIN_EMAILS = ["alberto.lantaron@gmail.com", "albertterre.lantaron@gmail.com"]

# 👉 TUS DOS ENLACES DE STRIPE:
URL_STRIPE_39 = "https://buy.stripe.com/4gM9AV8hw6mG1dxaEC0Ny04"
URL_STRIPE_149 = "https://buy.stripe.com/9B67sNbtI6mG09t6om0Ny05"

# --- CONSTANTES TÉCNICAS (BOE / CIRCULAR 3/2020 CNMC) ---
PRECIOS_PEAJES = {
    "3.0TD": [15.42, 11.78, 5.26, 4.48, 3.19, 1.82],
    "6.1TD": [21.84, 17.52, 9.35, 7.82, 4.12, 2.38]
}

# --- ESTILOS VISUALES: TITANIUM WORKBENCH ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    .stApp {
        background-color: #f1f5f9;
        color: #0f172a;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
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
    .stat-purple { background: #f3e8ff; color: #7e22ce; border: 1px solid #d8b4fe; }
    
    .big-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- SELECTOR DE IDIOMA EN CABECERA ---
c_top1, c_top2 = st.columns([4, 1])
with c_top2:
    idioma = st.radio("Language / Idioma:", ["🇪🇸 Español", "🇬🇧 English"], horizontal=True, label_visibility="collapsed")
es_espanol = "Español" in idioma

# --- DICCIONARIO BILINGÜE COMPLETO ---
TEXTOS = {
    "badge_top": "MOTOR MATEMÁTICO CNMC CIRCULAR 3/2020 ACTIVO" if es_espanol else "CNMC CIRCULAR 3/2020 MATHEMATICAL CORE ACTIVE",
    "titulo": "⚡ OptiVolt Industrial | Energy Workbench",
    "subtitulo": "Auditoría Pericial de Término de Potencia, Maxímetros y Reactiva con Filtro de Armónicos" if es_espanol else "Quantitative Power Optimization (CNMC 3/2020) & Reactive Energy Harmonic Filtering Workbench",
    "cargar_caso": "📂 Cargar Escenario Industrial:" if es_espanol else "📂 Load Industrial Facility Preset:",
    "sec1_titulo": "1. Parámetros de Facturación del Suministro" if es_espanol else "1. Electricity Bill & Supply Point Parameters",
    "cups_lbl": "Código Unificado de Punto de Suministro (CUPS):" if es_espanol else "Supply Point Identification Code (CUPS):",
    "tarifa_lbl": "Tarifa de Acceso a Red:" if es_espanol else "Grid Access Tariff:",
    "cos_lbl": "Factor de Potencia en Factura (cos φ):" if es_espanol else "Current Invoiced Power Factor (cos φ):",
    "p_media_lbl": "Potencia Activa Media de Planta (kW):" if es_espanol else "Mean Active Operating Power (kW):",
    "multa_lbl": "Penalización Mensual de Reactiva (€/mes):" if es_espanol else "Monthly Reactive Surcharge (€/mo):",
    "tension_lbl": "Tensión de Conexión:" if es_espanol else "Grid Voltage Level:",
    "t_baja": "Baja Tensión (400V)" if es_espanol else "Low Voltage (400V)",
    "t_media": "Media Tensión (20kV)" if es_espanol else "Medium Voltage (20kV)",
    "matriz_lbl": "Matriz de Potencias P1 a P6 (kW):" if es_espanol else "Capacity Matrix P1 to P6 (kW):",
    "p_cont": "Contratada (kW)" if es_espanol else "Contracted (kW)",
    "p_max": "Maxímetro (kW)" if es_espanol else "Peak Demand (kW)",
    "kpi_act_title": "SOBRECOSTE ACTUAL" if es_espanol else "CURRENT INVOICED COST",
    "kpi_act_desc": "Gasto fijo anual sin auditar" if es_espanol else "Annual fixed grid toll cost",
    "kpi_opt_title": "COSTE TÉCNICO ÓPTIMO" if es_espanol else "OPTIMAL BOE CAPACITY COST",
    "kpi_opt_desc": "Ajuste seguro con regla CNMC" if es_espanol else "Safe adjustment under CNMC rule",
    "kpi_ahorro_title": "AHORRO NETO AUDITADO" if es_espanol else "NET AUDITED ANNUAL SAVINGS",
    "kpi_ahorro_desc": "Recuperación en primer trimestre" if es_espanol else "Payback in first quarter",
    "unit_year": "€/año" if es_espanol else "€/year",
    "unit_mo": "€/mes" if es_espanol else "€/mo",
    "chart1_title": "Balance de Curva de Potencias (P1 a P6)" if es_espanol else "Power Capacity Balance (P1 to P6)",
    "bar_act": "Potencia Contratada Actual" if es_espanol else "Current Contracted Capacity",
    "bar_opt": "Potencia Óptima (Regla BOE)" if es_espanol else "Optimal BOE Capacity",
    "scatter_max": "Pico Real (Maxímetro)" if es_espanol else "Peak Recorded Demand",
    "chart_xaxis": "Periodo Tarifario" if es_espanol else "Tariff Period",
    "chart_yaxis": "Potencia (kW)" if es_espanol else "Power (kW)",
    "chart2_title": "Flujo de Caja Recuperado Acumulado a 12 Meses (€)" if es_espanol else "12-Month Cumulative Cashflow Recovery (€)",
    "chart2_line": "Ahorro Acumulado en Caja (€)" if es_espanol else "Cumulative Cash Savings (€)",
    "sec2_title": "2. Expediente Técnico Oficial de Reclamación (3 Páginas)" if es_espanol else "2. Official 3-Page Technical Claim Dossier",
    "dossier_status": "Estado del Expediente Pericial:" if es_espanol else "Technical Dossier Status:",
    "proj_savings": "Ahorro Anual Proyectado" if es_espanol else "Projected Annual Savings",
    "audit_status": "AUDITORÍA CONFORME" if es_espanol else "COMPLIANT AUDIT",
    "audit_ready": "Apto para tramitación" if es_espanol else "Ready for filing",
    "preview_lbl": "Vista Previa del Documento Oficial (Modo Teaser Anti-Copia Activo):" if es_espanol else "Official Document Preview (Anti-Copy Teaser Mode):",
    "warn_unlicensed": "🔒 VISTA PREVIA PROTEGIDA: Selecciona tu modalidad de acceso:" if es_espanol else "🔒 PREVIEW PROTECTED: Choose your access license:",
    "plan_pyme_name": "PLAN EMPRESA / FÁBRICA" if es_espanol else "BUSINESS 2-CUPS PLAN",
    "plan_pyme_desc": "Hasta <strong>2 Suministros (CUPS)</strong><br>Borradores y revisiones ilimitadas" if es_espanol else "Up to <strong>2 Supply Points (CUPS)</strong><br>Unlimited revisions for your plants",
    "plan_pyme_btn": "Comprar Bono 2 CUPS (39,00 €)" if es_espanol else "Unlock 2-CUPS License (39.00 €)",
    "plan_pro_name": "PLAN CONSULTOR B2B" if es_espanol else "UNLIMITED CONSULTANT B2B",
    "plan_pro_desc": "<strong>INFINITOS CUPS</strong> de por vida<br>Para ingenierías, asesorías e instaladores" if es_espanol else "<strong>UNLIMITED CUPS</strong> lifetime access<br>For energy consultants & contractors",
    "plan_pro_btn": "Comprar Plan Ilimitado (149,00 €)" if es_espanol else "Unlock Unlimited Plan (149.00 €)",
    "btn_print_html": "🖨️ Imprimir / Guardar Dictamen en PDF Oficial" if es_espanol else "🖨️ Print / Save Official PDF Dossier",
    "print_hint": "Destino en opciones de impresión: Guardar como PDF." if es_espanol else "Printer destination: Save as PDF.",
    "doc_p1_title": "DICTAMEN PERICIAL DE ADECUACIÓN DE POTENCIAS DE ACCESO" if es_espanol else "OFFICIAL EXPERT OPINION ON POWER CAPACITY ALLOCATION",
    "doc_p1_sub": "CONFORME A CIRCULAR 3/2020 CNMC, R.D. 1164/2001 Y LEY 24/2013 DEL SECTOR ELÉCTRICO" if es_espanol else "PURSUANT TO CNMC CIRCULAR 3/2020, ROYAL DECREE 1164/2001 & ELECTRICITY SECTOR ACT 24/2013",
    "doc_ref": "REF REGISTRO:" if es_espanol else "REGISTRY REF:",
    "doc_date": "FECHA DE EMISIÓN:" if es_espanol else "DATE OF ISSUE:",
    "doc_cups_lbl": "PUNTO DE SUMINISTRO (CUPS):" if es_espanol else "POINT OF SUPPLY (CUPS):",
    "doc_tariff_lbl": "TARIFA VIGENTE AUDITADA:" if es_espanol else "AUDITED GRID TARIFF:",
    "doc_sec1_title": "1. REAJUSTE DE ESCALONES DE POTENCIA (P1 A P6)" if es_espanol else "1. CERTIFIED CAPACITY ALLOCATION MATRIX (P1 TO P6)",
    "doc_th_tramo": "Tramo" if es_espanol else "Period",
    "doc_th_pact": "P. Actual" if es_espanol else "Current Capacity",
    "doc_th_pmax": "Pico Registrado" if es_espanol else "Peak Recorded",
    "doc_th_popt": "P. Óptima CNMC" if es_espanol else "Optimal CNMC",
    "doc_th_peaje": "Peaje Acceso" if es_espanol else "Grid Toll Fee",
    "doc_th_ahorro": "Ahorro Anual" if es_espanol else "Annual Savings",
    "doc_sec2_title": "2. LIQUIDACIÓN ECONÓMICA DE AHORRO" if es_espanol else "2. CONSOLIDATED ANNUAL ECONOMIC BALANCE",
    "doc_save_pot": "- Reducción en Término Fijo de Potencia:" if es_espanol else "- Direct reduction in fixed capacity grid charges:",
    "doc_save_rea": "- Supresión íntegra del recargo por Reactiva:" if es_espanol else "- Complete elimination of reactive power surcharges:",
    "doc_save_tot": "AHORRO TOTAL ANUAL CONSOLIDADO:" if es_espanol else "TOTAL CERTIFIED ANNUAL SAVINGS:",
    "doc_p2_title": "MEMORIA TÉCNICA DE COMPENSACIÓN REACTIVA Y FILTRADO" if es_espanol else "TECHNICAL MEMORANDUM: REACTIVE POWER COMPENSATION & HARMONIC FILTERING",
    "doc_p2_sub": "ANÁLISIS DE FACTOR DE POTENCIA Y PROTECCIÓN DE MÁQUINAS" if es_espanol else "POWER FACTOR DIAGNOSTIC & INDUSTRIAL MOTOR PROTECTION",
    "doc_p2_txt": "La instalación registra un factor de potencia medio por debajo del límite reglamentario de 0,95 fijado por el Ministerio de Industria y la CNMC, devengando penalizaciones mensuales continuadas." if es_espanol else "The industrial facility currently records an average power factor falling below the regulatory threshold of 0.95 established by the Ministry of Industry and CNMC regulations, devenging recurring monthly penalties.",
    "doc_p2_box_title": "PRESCRIPCIÓN DE BATERÍA AUTOMÁTICA DE CONDENSADORES:" if es_espanol else "AUTOMATIC CAPACITOR BANK PRESCRIPTION:",
    "doc_p2_q_req": "• Potencia Reactiva Neta Requerida:" if es_espanol else "• Net Reactive Capacity Required:",
    "doc_p2_filter": "• Filtro Anti-Armónicos Obligatorio: Reactancias de Rechazo sintonizadas a 189 Hz (p = 7%) para blindar la instalación fabril contra resonancias de armónicos de 5º orden derivados de variadores y motores." if es_espanol else "• Mandatory Anti-Harmonic Filter: Mandatory incorporation of 189 Hz detuned harmonic filtering reactors (p = 7%) to shield industrial machinery and prevent destructive 5th harmonic resonance.",
    "doc_p2_cos_final": "• Factor de Potencia Final Estimado: cos φ = 0,98 (Supresión íntegra de multas en factura)." if es_espanol else "• Final Power Factor: cos φ = 0.98 (100% elimination of reactive penalties in utility invoices).",
    "doc_p3_title": "SOLICITUD FORMAL VINCULANTE DE MODIFICACIÓN CONTRACTUAL" if es_espanol else "BINDING FORMAL REQUEST FOR CONTRACTUAL CAPACITY ADJUSTMENT",
    "doc_p3_sub": "DIRIGIDA AL DEPARTAMENTO DE CONTRATACIÓN Y PEAJES DE LA COMERCIALIZADORA" if es_espanol else "ADDRESSED TO THE CONTRACTING AND GRID TARIFFS DEPARTMENT OF THE ELECTRIC UTILITY",
    "doc_p3_dest": "A la atención del Departamento de Contratación de la Comercializadora del punto de suministro CUPS" if es_espanol else "To the attention of the Contracting and Tariffs Department of the Electricity Supplier for point of supply CUPS",
    "doc_p3_legal": "El titular del contrato, al amparo de la Ley 24/2013 del Sector Eléctrico, el Real Decreto 1164/2001 y la Circular 3/2020 de la CNMC, SOLICITA FORMALMENTE la adecuación inmediata de las potencias contratadas en el sistema de peajes a los siguientes escalones técnicos periciales crecientes:" if es_espanol else "The contract holder, pursuant to Royal Decree 1164/2001, Electricity Sector Act 24/2013, and Circular 3/2020 of the National Commission on Markets and Competition (CNMC), HEREBY FORMALLY PETITIONS the immediate adjustment of contracted capacities across all 6 time periods to the following certified optimal values:",
    "doc_p3_mandate": "Se advierte que la empresa Distribuidora viene obligada por imperativo legal a admitir cualquier reajuste de potencia que cumpla la regla no decreciente (P1 ≤ P2 ≤ P3 ≤ P4 ≤ P5 ≤ P6), debiendo quedar regularizado en el ciclo de facturación inmediatamente posterior." if es_espanol else "Notice is hereby served that the Distribution Utility is legally mandated to execute any capacity adjustment meeting the non-decreasing rule (P1 <= P2 <= P3 <= P4 <= P5 <= P6), enforceable from the billing cycle immediately following receipt of this official technical memorandum.",
    "doc_sign_client": "Firma del Titular / Apoderado Legal" if es_espanol else "Authorized Company Representative Signature / Stamp",
    "doc_sign_auditor": "Firma y Sello Auditor Energético" if es_espanol else "Certified Energy Auditor Signature & Official Stamp",
    "meses": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"] if es_espanol else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
}

# --- PRESETS DE PRUEBA (PERSONALIZADO SIEMPRE PRIMERO) ---
PRESETS_DATA = {
    ("Personalizado (Mis datos de factura)" if es_espanol else "Custom Facility (My Invoice Data)"): {
        "tarifa": "3.0TD", "p_act": [60.0, 60.0, 60.0, 60.0, 60.0, 60.0],
        "p_max": [38.0, 42.0, 32.0, 28.0, 20.0, 16.0],
        "cos_phi": 0.84, "p_media": 32.0, "multa_mes": 130.0, "cups": "ES0022000033445566CD1P"
    },
    ("Ejemplo 1: Taller Mecanizado" if es_espanol else "Demo 1: CNC Metalworking Facility"): {
        "tarifa": "3.0TD", "p_act": [90.0, 90.0, 90.0, 90.0, 90.0, 90.0],
        "p_max": [54.0, 58.0, 44.0, 36.0, 26.0, 22.0],
        "cos_phi": 0.78, "p_media": 48.0, "multa_mes": 240.0, "cups": "ES0021000045127891QZ1P"
    },
    ("Ejemplo 2: Planta Inyección de Plásticos" if es_espanol else "Demo 2: Plastic Injection Plant"): {
        "tarifa": "3.0TD", "p_act": [140.0, 140.0, 140.0, 140.0, 140.0, 140.0],
        "p_max": [102.0, 108.0, 88.0, 78.0, 62.0, 50.0],
        "cos_phi": 0.81, "p_media": 85.0, "multa_mes": 310.0, "cups": "ES0031000088992211MN1P"
    }
}

# --- GESTIÓN DE LICENCIAS ---
if "tipo_licencia" not in st.session_state:
    st.session_state.tipo_licencia = "ninguna"
if "cliente_email" not in st.session_state:
    st.session_state.cliente_email = ""
if "cups_registrados" not in st.session_state:
    st.session_state.cups_registrados = []

session_id_param = st.query_params.get("session_id")
if session_id_param and st.session_state.tipo_licencia == "ninguna":
    if stripe and stripe_key:
        try:
            sesion = stripe.checkout.Session.retrieve(session_id_param)
            if sesion.payment_status == "paid":
                monto_pagado = sesion.amount_total or 0
                if monto_pagado >= 10000:
                    st.session_state.tipo_licencia = "consultor"
                    msg_toast = "🎉 ¡Plan Consultor Ilimitado Activado!" if es_espanol else "🎉 Unlimited Consultant License Activated!"
                else:
                    st.session_state.tipo_licencia = "pyme"
                    msg_toast = "🎉 ¡Bono Empresa 2 CUPS Activado!" if es_espanol else "🎉 2-CUPS Business License Activated!"
                
                st.session_state.cliente_email = sesion.customer_details.email if sesion.customer_details else "Verified Customer"
                st.balloons()
                st.toast(msg_toast, icon="💎")
        except Exception:
            pass

def comprobar_email_stripe(email_test):
    limpio = email_test.strip().lower()
    if limpio in [e.lower() for e in ADMIN_EMAILS]:
        return True, "consultor", "Master Access (Unlimited)" if not es_espanol else "Acceso Maestro (Ilimitado)"
    if not stripe or not stripe_key:
        return False, "ninguna", "Stripe key not configured." if not es_espanol else "Clave Stripe no configurada."
    try:
        clientes = stripe.Customer.list(email=limpio)
        if not clientes.data:
            return False, "ninguna", "Email not registered in Stripe." if not es_espanol else "Correo no registrado en Stripe."
        
        tipo_encontrado = "ninguna"
        for c in clientes.data:
            cargos = stripe.Charge.list(customer=c.id, limit=10)
            for cargo in cargos.data:
                if cargo.paid and not cargo.refunded:
                    if cargo.amount >= 10000:
                        return True, "consultor", "Active Unlimited Consultant License (149€)" if not es_espanol else "Licencia Consultor Ilimitada Activa (149€)"
                    elif cargo.amount >= 3000:
                        tipo_encontrado = "pyme"
        
        if tipo_encontrado == "pyme":
            return True, "pyme", "Active 2-CUPS Business License (39€)" if not es_espanol else "Licencia Empresa Activa (Bono 2 CUPS - 39€)"
            
        return False, "ninguna", "No completed payments found." if not es_espanol else "No constan pagos completados."
    except Exception as e:
        return False, "ninguna", f"Error: {e}"

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

lista_presets = list(PRESETS_DATA.keys())
if "selector_perfil" not in st.session_state or st.session_state.selector_perfil not in lista_presets:
    st.session_state.selector_perfil = lista_presets[0]
    cambiar_perfil()

# --- TOP WORKBENCH BAR ---
col_logo, col_preset = st.columns([2.6, 1.4])
with col_logo:
    st.markdown(f"""
    <div class="top-workbench-bar">
        <span class="stat-badge stat-success">{TEXTOS['badge_top']}</span>
        <h1 style="font-size: 2.2rem; margin: 8px 0 2px 0; color: #ffffff;">{TEXTOS['titulo']}</h1>
        <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">{TEXTOS['subtitulo']}</p>
    </div>
    """, unsafe_allow_html=True)

with col_preset:
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.markdown(f"**{TEXTOS['cargar_caso']}**")
    st.selectbox("Perfil:", lista_presets, key="selector_perfil", on_change=cambiar_perfil, label_visibility="collapsed")
    
    es_admin = st.session_state.cliente_email.lower() in [e.lower() for e in ADMIN_EMAILS]
    
    if st.session_state.tipo_licencia == "consultor" or es_admin:
        st.markdown(f'<span class="stat-badge stat-purple">👑 PLAN CONSULTOR ILIMITADO ({st.session_state.cliente_email})</span>' if es_espanol else f'<span class="stat-badge stat-purple">👑 UNLIMITED CONSULTANT ({st.session_state.cliente_email})</span>', unsafe_allow_html=True)
    elif st.session_state.tipo_licencia == "pyme":
        n_cups = len(st.session_state.cups_registrados)
        st.markdown(f'<span class="stat-badge stat-success">🟢 PLAN EMPRESA ({n_cups}/2 CUPS)</span>' if es_espanol else f'<span class="stat-badge stat-success">🟢 BUSINESS PLAN ({n_cups}/2 CUPS)</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="stat-badge stat-danger">🔒 MODO EVALUACIÓN</span>' if es_espanol else f'<span class="stat-badge stat-danger">🔒 EVALUATION MODE</span>', unsafe_allow_html=True)
        with st.expander("¿Ya pagaste? Valida tu email" if es_espanol else "Already paid? Validate email"):
            mail_val = st.text_input("Email Stripe:")
            if st.button("Validar Licencia" if es_espanol else "Validate License"):
                ok, tipo, msg = comprobar_email_stripe(mail_val)
                if ok:
                    st.session_state.tipo_licencia = tipo
                    st.session_state.cliente_email = mail_val.strip().lower()
                    st.rerun()
                else:
                    st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PANEL CENTRAL: FORMULARIO Y GRÁFICAS ---
col_config, col_analisis = st.columns([1.1, 1.9])

with col_config:
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.subheader(TEXTOS['sec1_titulo'])
    
    cups = st.text_input(TEXTOS['cups_lbl'], key="cups_in").strip().upper()
    tarifa = st.selectbox(TEXTOS['tarifa_lbl'], ["3.0TD", "6.1TD"], key="tarifa_in")
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        cos_phi = st.number_input(TEXTOS['cos_lbl'], 0.50, 0.99, key="cos_phi_in", step=0.01)
        p_media = st.number_input(TEXTOS['p_media_lbl'], 5.0, 2000.0, key="p_media_in", step=5.0)
    with c_m2:
        multa_mes = st.number_input(TEXTOS['multa_lbl'], 0.0, 10000.0, key="multa_in", step=10.0)
        tension_sel = st.selectbox(TEXTOS['tension_lbl'], [TEXTOS['t_baja'], TEXTOS['t_media']])
    
    st.markdown("---")
    st.markdown(f"**{TEXTOS['matriz_lbl']}**")
    
    p_act = []
    p_max = []
    for i in range(6):
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            p_act.append(st.number_input(f"P{i+1} {TEXTOS['p_cont']}", min_value=1.0, key=f"p_act_{i}", step=2.0))
        with c_p2:
            p_max.append(st.number_input(f"P{i+1} {TEXTOS['p_max']}", min_value=1.0, key=f"p_max_{i}", step=1.0))
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- ALGORITMO BOE (RECALCULA EN TIEMPO REAL CON LOS NÚMEROS DE LAS CASILLAS) ---
def optimizar_potencias(maximetros, p_min=15.001):
    n = len(maximetros)
    p_res = [max(float(m), p_min) for m in maximetros]
    for i in range(1, n):
        if p_res[i] < p_res[i - 1]:
            p_res[i] = p_res[i - 1]
    return [round(p, 1) for p in p_res]

precios = PRECIOS_PEAJES[tarifa]
p_opt = optimizar_potencias(p_max, p_min=15.001 if tarifa == "3.0TD" else 450.0)

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
            <span class="stat-badge stat-danger">{TEXTOS['kpi_act_title']}</span>
            <div class="big-value" style="color:#dc2626;">{coste_act:,.2f} €</div>
            <span style="font-size:0.8rem; color:#64748b;">{TEXTOS['kpi_act_desc']}</span>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #2563eb;">
            <span class="stat-badge" style="background:#dbeafe; color:#1e40af;">{TEXTOS['kpi_opt_title']}</span>
            <div class="big-value" style="color:#2563eb;">{coste_opt:,.2f} €</div>
            <span style="font-size:0.8rem; color:#64748b;">{TEXTOS['kpi_opt_desc']}</span>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-panel" style="border-left: 5px solid #16a34a;">
            <span class="stat-badge stat-success">{TEXTOS['kpi_ahorro_title']}</span>
            <div class="big-value" style="color:#16a34a;">{ahorro_total:,.2f} {TEXTOS['unit_year']}</div>
            <span style="font-size:0.8rem; color:#64748b;">{TEXTOS['kpi_ahorro_desc']}</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
    st.markdown(f"#### {TEXTOS['chart1_title']}")
    
    tramos = ["P1", "P2", "P3", "P4", "P5", "P6"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tramos, y=p_act, name=TEXTOS['bar_act'], marker_color="#dc2626"))
    fig.add_trace(go.Bar(x=tramos, y=p_opt, name=TEXTOS['bar_opt'], marker_color="#16a34a"))
    fig.add_trace(go.Scatter(x=tramos, y=p_max, name=TEXTOS['scatter_max'], mode="lines+markers", line=dict(color="#0284c7", width=3, dash="dot")))
    
    fig.update_layout(
        xaxis_title=TEXTOS['chart_xaxis'],
        yaxis_title=TEXTOS['chart_yaxis'],
        barmode="group", height=290,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    flujo_acumulado = [(ahorro_total / 12.0) * m for m in range(1, 13)]
    
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Scatter(x=TEXTOS['meses'], y=flujo_acumulado, mode="lines+markers", name=TEXTOS['chart2_line'], line=dict(color="#16a34a", width=3), fill='tozeroy', fillcolor="rgba(22, 163, 74, 0.1)"))
    fig_roi.update_layout(
        title=TEXTOS['chart2_title'],
        height=210, margin=dict(l=10, r=10, t=35, b=10)
    )
    st.plotly_chart(fig_roi, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONTROL DE ACCESO POR LICENCIA ---
tipo_lic = st.session_state.tipo_licencia
cups_valido = False

if tipo_lic == "consultor" or es_admin:
    cups_valido = True
elif tipo_lic == "pyme":
    if cups in st.session_state.cups_registrados:
        cups_valido = True
    elif len(st.session_state.cups_registrados) < 2:
        st.session_state.cups_registrados.append(cups)
        cups_valido = True
    else:
        cups_valido = False
else:
    cups_valido = False

# --- EXPEDIENTE DE 3 PÁGINAS Y VENTA ---
st.markdown('<div class="metric-panel">', unsafe_allow_html=True)
st.subheader(TEXTOS['sec2_title'])

def compilar_informe_html(desbloqueado, en_espanol=True):
    blur = "" if desbloqueado else "filter: blur(6px); user-select: none; pointer-events: none;"
    
    filas_tabla = ""
    for i in range(6):
        ah = max(0.0, (p_act[i] - p_opt[i]) * precios[i])
        val_opt_str = f"{p_opt[i]:.1f} kW" if desbloqueado else "🔒 [BLOQUEADO]" if en_espanol else "🔒 [LOCKED]"
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
        <title>{TEXTOS['doc_p1_title']} - {cups}</title>
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
            <button class="btn-print" onclick="window.print()">{TEXTOS['btn_print_html']}</button>
            <p style="font-size:12px; color:#64748b; margin-top:5px;">{TEXTOS['print_hint']}</p>
        </div>

        <!-- PÁGINA 1 -->
        <div class="header-exp">
            <h2 style="margin:0; font-size:15pt; color:#0f172a;">{TEXTOS['doc_p1_title']}</h2>
            <p style="margin:2px 0; font-size:8.5pt; color:#64748b;">{TEXTOS['doc_p1_sub']}</p>
            <p style="margin:2px 0; font-size:8pt; font-weight:bold;">{TEXTOS['doc_ref']} EXP-OPT-{cups[-6:] if len(cups)>=6 else 'GEN'}-{datetime.date.today().strftime('%Y%m%d')}</p>
        </div>

        <p style="font-size:9pt;"><strong>{TEXTOS['doc_cups_lbl']}</strong> {cups}<br>
        <strong>{TEXTOS['doc_tariff_lbl']}</strong> {tarifa} | <strong>VOLTAGE:</strong> {tension_sel}</p>

        <h3 style="font-size:10.5pt; border-bottom: 1px solid #2563eb; padding-bottom: 2px;">{TEXTOS['doc_sec1_title']}</h3>
        <table>
            <thead>
                <tr>
                    <th>{TEXTOS['doc_th_tramo']}</th>
                    <th>{TEXTOS['doc_th_pact']}</th>
                    <th>{TEXTOS['doc_th_pmax']}</th>
                    <th>{TEXTOS['doc_th_popt']}</th>
                    <th>{TEXTOS['doc_th_peaje']}</th>
                    <th>{TEXTOS['doc_th_ahorro']}</th>
                </tr>
            </thead>
            <tbody>
                {filas_tabla}
            </tbody>
        </table>

        <div style="{blur}">
            <h3 style="font-size:10.5pt; border-bottom: 1px solid #2563eb; padding-bottom: 2px;">{TEXTOS['doc_sec2_title']}</h3>
            <p style="font-size:9pt;">
                {TEXTOS['doc_save_pot']} <strong>{ahorro_pot:,.2f} {TEXTOS['unit_year']}</strong><br>
                {TEXTOS['doc_save_rea']} <strong>{ahorro_react:,.2f} {TEXTOS['unit_year']}</strong><br>
                <span style="font-size:11pt; color:#16a34a;"><strong>{TEXTOS['doc_save_tot']} {ahorro_total:,.2f} {TEXTOS['unit_year']}</strong></span>
            </p>

            <div class="page-break"></div>

            <!-- PÁGINA 2 -->
            <div class="header-exp">
                <h2 style="margin:0; font-size:14pt;">{TEXTOS['doc_p2_title']}</h2>
                <p style="margin:2px 0; font-size:8pt; color:#64748b;">{TEXTOS['doc_p2_sub']}</p>
            </div>
            <p style="font-size:8.5pt; text-align:justify;">
                {TEXTOS['doc_p2_txt']}
            </p>
            <div class="box-legal">
                <strong>{TEXTOS['doc_p2_box_title']}</strong><br>
                {TEXTOS['doc_p2_q_req']} <strong>{qc_kvar} kVAr</strong> (5 x {round(qc_kvar/5, 1) if qc_kvar > 0 else 0} kVAr).<br>
                {TEXTOS['doc_p2_filter']}<br>
                {TEXTOS['doc_p2_cos_final']}
            </div>

            <div class="page-break"></div>

            <!-- PÁGINA 3 -->
            <div class="header-exp">
                <h2 style="margin:0; font-size:14pt;">{TEXTOS['doc_p3_title']}</h2>
                <p style="margin:2px 0; font-size:8pt; color:#64748b;">{TEXTOS['doc_p3_sub']}</p>
            </div>
            <p style="font-size:8.5pt; text-align:justify;">
                {TEXTOS['doc_p3_dest']} <strong>{cups}</strong>:<br><br>
                {TEXTOS['doc_p3_legal']}<br><br>
                <strong>P1: {p_opt[0]} kW | P2: {p_opt[1]} kW | P3: {p_opt[2]} kW | P4: {p_opt[3]} kW | P5: {p_opt[4]} kW | P6: {p_opt[5]} kW</strong>.<br><br>
                {TEXTOS['doc_p3_mandate']}
            </p>
            <div style="margin-top:50px; display:flex; justify-content:space-between;">
                <div style="width:45%; border-top:1px solid #000; padding-top:6px; text-align:center; font-size:8.5pt;">
                    <strong>{TEXTOS['doc_sign_client']}</strong>
                </div>
                <div style="width:45%; border-top:1px solid #000; padding-top:6px; text-align:center; font-size:8.5pt;">
                    <strong>{TEXTOS['doc_sign_auditor']}</strong>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

html_expediente = compilar_informe_html(cups_valido, es_espanol)

col_exp1, col_exp2 = st.columns([1.1, 0.9])
with col_exp1:
    if cups_valido:
        txt_ok = f"✅ DICTAMEN OFICIAL DESBLOQUEADO (CUPS: {cups})" if es_espanol else f"✅ OFFICIAL DOSSIER UNLOCKED (CUPS: {cups})"
        st.success(txt_ok)
        st.download_button(
            label="📥 Descargar Dictamen Oficial Completo (PDF / HTML)" if es_espanol else "📥 Download Official Claim Dossier (PDF / HTML)",
            data=html_expediente,
            file_name=f"Dictamen_Pericial_CNMC_{cups[-6:] if len(cups)>=6 else 'GEN'}.html",
            mime="text/html",
            type="primary",
            use_container_width=True
        )
        st.caption(TEXTOS['print_hint'])
    elif tipo_lic == "pyme" and not cups_valido:
        st.warning("⚠️ LÍMITE DE LICENCIA ALCANZADO (2/2 CUPS)" if es_espanol else "⚠️ LICENSE LIMIT REACHED (2/2 CUPS USED)")
        st.write(f"Suministros autorizados / Authorized points: `{st.session_state.cups_registrados}`.")
        st.info("Pasa al Plan Consultor para auditar infinitos CUPS o adquiere un nuevo bono." if es_espanol else "Upgrade to the Unlimited Consultant Plan to audit unlimited CUPS.")
        st.markdown(f'<a href="{URL_STRIPE_149}" target="_blank" style="background:#7e22ce; color:white; display:block; text-align:center; padding:12px; border-radius:6px; font-weight:bold; font-size:14px; text-decoration:none; margin-bottom:8px;">{TEXTOS["plan_pro_btn"]}</a>', unsafe_allow_html=True)
        st.markdown(f'<a href="{URL_STRIPE_39}" target="_blank" style="background:#2563eb; color:white; display:block; text-align:center; padding:10px; border-radius:6px; font-weight:bold; font-size:13px; text-decoration:none;">{TEXTOS["plan_pyme_btn"]}</a>', unsafe_allow_html=True)
    else:
        st.warning(TEXTOS['warn_unlicensed'])
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"""
            <div style="background:#f8fafc; border:2px solid #2563eb; padding:15px; border-radius:8px; text-align:center;">
                <span class="stat-badge stat-success">{TEXTOS['plan_pyme_name']}</span>
                <h2 style="margin:6px 0; color:#0f172a;">39,00 €</h2>
                <p style="font-size:0.8rem; color:#64748b; margin-bottom:10px;">{TEXTOS['plan_pyme_desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f'<a href="{URL_STRIPE_39}" target="_blank" style="background:#2563eb; color:white; display:block; text-align:center; padding:10px; border-radius:6px; font-weight:bold; font-size:13px; text-decoration:none; margin-top:8px;">{TEXTOS["plan_pyme_btn"]}</a>', unsafe_allow_html=True)

        with col_p2:
            st.markdown(f"""
            <div style="background:#f8fafc; border:2px solid #7e22ce; padding:15px; border-radius:8px; text-align:center;">
                <span class="stat-badge stat-purple">{TEXTOS['plan_pro_name']}</span>
                <h2 style="margin:6px 0; color:#0f172a;">149,00 €</h2>
                <p style="font-size:0.8rem; color:#64748b; margin-bottom:10px;">{TEXTOS['plan_pro_desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f'<a href="{URL_STRIPE_149}" target="_blank" style="background:#7e22ce; color:white; display:block; text-align:center; padding:10px; border-radius:6px; font-weight:bold; font-size:13px; text-decoration:none; margin-top:8px;">{TEXTOS["plan_pro_btn"]}</a>', unsafe_allow_html=True)

with col_exp2:
    st.markdown(f"#### {TEXTOS['dossier_status']}")
    st.metric(TEXTOS['proj_savings'], f"{ahorro_total:,.2f} {TEXTOS['unit_year']}", delta=f"{ahorro_total/12:,.2f} {TEXTOS['unit_mo']}")
    st.metric("Circular CNMC 3/2020", TEXTOS['audit_status'], delta=TEXTOS['audit_ready'])

st.divider()
st.markdown(f"#### {TEXTOS['preview_lbl']}")
st.components.v1.html(html_expediente, height=650, scrolling=True)
st.markdown('</div>', unsafe_allow_html=True)