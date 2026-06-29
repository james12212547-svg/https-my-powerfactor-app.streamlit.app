import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import json
import io
from google import genai
from google.genai import types

# Import our modularized backend logic
from src.engineering import (
    calculate_q_and_c, check_harmonic_resonance,
    calculate_detail_engineering, calculate_cap_steps,
    analyze_harmonics_ieee519
)
from src.financial import calculate_roi, generate_boq
from src.data_loader import process_load_profile
from src.pdf_generator import generate_report

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="PFC Pro Analyzer | ระบบวิเคราะห์ Power Factor", layout="wide", page_icon="⚡")

# Google Fonts — ต้องแยกออกจาก <style> block เพื่อให้ Streamlit render ถูกต้อง
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">',
    unsafe_allow_html=True
)

# MASTER CSS — Modern Glassmorphism + Cyber-SCADA Theme
st.markdown("""
<style>
/* Global */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* App background */
.stApp {
    background: linear-gradient(135deg, #020b18 0%, #050f1f 40%, #071428 70%, #030d1a 100%) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #05111f 0%, #071624 100%) !important;
    border-right: 1px solid rgba(0,200,255,0.12) !important;
}
[data-testid="stSidebar"] * { color: #a8c8e8 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #00c8ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-bottom: 1px solid rgba(0,200,255,0.2) !important;
    padding-bottom: 6px !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stSidebar"] label { color: #7eb8d4 !important; font-size: 0.82rem !important; }

/* Main padding */
[data-testid="stMainBlockContainer"] { padding: 1.5rem 2rem !important; }

/* Tabs — Scrollable horizontal tab bar */
[data-testid="stTabs"] > div:first-child {
    background: rgba(0,200,255,0.04);
    border-radius: 12px 12px 0 0;
    border-bottom: 1px solid rgba(0,200,255,0.15);
    padding: 4px 8px 0;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
    scrollbar-color: rgba(0,200,255,0.35) transparent;
    white-space: nowrap;
    display: flex !important;
    flex-wrap: nowrap !important;
}
[data-testid="stTabs"] > div:first-child::-webkit-scrollbar {
    height: 3px;
}
[data-testid="stTabs"] > div:first-child::-webkit-scrollbar-track {
    background: transparent;
}
[data-testid="stTabs"] > div:first-child::-webkit-scrollbar-thumb {
    background: rgba(0,200,255,0.35);
    border-radius: 4px;
}
[data-testid="stTabs"] button {
    color: #5a8aa0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    border-radius: 8px 8px 0 0 !important;
    border: none !important;
    background: transparent !important;
    padding: 8px 14px !important;
    transition: all 0.2s ease;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
}
[data-testid="stTabs"] button:hover { color: #00c8ff !important; background: rgba(0,200,255,0.08) !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00c8ff !important;
    background: rgba(0,200,255,0.12) !important;
    border-bottom: 2px solid #00c8ff !important;
}


/* Section headers */
h2, h3 {
    font-family: 'JetBrains Mono', monospace !important;
    color: #00c8ff !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    border-bottom: 1px solid rgba(0,200,255,0.2) !important;
    padding-bottom: 6px !important;
    margin-top: 1.5rem !important;
}

/* st.metric fallback */
[data-testid="stMetric"] {
    background: rgba(0,200,255,0.04) !important;
    border: 1px solid rgba(0,200,255,0.12) !important;
    border-left: 3px solid #00c8ff !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] p {
    color: #5a8aa0 !important;
    font-size: 0.72rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
[data-testid="stMetricValue"] div {
    color: #00ffcc !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.3rem !important;
    font-weight: 700;
}

/* Alert boxes */
[data-testid="stAlert"] { border-radius: 10px !important; border-left-width: 4px !important; }

/* Expander */
[data-testid="stExpander"] {
    background: rgba(0,200,255,0.03) !important;
    border: 1px solid rgba(0,200,255,0.12) !important;
    border-radius: 10px !important;
}

/* Buttons */
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, rgba(0,200,255,0.15), rgba(0,100,200,0.2)) !important;
    border: 1px solid rgba(0,200,255,0.35) !important;
    color: #00c8ff !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    transition: all 0.25s ease;
}
[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg, rgba(0,200,255,0.3), rgba(0,100,200,0.4)) !important;
    box-shadow: 0 0 20px rgba(0,200,255,0.3) !important;
    transform: translateY(-1px);
}

/* Divider */
hr { border-color: rgba(0,200,255,0.15) !important; }

/* Table */
[data-testid="stTable"] table {
    background: rgba(0,15,30,0.6) !important;
    border-radius: 10px;
    border: 1px solid rgba(0,200,255,0.12);
}
[data-testid="stTable"] thead tr { background: rgba(0,200,255,0.08) !important; }
[data-testid="stTable"] th { color: #00c8ff !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; }
[data-testid="stTable"] td { color: #a8c8e8 !important; font-size: 0.82rem !important; border-color: rgba(0,200,255,0.06) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #020b18; }
::-webkit-scrollbar-thumb { background: rgba(0,200,255,0.25); border-radius: 4px; }

/* Chat */
[data-testid="stChatMessage"] {
    background: rgba(0,200,255,0.04) !important;
    border: 1px solid rgba(0,200,255,0.1) !important;
    border-radius: 12px !important;
}
[data-testid="stChatInputContainer"] {
    background: rgba(0,15,30,0.8) !important;
    border: 1px solid rgba(0,200,255,0.25) !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)


# ── Hero Header ──

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(0,200,255,0.06) 0%, rgba(0,50,120,0.12) 50%, rgba(0,200,255,0.04) 100%);
    border: 1px solid rgba(0,200,255,0.18);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    backdrop-filter: blur(12px);
    position: relative;
    overflow: hidden;
">
  <div style="position:absolute;top:0;right:0;width:300px;height:100%;background:radial-gradient(ellipse at right,rgba(0,200,255,0.06),transparent 70%);pointer-events:none;"></div>
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
    <span style="font-size:2.5rem;">⚡</span>
    <div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:1.35rem;font-weight:700;color:#00c8ff;letter-spacing:1px;">PFC PRO ANALYZER</div>
      <div style="font-family:'Inter',sans-serif;font-size:0.85rem;color:#5a8aa0;margin-top:2px;">ระบบวิเคราะห์และออกแบบ Power Factor ขั้นสูง · Detail Engineering Design · AI-Powered</div>
    </div>
    <div style="margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;">
      <span style="background:rgba(0,255,100,0.12);border:1px solid rgba(0,255,100,0.3);color:#00ff64;font-family:'JetBrains Mono',monospace;font-size:0.65rem;padding:4px 10px;border-radius:20px;font-weight:600;letter-spacing:0.5px;">● LIVE</span>
      <span style="background:rgba(0,200,255,0.1);border:1px solid rgba(0,200,255,0.25);color:#00c8ff;font-family:'JetBrains Mono',monospace;font-size:0.65rem;padding:4px 10px;border-radius:20px;font-weight:600;letter-spacing:0.5px;">EIT 022001-22</span>
      <span style="background:rgba(120,80,255,0.1);border:1px solid rgba(120,80,255,0.3);color:#a080ff;font-family:'JetBrains Mono',monospace;font-size:0.65rem;padding:4px 10px;border-radius:20px;font-weight:600;letter-spacing:0.5px;">AI GEMINI</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar - Inputs
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 1. พารามิเตอร์ระบบไฟฟ้า")
    phase_type = st.radio("ระบบไฟฟ้า", ["3 เฟส (อุตสาหกรรม)", "1 เฟส"])
    phase_num = 3 if "3" in phase_type else 1
    
    st.subheader("อัปโหลดข้อมูลโหลด (ทางเลือก)")
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ (CSV/Excel)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        load_data = process_load_profile(uploaded_file)
        if load_data['success']:
            st.success("อัปโหลดข้อมูลสำเร็จ!")
            P_input = float(load_data['worst_case']['p_kw'])
            pf1_input = float(load_data['worst_case']['pf'])
            st.info(f"ใช้ข้อมูลเดือน {load_data['worst_case']['month']}: P={P_input}kW, PF={pf1_input}")
        else:
            st.error(load_data['error'])
            P_input = 150.0
            pf1_input = 0.75
    else:
        P_input = 150.0
        pf1_input = 0.75

    P = st.number_input("กำลังไฟฟ้าจริง P (kW)", min_value=1.0, value=P_input, step=10.0)
    
    default_v = 380 if phase_num == 3 else 220
    V = st.number_input("แรงดันไฟฟ้า V (Volt)", min_value=1, value=default_v)
    f = st.number_input("ความถี่ f (Hz)", min_value=1, value=50)
    
    st.header("🎯 2. เป้าหมายการปรับปรุง")
    pf1 = st.slider("Power Factor ปัจจุบัน", min_value=0.50, max_value=0.99, value=pf1_input, step=0.01)
    pf2 = st.slider("Power Factor เป้าหมาย", min_value=0.50, max_value=1.00, value=0.95, step=0.01)
    
    if pf2 <= pf1:
        st.error("⚠️ Power Factor เป้าหมายต้องมีค่ามากกว่า Power Factor ปัจจุบัน")
        st.stop()
        
    st.header("⚠️ 3. หม้อแปลงและฮาร์มอนิก")
    trafo_kva = st.number_input("พิกัดหม้อแปลง (kVA)", min_value=50.0, value=500.0, step=50.0)
    z_percent = st.number_input("อิมพีแดนซ์ (%Z)", min_value=1.0, value=4.0, step=0.1)

    st.header("📡 4. ค่าฮาร์มอนิกที่วัดได้จริง (IEEE 519)")
    enable_ieee519 = st.checkbox("เปิดใช้งานการวิเคราะห์ IEEE 519", value=False)
    if enable_ieee519:
        thdi_pct = st.number_input("THDi กระแส (%)", min_value=0.0, max_value=200.0, value=12.0, step=0.5,
                                   help="ค่า Total Harmonic Distortion ของกระแส วัดด้วย Power Analyzer")
        thdv_pct = st.number_input("THDv แรงดัน (%)", min_value=0.0, max_value=50.0, value=3.5, step=0.5,
                                   help="ค่า Total Harmonic Distortion ของแรงดัน")
        isc_il   = st.number_input("Isc/IL Ratio", min_value=1.0, max_value=2000.0, value=20.0, step=5.0,
                                   help="อัตราส่วนกระแสลัดวงจร / กระแสโหลด")
        vl_level = st.selectbox("ระดับแรงดันระบบ", ["LV (< 1 kV)", "MV (1–69 kV)", "HV (69–161 kV)"])
        vl_key   = "LV" if "LV" in vl_level else ("MV" if "MV" in vl_level else "HV")
    else:
        thdi_pct, thdv_pct, isc_il, vl_key = 0.0, 0.0, 20.0, "LV"

    st.header("🔧 5. การจัดสเต็ปคาปาซิเตอร์")
    num_steps_pref = st.selectbox("จำนวนสเต็ปที่ต้องการ (อ้างอิง)", [3, 4, 5, 6, 8], index=2)
    use_detuned    = harmonic_results_placeholder = st.checkbox("ติดตั้ง Detuned Reactor 7%", value=False,
                                   help="เปิดหากระบบมีฮาร์มอนิกสูง หรือ h_r อยู่ในช่วงเสี่ยง")

    st.header("💰 6. พารามิเตอร์ทางการเงิน")
    cost_per_kvar = st.number_input("ราคาประเมินตู้ต่อ kVAR (บาท)", min_value=100.0, value=1500.0, step=100.0)
    penalty_rate  = st.number_input("ค่าปรับจากการไฟฟ้า (บาท/kVAR/เดือน)", min_value=0.0, value=56.07)
    overhead_pct  = st.slider("Profit Margin / Overhead (%)", min_value=0, max_value=40, value=10) / 100

    st.divider()
    st.header("💾 7. บันทึก / โหลดโปรเจกต์")

    # ── Load Project ──
    proj_file = st.file_uploader("📂 โหลดโปรเจกต์ (.json)", type=["json"], key="proj_loader")
    if proj_file is not None:
        try:
            proj_data = json.load(proj_file)
            st.success(f"✅ โหลดโปรเจกต์ '{proj_data.get('project_name','ไม่มีชื่อ')}' สำเร็จ!")
            st.info("ℹ️ รีเฟรชหน้าแล้วค่าจะถูกโหลดอัตโนมัติในรอบถัดไป (ใช้ session_state)")
            st.session_state["loaded_project"] = proj_data
        except Exception as e:
            st.error(f"โหลดไม่ได้: {e}")

# ---------------------------------------------------------
# Processing Logic
# ---------------------------------------------------------
eng_results     = calculate_q_and_c(P, V, f, pf1, pf2, phase_num)
harmonic_results= check_harmonic_resonance(eng_results["Qc_total_kVAR"], trafo_kva, z_percent)
fin_results     = calculate_roi(P, pf1, pf2, eng_results["Qc_total_kVAR"], penalty_rate, cost_per_kvar)
detail_eng      = calculate_detail_engineering(eng_results["I_c_A"], eng_results["I_load_A"], eng_results["Qc_total_kVAR"], trafo_kva, z_percent)
step_config     = calculate_cap_steps(eng_results["Qc_total_kVAR"], num_steps=num_steps_pref)

# Parse CT primary from string like "400/5A"
ct_primary_val  = int(detail_eng['ct_ratio'].split('/')[0])

# BOQ calculation
boq_results = generate_boq(
    qc_kvar       = eng_results["Qc_total_kVAR"],
    step_config   = step_config,
    i_c_A         = eng_results["I_c_A"],
    i_load_A      = eng_results["I_load_A"],
    cable_size    = detail_eng["cable_size"],
    cb_at         = eng_results["recommended_cb_AT"],
    fuse_amp      = detail_eng["fuse_amp_req"],
    ct_primary    = ct_primary_val,
    use_detuned_reactor = use_detuned,
    overhead_pct  = overhead_pct,
)

# IEEE 519 Analysis
if enable_ieee519:
    ieee519_results = analyze_harmonics_ieee519(thdi_pct, thdv_pct, isc_il, vl_key)
else:
    ieee519_results = None

co2_reduction_kg = fin_results["energy_saved_kwh_yr"] * 0.4999

# ── Save Project JSON (after all inputs collected) ──
project_snapshot = {
    "project_name":  "PFC Project",
    "P_kw": P, "V": V, "f": f, "pf1": pf1, "pf2": pf2,
    "phase": phase_num, "trafo_kva": trafo_kva, "z_pct": z_percent,
    "cost_per_kvar": cost_per_kvar, "penalty_rate": penalty_rate,
    "overhead_pct": overhead_pct, "num_steps_pref": num_steps_pref,
    "use_detuned": use_detuned, "enable_ieee519": enable_ieee519,
    "thdi_pct": thdi_pct if enable_ieee519 else 0,
    "thdv_pct": thdv_pct if enable_ieee519 else 0,
    "isc_il": isc_il if enable_ieee519 else 20,
    "vl_key": vl_key,
}

# ---------------------------------------------------------
# Main UI Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "⚙️ Detail Engineering",
    "🔋 Step Configuration",
    "📡 IEEE 519 Harmonic",
    "📐 Power Triangle",
    "💰 ROI & สิ่งแวดล้อม",
    "📋 BOQ / ใบเสนอราคา",
    "☀️ Solar & PDF",
])

with tab1:
    # ── Helper: Glow Metric Card ──
    def metric_card(label, value, icon="", accent="#00c8ff", glow_color="rgba(0,200,255,0.15)"):
        return f"""
        <div style="
            background: linear-gradient(135deg, rgba(0,15,30,0.8), rgba(0,30,60,0.6));
            border: 1px solid {accent}30;
            border-left: 3px solid {accent};
            border-radius: 12px;
            padding: 16px 20px;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 24px {glow_color}, inset 0 1px 0 rgba(255,255,255,0.03);
            transition: transform 0.2s;
        ">
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#4a7a90;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">{icon} {label}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:1.25rem;font-weight:700;color:{accent};text-shadow:0 0 16px {glow_color};">{value}</div>
        </div>
        """

    st.subheader("1. พิกัดกำลังไฟฟ้า (Power Sizing)")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(metric_card("Qc ที่ต้องการ", f"{eng_results['Qc_total_kVAR']:.2f} kVAR", "🔋", "#00ffcc", "rgba(0,255,204,0.15)"), unsafe_allow_html=True)
    col2.markdown(metric_card("คาปาซิแตนซ์", f"{eng_results['C_microfarad']:.2f} µF", "⚙️", "#00c8ff", "rgba(0,200,255,0.15)"), unsafe_allow_html=True)
    col3.markdown(metric_card("กระแส Capacitor (In)", f"{eng_results['I_c_A']:.2f} A", "⚡", "#7dd4fc", "rgba(125,212,252,0.15)"), unsafe_allow_html=True)
    col4.markdown(metric_card("กระแสโหลดรวม (I_load)", f"{eng_results['I_load_A']:.2f} A", "🏭", "#a0aec0", "rgba(160,174,192,0.1)"), unsafe_allow_html=True)

    st.subheader("2. มาตรฐานสวิตช์เกียร์และสายไฟ (วสท. 022001-22)")
    sc1, sc2, sc3 = st.columns(3)
    sc1.markdown(metric_card("สายไฟเมน (≥ 1.35 In)", detail_eng['cable_size'], "🔌", "#00ffcc", "rgba(0,255,204,0.15)"), unsafe_allow_html=True)
    sc2.markdown(metric_card("Main Breaker (≥ 1.43 In)", f"{eng_results['recommended_cb_AT']} AT", "🔴", "#f97316", "rgba(249,115,22,0.15)"), unsafe_allow_html=True)
    sc3.markdown(metric_card("ฟิวส์ HRC (≥ 1.65 In)", f"{detail_eng['fuse_amp_req']:.1f} A", "🛡️", "#a78bfa", "rgba(167,139,250,0.15)"), unsafe_allow_html=True)

    st.info(f"💡 **APFC Steps:** แนะนำแบ่งเป็น 5 สเต็ป (สเต็ปละประมาณ {detail_eng['step_kvar']:.2f} kVAR) \n\n"
            f"🔌 **Magnetic Contactor:** {detail_eng['contactor_type']}\n\n"
            f"⚡ **วงจรคายประจุ (Discharge Resistor):** {detail_eng['discharge_resistor']}")

    with st.expander("📌 ข้อกำหนดสเปกตัวเก็บประจุ (Capacitor Specification)", expanded=True):
        st.markdown("""
        - **ชนิด:** Dry Type (Non-PCB / Non-SF6) ใช้ฟิล์มโลหะโพลีโพรพิลีน (Metallized Polypropylene Film)
        - **คุณสมบัติ:** ซ่อมแซมตัวเองได้ (Self-healing) และมีกลไกตัดวงจรเมื่อแรงดันภายในสูง (Pressure Sensitive Disconnector)
        - **กำลังสูญเสียภายใน (Dielectric Losses):** ต้องต่ำกว่า 0.5 W/kVar
        - **หมวดหมู่อุณหภูมิ:** -25/D (ทนอุณหภูมิได้ถึง 55°C)
        """)
        if harmonic_results.get("detuned_p", 0.0) > 0:
            st.error(f"🚨 **ข้อบังคับวิกฤต (กรณีใช้ Detuned Reactor {harmonic_results['tuning_factor']}):**\n"
                     f"การนำ Reactor มาต่ออนุกรมจะทำให้แรงดันขั้วคาปาซิเตอร์พุ่งสูงขึ้น \n"
                     f"**$U_c = U_n / (1 - p)$ = {harmonic_results['u_c_voltage']:.1f} V** \n"
                     f"ดังนั้น **ห้ามใช้ Capacitor พิกัด 400V เด็ดขาด!** ต้องใช้ Capacitor ที่มีพิกัดแรงดันอย่างน้อย **440V, 480V หรือ 525V** เพื่อป้องกันการระเบิด")

    st.subheader("3. ระบบควบคุมและระบายความร้อน (Control & Ventilation)")
    vc1, vc2, vc3 = st.columns(3)
    vc1.markdown(metric_card("CT Ratio", detail_eng['ct_ratio'], "📡", "#00c8ff", "rgba(0,200,255,0.15)"), unsafe_allow_html=True)
    vc2.markdown(metric_card("ความร้อนในตู้ (Watt Loss)", f"{detail_eng['watt_loss']:.0f} W", "🌡️", "#f97316", "rgba(249,115,22,0.12)"), unsafe_allow_html=True)
    vc3.markdown(metric_card("พัดลมระบาย (Min.)", f"≥ {detail_eng['cfm_required']:.0f} CFM", "🌀", "#7dd4fc", "rgba(125,212,252,0.12)"), unsafe_allow_html=True)

with tab2:
    # ── Step Configuration ──
    st.subheader("🔋 การจัดสเต็ปคาปาซิเตอร์ (Smart Step Configuration)")

    sc = step_config
    r1, r2, r3 = st.columns(3)
    r1.markdown(metric_card("รูปแบบที่ดีที่สุด", sc["pattern_name"], "🏆", "#00ffcc", "rgba(0,255,204,0.15)"), unsafe_allow_html=True)
    r2.markdown(metric_card("kVAR ที่ได้จริง", f"{sc['total_achieved_kvar']:.1f} kVAR", "✅", "#00c8ff", "rgba(0,200,255,0.15)"), unsafe_allow_html=True)
    r3.markdown(metric_card("Coverage", f"{sc['coverage_pct']:.1f}%", "📊", "#a78bfa", "rgba(167,139,250,0.15)"), unsafe_allow_html=True)

    st.subheader("รายการสเต็ปที่แนะนำ")
    step_data = [{"สเต็ป": i+1, "ขนาด (kVAR)": s, "หมายเหตุ": "Dry Film Capacitor"}
                 for i, s in enumerate(sc["steps_kvar"])]
    st.dataframe(pd.DataFrame(step_data), use_container_width=True, hide_index=True)

    st.subheader("ค่า kVAR ที่สามารถสวิตช์ได้ทุกรูปแบบ")
    combos = sc["combinations"]
    combo_str = ", ".join([f"{c} kVAR" for c in combos])
    st.info(f"🔌 **{len(combos)} รูปแบบ:** {combo_str}")

    with st.expander("📊 เปรียบเทียบทุกรูปแบบสเต็ป", expanded=False):
        df_patterns = pd.DataFrame(sc["all_patterns"])
        st.dataframe(df_patterns, use_container_width=True, hide_index=True)

with tab3:
    # ── IEEE 519 ──
    st.subheader("📡 การวิเคราะห์ฮาร์มอนิก IEEE 519-2014")

    if not enable_ieee519:
        st.info("⚡ เปิดใช้งาน **'การวิเคราะห์ IEEE 519'** ในแถบด้านซ้ายเพื่อดูผลการวิเคราะห์ครับ")
        st.subheader("⚠️ ผลการประเมินเบื้องต้น (จากสเปคหม้อแปลง)")
        if harmonic_results["risk"] == "High":
            st.error(f"⚠️ {harmonic_results['message']}")
            st.warning(f"🔧 แนะนำ **Detuned Reactor** สเปค: {harmonic_results['tuning_factor']}")
            st.error(f"📌 แรงดันขั้วคาปา (Uc): **{harmonic_results['u_c_voltage']:.1f} V** — ต้องใช้ Capacitor ≥ 440V")
        else:
            st.success(f"✅ {harmonic_results['message']}")
    else:
        res = ieee519_results
        status_color = "#00ffcc" if "PASS" in res["overall_status"] else "#f97316"
        st.markdown(f"""
        <div style="background:rgba(0,15,30,0.8);border:2px solid {status_color};border-radius:14px;padding:20px 28px;margin-bottom:16px;text-align:center;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:1.5rem;font-weight:700;color:{status_color};">{res["overall_status"]}</div>
          <div style="color:#5a8aa0;font-size:0.8rem;margin-top:4px;">IEEE 519-2014 Compliance Result</div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("THDi วัดได้", f"{res['thdi_measured']:.1f}%", "📈", "#f97316" if not res["current_compliant"] else "#00ffcc"), unsafe_allow_html=True)
        c2.markdown(metric_card("THDv วัดได้", f"{res['thdv_measured']:.1f}%", "📉", "#f97316" if not res["voltage_compliant"] else "#00ffcc"), unsafe_allow_html=True)
        c3.markdown(metric_card("Isc/IL Ratio", f"{res['isc_il_ratio']:.0f}", "⚡", "#00c8ff"), unsafe_allow_html=True)

        st.subheader("ตารางความสอดคล้องมาตรฐาน IEEE 519")
        df_comp = pd.DataFrame(res["compliance_table"])
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

        st.subheader("คำแนะนำ")
        for rec in res["recommendations"]:
            st.markdown(f"- {rec}")

        if res["filter_recommendation"] != "ไม่จำเป็น":
            st.error(f"🔧 **อุปกรณ์ที่แนะนำ:** {res['filter_recommendation']}")
            st.warning(f"💰 **ประมาณงบประมาณ:** {res['filter_cost_estimate']}")

