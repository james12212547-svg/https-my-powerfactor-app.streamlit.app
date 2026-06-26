import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from google import genai
from google.genai import types

# Import our modularized backend logic
from src.engineering import calculate_q_and_c, check_harmonic_resonance, calculate_detail_engineering
from src.financial import calculate_roi
from src.data_loader import process_load_profile
from src.pdf_generator import generate_report

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="Advanced PFC Analyzer", layout="wide", page_icon="⚡")

# Custom CSS for Engineering/SCADA Theme
st.markdown("""
<style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
    /* SCADA Theme for Metrics */
    .stMetric {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-left: 4px solid #00FF00;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stMetric label {
        color: #888 !important;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9rem;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #00FF00 !important;
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
    }
    /* Section Headers */
    h2, h3 {
        color: #4DA8DA;
        font-family: 'Courier New', Courier, monospace;
        text-transform: uppercase;
        border-bottom: 1px solid #4DA8DA;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Floating AI Chat Widget CSS
# ============================================================
st.markdown("""
<style>
/* Floating Chat Button */
.chat-fab {
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 9999;
    background: linear-gradient(135deg, #0D47A1, #1565C0);
    color: white;
    border: none;
    border-radius: 50px;
    padding: 14px 22px;
    font-size: 15px;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 6px 24px rgba(13,71,161,0.55);
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    letter-spacing: 0.5px;
}
.chat-fab:hover {
    transform: translateY(-3px) scale(1.05);
    box-shadow: 0 10px 30px rgba(13,71,161,0.7);
    background: linear-gradient(135deg, #1565C0, #0D47A1);
}
/* AI Badge on title */
.ai-badge {
    display: inline-block;
    background: linear-gradient(90deg, #0D47A1, #00BCD4);
    color: white;
    font-size: 11px;
    font-family: 'Courier New', monospace;
    padding: 3px 10px;
    border-radius: 20px;
    margin-left: 10px;
    vertical-align: middle;
    letter-spacing: 1px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ ระบบวิเคราะห์และออกแบบ Power Factor ขั้นสูง (PRO VERSION)")
st.markdown("เครื่องมือวิศวกรรมสำหรับ **Detail Engineering Design** (คำนวณ Capacitor, สายไฟ, เซอร์กิตเบรกเกอร์, ระบบระบายความร้อน และ ROI)")
st.divider()

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

    st.header("💰 4. พารามิเตอร์ทางการเงิน")
    cost_per_kvar = st.number_input("ราคาประเมินตู้ต่อ kVAR (บาท)", min_value=100.0, value=1500.0, step=100.0)
    penalty_rate = st.number_input("ค่าปรับจากการไฟฟ้า (บาท/kVAR/เดือน)", min_value=0.0, value=56.07)

# ---------------------------------------------------------
# Processing Logic
# ---------------------------------------------------------
eng_results = calculate_q_and_c(P, V, f, pf1, pf2, phase_num)
harmonic_results = check_harmonic_resonance(eng_results["Qc_total_kVAR"], trafo_kva, z_percent)
fin_results = calculate_roi(P, pf1, pf2, eng_results["Qc_total_kVAR"], penalty_rate, cost_per_kvar)
detail_eng = calculate_detail_engineering(eng_results["I_c_A"], eng_results["I_load_A"], eng_results["Qc_total_kVAR"], trafo_kva, z_percent)

co2_reduction_kg = fin_results["energy_saved_kwh_yr"] * 0.4999

# ---------------------------------------------------------
# Main UI Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚙️ Detail Engineering", 
    "📐 สามเหลี่ยมกำลังไฟฟ้า", 
    "💰 วิเคราะห์ความคุ้มทุน", 
    "☀️ โซลาร์เซลล์และฮาร์มอนิก", 
    "📄 ออกรายงาน PDF"
])

with tab1:
    st.subheader("1. พิกัดกำลังไฟฟ้า (Power Sizing)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Qc ที่ต้องการ", f"{eng_results['Qc_total_kVAR']:.2f} kVAR")
    col2.metric("คาปาซิแตนซ์", f"{eng_results['C_microfarad']:.2f} µF")
    col3.metric("กระแสพิกัดคาปาฯ (In)", f"{eng_results['I_c_A']:.2f} A")
    col4.metric("กระแสโหลดรวม (I_load)", f"{eng_results['I_load_A']:.2f} A")
    
    st.subheader("2. มาตรฐานอุปกรณ์สวิตช์เกียร์และสายไฟ (วสท. 022001-22)")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("ขนาดสายไฟเมน (≥ 1.35 In)", f"{detail_eng['cable_size']}")
    sc2.metric("Main Breaker (≥ 1.43 In)", f"{eng_results['recommended_cb_AT']} AT")
    sc3.metric("พิกัดฟิวส์ HRC (≥ 1.65 In)", f"{detail_eng['fuse_amp_req']:.1f} A")
    
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
    vc1.metric("อัตราส่วน CT (CT Ratio)", f"{detail_eng['ct_ratio']}")
    vc2.metric("ความร้อนสะสมในตู้ (Watt Loss)", f"{detail_eng['watt_loss']:.0f} W")
    vc3.metric("พัดลมดูดอากาศที่ต้องการ", f"≥ {detail_eng['cfm_required']:.0f} CFM")

with tab2:
    st.subheader("กราฟสามเหลี่ยมกำลังไฟฟ้า (Interactive Power Triangle)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, P, P, 0], y=[0, 0, eng_results['Q1'], 0], fill='toself', 
                             name=f'ก่อนปรับปรุง (PF={pf1})', marker=dict(color='rgba(255, 99, 132, 0.5)')))
    fig.add_trace(go.Scatter(x=[0, P, P, 0], y=[0, 0, eng_results['Q2'], 0], fill='toself', 
                             name=f'หลังปรับปรุง (PF={pf2})', marker=dict(color='rgba(75, 192, 192, 0.7)')))
    
    fig.update_layout(title='Active Power vs Reactive Power',
                      xaxis_title='Active Power (kW)', yaxis_title='Reactive Power (kVAR)',
                      showlegend=True, height=500, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("ผลตอบแทนทางการเงินและสิ่งแวดล้อม (ต่อปี)")
    
    with st.expander("ℹ️ ข้อกำหนดค่าปรับ Power Factor จากการไฟฟ้า (PEA/MEA)", expanded=False):
        st.markdown("""
        **หลักเกณฑ์การคิดค่าปรับ:**
        การไฟฟ้าส่วนภูมิภาค (PEA) และการไฟฟ้านครหลวง (MEA) กำหนดให้ผู้ใช้ไฟฟ้าประเภทกิจการขนาดกลาง (ประเภทที่ 3) กิจการขนาดใหญ่ (ประเภทที่ 4) และกิจการเฉพาะอย่าง (ประเภทที่ 5-7) จะถูกเรียกเก็บ **"ค่าปรับเพาเวอร์แฟกเตอร์"** หากมีการดึงกำลังไฟฟ้ารีแอคทีฟเกินกว่า **ร้อยละ 61.97** ของความต้องการพลังไฟฟ้าสูงสุด (Maximum Demand: kW) ในรอบเดือน
        
        *ตัวเลขร้อยละ 61.97 นี้มีที่มาจากการคำนวณทางตรีโกณมิติ โดยเทียบเท่ากับค่าพาวเวอร์แฟกเตอร์ที่ 0.85 (กล่าวคือ มุม $\\theta$ ที่ทำให้ $\\cos(\\theta) = 0.85$ จะมีค่า $\\tan(\\theta)$ เท่ากับ 0.6197)*
        
        **อัตราค่าปรับ:** ถูกกำหนดไว้ที่ **56.07 บาทต่อกิโลวาร์ (kVAR)** สำหรับส่วนที่เกินในแต่ละเดือน
        """)

    fin_col1, fin_col2 = st.columns(2)
    with fin_col1:
        st.success("💰 ผลตอบแทนการลงทุน (ROI)")
        st.metric("ประมาณการเงินลงทุน (ตู้ CAP)", f"฿ {fin_results['investment_thb']:,.2f}")
        st.metric("ประหยัดเงินได้รวม", f"฿ {fin_results['yearly_saving_thb']:,.2f} / ปี")
        st.metric("ระยะเวลาคืนทุน (ประมาณ)", f"{fin_results['payback_months']:.1f} เดือน")
        st.caption("รวมค่าปรับที่หลีกเลี่ยงได้ และพลังงานในสายส่งที่ประหยัดได้")
    with fin_col2:
        st.success("🌍 ผลกระทบเชิงบวกต่อสิ่งแวดล้อม")
        st.metric("พลังงานที่ประหยัดได้ (Line Loss)", f"{fin_results['energy_saved_kwh_yr']:,.2f} kWh/ปี")
        st.metric("ลดการปล่อยคาร์บอน", f"{co2_reduction_kg:,.2f} kgCO2e/ปี")

with tab4:
    st.subheader("☀️ ผลกระทบของ Solar PV ต่อค่า Power Factor")
    st.markdown("""
    โรงงานที่ติดตั้ง Solar PV Rooftop มักประสบปัญหาค่า Power Factor ตกต่ำลงอย่างรุนแรง และถูกการไฟฟ้าฯ ปรับเงิน ทั้งที่ไม่เคยโดนปรับมาก่อน
    
    **กลไกที่เกิดขึ้น:** อินเวอร์เตอร์โซลาร์เซลล์โดยทั่วไปจะอัดฉีดเฉพาะกำลังไฟฟ้าจริง (kW) แต่ไม่จ่ายกำลังไฟฟ้ารีแอคทีฟ (kVar) ทำให้โรงงานดึง kW จากการไฟฟ้าน้อยลง แต่ยังคงดึง kVar เท่าเดิม สัดส่วน kVar/kW จึงพุ่งสูงขึ้นจนทะลุเกณฑ์ของการไฟฟ้าฯ
    """)
    
    st.subheader("🛠️ กลยุทธ์การแก้ปัญหา (Mitigation Strategies)")
    
    strategies = [
        {"กลยุทธ์": "1. ย้ายจุดเชื่อมต่อโซลาร์ / ย้าย CT", "กลไก": "ย้าย CT ของตู้ Cap Bank ให้มาอยู่ก่อนจุดที่โซลาร์เซลล์จะจ่ายไฟ เพื่อให้รีเลย์มองเห็นโหลดโรงงานที่แท้จริง", "งบประมาณ": "ต่ำ (5,000 - 30,000 บาท)", "ความเหมาะสม": "ตู้ Cap Bank เดิมยังมีสภาพดี และมี Step ขนาดเล็กพอ"},
        {"กลยุทธ์": "2. อัพเกรดเป็น APFC แบบ 4-Quadrant", "กลไก": "เปลี่ยนรีเลย์ให้เป็นรุ่นที่วัดกระแสย้อนกลับแบบสองทิศทางได้", "งบประมาณ": "ปานกลาง (50k - 200k บาท)", "ความเหมาะสม": "ตู้เก่าใช้รีเลย์ที่ไม่รองรับโหลดสองทิศทาง"},
        {"กลยุทธ์": "3. โหมดชดเชย kVar จาก Inverter", "กลไก": "ตั้งค่าอินเวอร์เตอร์โซลาร์ให้จ่าย kVar ออกมาช่วย", "งบประมาณ": "0 บาท (แต่สูญเสียกำลังการผลิต kW 5-10%)", "ความเหมาะสม": "อินเวอร์เตอร์รองรับ และยอมสูญเสียพลังงาน kW ได้"},
        {"กลยุทธ์": "4. ติดตั้ง Static Var Generator (SVG)", "กลไก": "ใช้อุปกรณ์อิเล็กทรอนิกส์กำลังในการชดเชย kVar แบบ Stepless", "งบประมาณ": "สูง (> 1 ล้านบาท)", "ความเหมาะสม": "โหลดผันผวนสูงมาก ต้องการแก้ปัญหาอย่างเด็ดขาด"}
    ]
    
    st.table(strategies)
    
    st.subheader("⚠️ การจัดการฮาร์มอนิกและเรโซแนนซ์")
    if harmonic_results["risk"] == "High":
        st.error(f"⚠️ {harmonic_results['message']}")
        st.warning(f"🔧 แนะนำให้ติดตั้ง **Detuned Reactor** สเปค: {harmonic_results['tuning_factor']}")
    else:
        st.success(f"✅ {harmonic_results['message']}")

with tab5:
    st.subheader("📄 ออกรายงานวิศวกรรมฉบับสมบูรณ์ (PDF)")
    st.write("สร้างเอกสารรายละเอียดทางวิศวกรรมเพื่อส่งให้ผู้รับเหมาหรือฝ่ายจัดซื้อ")
    
    if st.button("สร้างรายงาน PDF"):
        params = {
            "p_kw": P,
            "voltage": V,
            "pf1": pf1,
            "pf2": pf2,
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
            "cfm": detail_eng['cfm_required']
        }
        
        output_file = "PFC_Engineering_Report.pdf"
        generate_report(params, output_file)
        
        with open(output_file, "rb") as file:
            btn = st.download_button(
                label="📥 ดาวน์โหลดเอกสาร",
                data=file,
                file_name=output_file,
                mime="application/pdf",
                type="primary"
            )
        st.success("สร้างรายงานสำเร็จเรียบร้อยแล้ว!")


# ============================================================
# AI CHAT ASSISTANT (Floating Bottom-Right)
# ============================================================
st.markdown("---")
st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
    <span style="font-size:1.4rem; font-weight:bold; color:#4DA8DA; font-family:'Courier New',monospace;">
        🤖 AI ENGINEERING ASSISTANT
    </span>
    <span style="background:linear-gradient(90deg,#0D47A1,#00BCD4);color:white;font-size:11px;
                 padding:3px 10px;border-radius:20px;font-family:'Courier New',monospace;
                 letter-spacing:1px;font-weight:bold;">POWERED BY GEMINI</span>
</div>
<p style="color:#888;font-size:0.85rem;font-family:'Courier New',monospace;margin-bottom:16px;">
    ถามได้เลยครับ — AI รู้จักผลการคำนวณทั้งหมดของระบบนี้ เช่น ขนาดตู้ Capacitor, ความเสี่ยง Harmonic, ROI หรือปัญหา Solar PV
</p>
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