with tab4:
    st.subheader("กราฟสามเหลี่ยมกำลังไฟฟ้า (Interactive Power Triangle)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, P, P, 0], y=[0, 0, eng_results['Q1'], 0], fill='toself',
        name=f'ก่อนปรับปรุง (PF={pf1})',
        fillcolor='rgba(249,115,22,0.15)',
        line=dict(color='rgba(249,115,22,0.8)', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=[0, P, P, 0], y=[0, 0, eng_results['Q2'], 0], fill='toself',
        name=f'หลังปรับปรุง (PF={pf2})',
        fillcolor='rgba(0,255,204,0.1)',
        line=dict(color='rgba(0,255,204,0.9)', width=2)
    ))
    fig.update_layout(
        title=dict(text='Power Triangle: Active vs Reactive Power', font=dict(family='JetBrains Mono', size=13, color='#00c8ff')),
        xaxis_title='Active Power (kW)', yaxis_title='Reactive Power (kVAR)',
        showlegend=True, height=480,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,15,30,0.6)',
        font=dict(family='Inter', color='#7a9bb5'),
        xaxis=dict(gridcolor='rgba(0,200,255,0.07)', zerolinecolor='rgba(0,200,255,0.2)'),
        yaxis=dict(gridcolor='rgba(0,200,255,0.07)', zerolinecolor='rgba(0,200,255,0.2)'),
        legend=dict(bgcolor='rgba(0,15,30,0.8)', bordercolor='rgba(0,200,255,0.2)', borderwidth=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("ผลตอบแทนทางการเงินและสิ่งแวดล้อม (ต่อปี)")

    with st.expander("ℹ️ ข้อกำหนดค่าปรับ Power Factor จากการไฟฟ้า (PEA/MEA)", expanded=False):
        st.markdown("""
        **หลักเกณฑ์การคิดค่าปรับ:**
        การไฟฟ้าส่วนภูมิภาค (PEA) และการไฟฟ้านครหลวง (MEA) กำหนดให้ผู้ใช้ไฟฟ้าประเภทกิจการขนาดกลาง (ประเภทที่ 3) กิจการขนาดใหญ่ (ประเภทที่ 4) และกิจการเฉพาะอย่าง (ประเภทที่ 5-7) จะถูกเรียกเก็บ **"ค่าปรับเพาเวอร์แฟกเตอร์"** หากมีการดึงกำลังไฟฟ้ารีแอคทีฟเกินกว่า **ร้อยละ 61.97** ของความต้องการพลังไฟฟ้าสูงสุดในรอบเดือน

        **อัตราค่าปรับ:** ถูกกำหนดไว้ที่ **56.07 บาทต่อกิโลวาร์ (kVAR)** สำหรับส่วนที่เกินในแต่ละเดือน
        """)

    fin_col1, fin_col2 = st.columns(2)
    with fin_col1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(0,255,100,0.05),rgba(0,80,40,0.08));border:1px solid rgba(0,255,100,0.2);border-radius:14px;padding:20px 24px;margin-bottom:16px;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#00ff64;letter-spacing:1.5px;margin-bottom:16px;">💰 ผลตอบแทนการลงทุน (ROI)</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("ประมาณการเงินลงทุน (ตู้ CAP)", f"฿ {fin_results['investment_thb']:,.2f}")
        st.metric("ประหยัดเงินได้รวม", f"฿ {fin_results['yearly_saving_thb']:,.2f} / ปี")
        st.metric("ระยะเวลาคืนทุน (ประมาณ)", f"{fin_results['payback_months']:.1f} เดือน")
        st.caption("รวมค่าปรับที่หลีกเลี่ยงได้ และพลังงานในสายส่งที่ประหยัดได้")
    with fin_col2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,rgba(0,200,255,0.05),rgba(0,50,120,0.08));border:1px solid rgba(0,200,255,0.2);border-radius:14px;padding:20px 24px;margin-bottom:16px;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#00c8ff;letter-spacing:1.5px;margin-bottom:16px;">🌍 ผลกระทบเชิงบวกต่อสิ่งแวดล้อม</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("พลังงานที่ประหยัดได้ (Line Loss)", f"{fin_results['energy_saved_kwh_yr']:,.2f} kWh/ปี")
        st.metric("ลดการปล่อยคาร์บอน", f"{co2_reduction_kg:,.2f} kgCO2e/ปี")

with tab6:
    # ── BOQ ──
    st.subheader("📋 Bill of Quantities (BOQ) / ใบเสนอราคาเบื้องต้น")

    bq = boq_results
    b1, b2, b3, b4 = st.columns(4)
    b1.markdown(metric_card("ค่าวัสดุรวม", f"฿{bq['material_total']:,.0f}", "🔩", "#00c8ff"), unsafe_allow_html=True)
    b2.markdown(metric_card("ค่าแรง + วิศวกรรม", f"฿{bq['labor_cost']+bq['engineering_cost']:,.0f}", "👷", "#7dd4fc"), unsafe_allow_html=True)
    b3.markdown(metric_card("Overhead / กำไร", f"฿{bq['overhead']:,.0f}", "📈", "#a78bfa"), unsafe_allow_html=True)
    b4.markdown(metric_card("รวมทั้งสิ้น", f"฿{bq['grand_total']:,.0f}", "💰", "#00ffcc", "rgba(0,255,204,0.2)"), unsafe_allow_html=True)

    st.subheader("รายการวัสดุและอุปกรณ์")
    df_boq = pd.DataFrame(bq["line_items"])
    st.dataframe(df_boq, use_container_width=True, hide_index=True)

    # Summary table
    st.subheader("สรุปงบประมาณ")
    summary_data = [
        {"หมวด": "วัสดุและอุปกรณ์ (Material)", "จำนวน (บาท)": f"฿ {bq['material_total']:,.2f}"},
        {"หมวด": f"ค่าแรงติดตั้ง ({int(18)}%)", "จำนวน (บาท)": f"฿ {bq['labor_cost']:,.2f}"},
        {"หมวด": f"ค่าวิศวกรรม + Commissioning ({int(8)}%)", "จำนวน (บาท)": f"฿ {bq['engineering_cost']:,.2f}"},
        {"หมวด": f"Overhead / กำไร ({int(overhead_pct*100)}%)", "จำนวน (บาท)": f"฿ {bq['overhead']:,.2f}"},
        {"หมวด": "💰 ราคาเสนอรวม (Grand Total)", "จำนวน (บาท)": f"฿ {bq['grand_total']:,.2f}"},
    ]
    st.table(pd.DataFrame(summary_data))

    # Export BOQ to Excel
    st.subheader("ส่งออกข้อมูล")
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        pd.DataFrame(bq["line_items"]).to_excel(writer, sheet_name="BOQ", index=False)
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
    excel_buf.seek(0)
    st.download_button(
        label="📥 ดาวน์โหลด BOQ (.xlsx)",
        data=excel_buf,
        file_name="PFC_BOQ.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # Save Project JSON
    proj_json = json.dumps(project_snapshot, ensure_ascii=False, indent=2)
    st.download_button(
        label="💾 บันทึกโปรเจกต์ (.json)",
        data=proj_json.encode("utf-8"),
        file_name="pfc_project.json",
        mime="application/json",
    )

with tab7:
    st.subheader("☀️ ผลกระทบของ Solar PV ต่อค่า Power Factor")
    st.markdown("""
    โรงงานที่ติดตั้ง Solar PV Rooftop มักประสบปัญหาค่า Power Factor ตกต่ำลงอย่างรุนแรง และถูกการไฟฟ้าฯ ปรับเงิน ทั้งที่ไม่เคยโดนปรับมาก่อน

    **กลไกที่เกิดขึ้น:** อินเวอร์เตอร์โซลาร์เซลล์โดยทั่วไปจะอัดฉีดเฉพาะกำลังไฟฟ้าจริง (kW) แต่ไม่จ่ายกำลังไฟฟ้ารีแอคทีฟ (kVar) ทำให้โรงงานดึง kW จากการไฟฟ้าน้อยลง แต่ยังคงดึง kVar เท่าเดิม สัดส่วน kVar/kW จึงพุ่งสูงขึ้นจนทะลุเกณฑ์ของการไฟฟ้าฯ
    """)

    st.subheader("🛠️ กลยุทธ์การแก้ปัญหา (Mitigation Strategies)")
    strategies = [
        {"กลยุทธ์": "1. ย้ายจุดเชื่อมต่อโซลาร์ / ย้าย CT", "กลไก": "ย้าย CT ของตู้ Cap Bank ให้มาอยู่ก่อนจุดที่โซลาร์เซลล์จะจ่ายไฟ", "งบประมาณ": "ต่ำ (5,000 - 30,000 บาท)", "ความเหมาะสม": "ตู้ Cap Bank เดิมยังมีสภาพดี"},
        {"กลยุทธ์": "2. อัพเกรดเป็น APFC แบบ 4-Quadrant", "กลไก": "เปลี่ยนรีเลย์ให้เป็นรุ่นที่วัดกระแสย้อนกลับได้", "งบประมาณ": "ปานกลาง (50k - 200k บาท)", "ความเหมาะสม": "ตู้เก่าใช้รีเลย์ที่ไม่รองรับโหลดสองทิศทาง"},
        {"กลยุทธ์": "3. โหมดชดเชย kVar จาก Inverter", "กลไก": "ตั้งค่าอินเวอร์เตอร์โซลาร์ให้จ่าย kVar ออกมาช่วย", "งบประมาณ": "0 บาท (สูญเสียกำลัง kW 5-10%)", "ความเหมาะสม": "อินเวอร์เตอร์รองรับ"},
        {"กลยุทธ์": "4. ติดตั้ง Static Var Generator (SVG)", "กลไก": "ใช้อิเล็กทรอนิกส์กำลังชดเชย kVar แบบ Stepless", "งบประมาณ": "สูง (> 1 ล้านบาท)", "ความเหมาะสม": "โหลดผันผวนสูงมาก"},
    ]
    st.table(strategies)

    st.subheader("📄 ออกรายงานวิศวกรรม PDF")
    if st.button("🖨️ สร้างรายงาน PDF"):
        params = {
            "p_kw": P, "voltage": V, "pf1": pf1, "pf2": pf2,
            "qc_kvar": eng_results['Qc_total_kVAR'],
            "c_uF": eng_results['C_microfarad'],
            "i_c": eng_results['I_c_A'],
            "cb_rating": eng_results['recommended_cb_AT'],
            "h_r": harmonic_results["h_r"],
            "risk": harmonic_results["risk"],
            "risk_msg": harmonic_results["message"],
            "tuning_factor": harmonic_results["tuning_factor"],
            "roi": fin_results,
            "co2": co2_reduction_kg,
            "cable_size": detail_eng['cable_size'],
            "breaker_ka": detail_eng['breaker_kA'],
            "ct_ratio": detail_eng['ct_ratio'],
            "cfm": detail_eng['cfm_required'],
        }
        output_file = "PFC_Engineering_Report.pdf"
        generate_report(params, output_file)
        with open(output_file, "rb") as file:
            st.download_button(
                label="📥 ดาวน์โหลดเอกสาร PDF",
                data=file,
                file_name=output_file,
                mime="application/pdf",
            )
        st.success("สร้างรายงานสำเร็จ!")




# ── AI Chat Section Header ──

st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(120,80,255,0.08), rgba(0,100,200,0.06));
    border: 1px solid rgba(120,80,255,0.2);
    border-radius: 14px;
    padding: 20px 28px;
    margin: 24px 0 16px;
    display:flex; align-items:center; gap:16px;
">
  <span style="font-size:1.8rem;">🤖</span>
  <div>
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;font-weight:700;color:#a080ff;letter-spacing:1px;">AI ENGINEERING ASSISTANT</div>
    <div style="font-family:'Inter',sans-serif;font-size:0.78rem;color:#6a5a90;margin-top:2px;">ถามได้เลยครับ — AI รู้จักผลการคำนวณทั้งหมดของระบบ (Capacitor, Harmonic, ROI, Solar PV)</div>
  </div>
  <span style="margin-left:auto;background:linear-gradient(90deg,rgba(120,80,255,0.2),rgba(0,100,200,0.2));border:1px solid rgba(120,80,255,0.3);color:#a080ff;font-family:'JetBrains Mono',monospace;font-size:0.65rem;padding:4px 12px;border-radius:20px;font-weight:600;letter-spacing:0.5px;">POWERED BY GEMINI</span>
</div>
""", unsafe_allow_html=True)

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Build a rich context string from current calculations
def build_engineering_context():
    harmonic_risk = harmonic_results.get("risk", "N/A")
    u_c = harmonic_results.get("u_c_voltage", 0)
    detuned_p = harmonic_results.get("detuned_p", 0.0)
    reactor_note = ""
    if detuned_p > 0:
        reactor_note = f"""
- ⚠️ ต้องใช้ Detuned Reactor {harmonic_results['tuning_factor']} เพราะมีความเสี่ยงฮาร์มอนิก
- แรงดันขยายตัวที่ขั้ว Capacitor (Uc) = {u_c:.1f} V → ต้องใช้ Capacitor พิกัด 440V/480V/525V เท่านั้น ห้ามใช้ 400V"""
    
    return f"""
คุณเป็น "AI วิศวกรผู้เชี่ยวชาญด้าน Power Factor Correction" ที่ถูกฝังอยู่ในระบบวิเคราะห์ PFC ขั้นสูง
คุณต้องตอบเป็นภาษาไทยเสมอ ยกเว้นคำศัพท์เทคนิคที่ไม่มีคำแปลที่เหมาะสม
คุณรู้จักผลการคำนวณของระบบในปัจจุบัน ดังนี้:

=== ผลการคำนวณปัจจุบัน (Context) ===
• กำลังไฟฟ้าจริง (P) = {P:.2f} kW
• แรงดันไฟฟ้า (V) = {V} V | ความถี่ = {f} Hz
• Power Factor ปัจจุบัน (PF1) = {pf1:.2f}
• Power Factor เป้าหมาย (PF2) = {pf2:.2f}
• Qc ที่ต้องการติดตั้ง = {eng_results['Qc_total_kVAR']:.2f} kVAR
• คาปาซิแตนซ์รวม (C) = {eng_results['C_microfarad']:.2f} µF
• กระแสพิกัด Capacitor (In) = {eng_results['I_c_A']:.2f} A
• กระแสโหลดรวม (I_load) = {eng_results['I_load_A']:.2f} A

=== มาตรฐาน วสท. 022001-22 ===
• ขนาดสายไฟเมน (≥1.35xIn) = {detail_eng['cable_size']}
• เมนเบรกเกอร์ (≥1.43xIn) = {eng_results['recommended_cb_AT']} AT
• พิกัดฟิวส์ HRC (≥1.65xIn) = {detail_eng['fuse_amp_req']:.1f} A
• CT Ratio = {detail_eng['ct_ratio']}
• ความร้อนในตู้ = {detail_eng['watt_loss']:.0f} W
• Contactor: {detail_eng['contactor_type']}
• Discharge Resistor: {detail_eng['discharge_resistor']}

=== ฮาร์มอนิกเรโซแนนซ์ ===
• ค่า h_r = {harmonic_results['h_r']:.2f} | ระดับความเสี่ยง = {harmonic_risk}{reactor_note}

=== ผลลัพธ์ทางการเงิน ===
• เงินลงทุนประเมิน = {fin_results['investment_thb']:,.2f} บาท
• ประหยัดต่อปี = {fin_results['yearly_saving_thb']:,.2f} บาท
• ระยะเวลาคืนทุน = {fin_results['payback_months']:.1f} เดือน
• ลด CO2 = {co2_reduction_kg:,.2f} kgCO2e/ปี
• ขนาดหม้อแปลง = {trafo_kva} kVA | %Z = {z_percent}%

ตอบคำถามให้กระชับ ถูกต้อง และมีมาตรฐานทางวิศวกรรม
อ้างอิงผลการคำนวณข้างต้นเมื่อเกี่ยวข้อง"""

# Display chat history
chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("ถามวิศวกร AI ได้เลยครับ เช่น 'ทำไมต้องใช้ Detuned Reactor?' หรือ 'ROI คุ้มไหม?'")

if user_input:
    # Add user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Call Gemini API
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("AI กำลังวิเคราะห์..."):
            try:
                GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
                if not GEMINI_API_KEY:
                    try:
                        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
                    except Exception:
                        GEMINI_API_KEY = ""

                if not GEMINI_API_KEY:
                    response_text = ("⚠️ กรุณาตั้งค่า **GEMINI_API_KEY** ก่อนใช้งาน AI Chat ครับ\n\n"
                                     "1. ไปที่ https://aistudio.google.com/app/apikey\n"
                                     "2. กด **Get API key** → **Create API key**\n"
                                     "3. Copy key (ขึ้นต้นด้วย AIza...)\n"
                                     "4. วางใน `.streamlit/secrets.toml`")
                else:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    
                    # Build conversation history
                    history_for_gemini = []
                    for h in st.session_state.chat_history[:-1]:
                        role = "user" if h["role"] == "user" else "model"
                        history_for_gemini.append(
                            types.Content(role=role, parts=[types.Part(text=h["content"])])
                        )
                    history_for_gemini.append(
                        types.Content(role="user", parts=[types.Part(text=user_input)])
                    )
                    
                    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
                    response_text = None
                    last_error = None
                    
                    for model_name in models_to_try:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=history_for_gemini,
                                config=types.GenerateContentConfig(
                                    system_instruction=build_engineering_context(),
                                    temperature=0.7,
                                )
                            )
                            response_text = response.text
                            break
                        except Exception as model_err:
                            last_error = model_err
                            continue
                    
                    if response_text is None:
                        err_str = str(last_error)
                        if "429" in err_str or "quota" in err_str.lower():
                            response_text = (
                                "❌ **API Key มี Quota หมดหรือเป็น 0 ครับ**\n\n"
                                "**วิธีแก้ไข:**\n"
                                "1. ไปที่ https://aistudio.google.com/app/apikey\n"
                                "2. Copy key ที่ขึ้นต้นด้วย **`AIzaSy`**\n"
                                "3. วางใน `.streamlit/secrets.toml` แทนที่ key เดิม\n"
                                "4. Restart แอปแล้วลองใหม่"
                            )
                        else:
                            response_text = f"❌ เกิดข้อผิดพลาด: `{err_str[:300]}`"

            except Exception as e:
                response_text = f"❌ เกิดข้อผิดพลาด: `{str(e)[:300]}`"

        st.markdown(response_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# Clear chat button
if st.session_state.chat_history:
    col_clear, _ = st.columns([1, 5])
    with col_clear:
        if st.button("🗑️ ล้างแชท", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
