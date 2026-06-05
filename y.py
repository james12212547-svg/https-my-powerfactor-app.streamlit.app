import streamlit as st
import math
import plotly.graph_objects as go
import pandas as pd

# ---------------------------------------------------------
# ตั้งค่าหน้าเว็บ
# ---------------------------------------------------------
st.set_page_config(page_title="Advanced PFC Analyzer", layout="wide")

st.title("⚡ ระบบวิเคราะห์การปรับปรุง Power Factor ขั้นสูง")
st.markdown("ประเมินขนาด Capacitor Bank, อุปกรณ์ป้องกัน และการลดการปล่อยก๊าซเรือนกระจก")
st.divider()

# ---------------------------------------------------------
# ส่วนที่ 1: รับค่าตัวแปร (Sidebar & Inputs)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ พารามิเตอร์ระบบ")
    phase_type = st.radio("ระบบไฟฟ้า", ["3 เฟส (อุตสาหกรรม)", "1 เฟส"])
    P = st.number_input("กำลังไฟฟ้าจริง P (kW)", min_value=1.0, value=150.0, step=10.0)
    
    default_v = 380 if "3" in phase_type else 220
    V = st.number_input("แรงดันไฟฟ้า V (Volt)", min_value=1, value=default_v)
    f = st.number_input("ความถี่ f (Hz)", min_value=1, value=50)
    
    st.header("🎯 เป้าหมาย")
    pf1 = st.slider("Power Factor ปัจจุบัน", min_value=0.50, max_value=0.99, value=0.75, step=0.01)
    pf2 = st.slider("Power Factor เป้าหมาย", min_value=0.50, max_value=1.00, value=0.95, step=0.01)

# ตรวจสอบเงื่อนไข
if pf2 <= pf1:
    st.error("⚠️ ข้อผิดพลาด: Power Factor เป้าหมาย ต้องมีค่ามากกว่าค่าปัจจุบัน")
    st.stop()

# ---------------------------------------------------------
# ส่วนที่ 2: การคำนวณทางคณิตศาสตร์วิศวกรรม
# ---------------------------------------------------------
# 1. คำนวณมุมและ Qc
theta1 = math.acos(pf1)
theta2 = math.acos(pf2)
Qc_total = P * (math.tan(theta1) - math.tan(theta2))

# คำนวณ S1, S2, Q1, Q2 สำหรับกราฟ
Q1 = P * math.tan(theta1)
Q2 = P * math.tan(theta2)
S1 = P / pf1
S2 = P / pf2

# 2. หาขนาดตัวเก็บประจุ
if "3" in phase_type:
    # 3 เฟส ต่อ Delta
    C_farad = (Qc_total * 1000) / (3 * 2 * math.pi * f * (V**2))
    I_c = (Qc_total * 1000) / (math.sqrt(3) * V)
else:
    # 1 เฟส
    C_farad = (Qc_total * 1000) / (2 * math.pi * f * (V**2))
    I_c = (Qc_total * 1000) / V

C_microfarad = C_farad * 1_000_000

# 3. คำนวณอุปกรณ์ป้องกันตามมาตรฐาน วสท. (พิกัดกระแส ~ 1.35 เท่าของ In)
cb_rating_calc = I_c * 1.35
# ขนาดเบรกเกอร์มาตรฐาน (AT)
standard_cb = [16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000]
recommended_cb = next((x for x in standard_cb if x >= cb_rating_calc), standard_cb[-1])

# 4. ประเมินการลดคาร์บอน (สมมติฐาน: ลด Line Loss ได้ประมาณ 2% ของ P จากกระแสที่ลดลง)
# ใช้ Emission Factor ของประเทศไทย ประมาณ 0.4999 kgCO2/kWh
hours_per_year = 300 * 12  # สมมติทำงานวันละ 12 ชม. 300 วัน/ปี
loss_reduction_kW = P * 0.02 * (1 - (pf1/pf2)**2) 
energy_saved_kWh = loss_reduction_kW * hours_per_year
co2_reduced_kg = energy_saved_kWh * 0.4999

# ---------------------------------------------------------
# ส่วนที่ 3: การแสดงผลผ่าน UI (แบ่งแท็บ)
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 สรุปผลวิศวกรรม & อุปกรณ์", "📐 Power Triangle", "🌱 วิเคราะห์ความคุ้มทุน & สิ่งแวดล้อม"])

with tab1:
    st.subheader("ผลการคำนวณการชดเชยกำลังไฟฟ้ารีแอคทีฟ")
    col1, col2, col3 = st.columns(3)
    col1.metric("พิกัด Qc ที่ต้องติดตั้งรวม", f"{Qc_total:.2f} kVAR")
    col2.metric("ลด Apparent Power (S)", f"{(S1 - S2):.2f} kVA", f"ลดลงจาก {S1:.1f} kVA")
    col3.metric("กระแสพิกัดคาปาซิเตอร์ (In)", f"{I_c:.2f} A")
    
    st.divider()
    st.subheader("🛠️ การออกแบบติดตั้ง (สเปคอ้างอิง วสท.)")
    
    req_col1, req_col2 = st.columns(2)
    with req_col1:
        st.info(f"**ขนาดเบรกเกอร์แนะนำ (CB):** {recommended_cb} AT")
        st.write(f"*คำนวณจาก 1.35 เท่าของพิกัดกระแส (คำนวณได้ {cb_rating_calc:.2f} A)*")
    
    with req_col2:
        # แนะนำการแบ่ง Step ตู้ Capacitor (ใช้ 4-6 สเต็ป)
        step_size = Qc_total / 5
        st.info(f"**แนะนำการแบ่งตู้ (APFC Steps):** 5 สเต็ป")
        st.write(f"*สเต็ปละประมาณ {step_size:.2f} kVAR (เลือกขนาดตลาดที่ใกล้เคียงที่สุด)*")

with tab2:
    st.subheader("กราฟสามเหลี่ยมกำลังไฟฟ้า (Interactive Power Triangle)")
    
    # วาดกราฟด้วย Plotly
    fig = go.Figure()
    
    # สามเหลี่ยมเดิม (สีแดง)
    fig.add_trace(go.Scatter(x=[0, P, P, 0], y=[0, 0, Q1, 0], fill='toself', 
                             name=f'ก่อนปรับปรุง (PF={pf1})', marker=dict(color='rgba(255, 99, 132, 0.5)')))
    
    # สามเหลี่ยมใหม่ (สีเขียว)
    fig.add_trace(go.Scatter(x=[0, P, P, 0], y=[0, 0, Q2, 0], fill='toself', 
                             name=f'หลังปรับปรุง (PF={pf2})', marker=dict(color='rgba(75, 192, 192, 0.7)')))
    
    fig.update_layout(title='ความสัมพันธ์ระหว่าง Active (P) และ Reactive (Q) Power',
                      xaxis_title='Active Power (kW)', yaxis_title='Reactive Power (kVAR)',
                      showlegend=True, height=500)
    
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("ประเมินผลกระทบเชิงบวก (รายปี)")
    
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        st.success("💰 ผลตอบแทนทางการเงิน")
        st.write("การปรับปรุง PF ช่วยหลีกเลี่ยงการถูกปรับ และลดความร้อนในสายไฟ")
        st.write(f"**ประมาณการหน่วยไฟฟ้าที่ประหยัดได้จาก Line Loss:** {energy_saved_kWh:,.2f} kWh/ปี")
        
    with col_e2:
        st.success("🌍 การลดคาร์บอนฟุตพรินต์")
        st.write(f"**ลดปริมาณก๊าซเรือนกระจกได้:** {co2_reduced_kg:,.2f} kgCO2e/ปี")
        st.write("*อ้างอิง Grid Emission Factor ของประเทศไทย*")

# ---------------------------------------------------------
# ส่วนที่ 4: ระบบสร้างรายงาน (Text/Markdown Download)
# ---------------------------------------------------------
st.divider()
st.subheader("📄 ส่งออกรายงาน")

# สร้างข้อความรายงาน
report_text = f"""รายงานวิเคราะห์การปรับปรุง Power Factor
--------------------------------------------------
พารามิเตอร์ระบบ:
- ระบบ: {phase_type}
- กำลังไฟฟ้าจริง (P): {P} kW
- แรงดัน (V): {V} Volt
- Power Factor ปัจจุบัน: {pf1}
- Power Factor เป้าหมาย: {pf2}

ผลการคำนวณ:
- กำลังไฟฟ้ารีแอคทีฟที่ต้องชดเชย: {Qc_total:.2f} kVAR
- ขนาดตัวเก็บประจุ: {C_microfarad:.2f} uF
- กระแสพิกัด In: {I_c:.2f} A

สเปคอุปกรณ์ที่แนะนำ:
- เซอร์กิตเบรกเกอร์ (CB): {recommended_cb} AT

ผลกระทบต่อสิ่งแวดล้อม:
- พลังงานสูญเสียในสายส่งที่ประหยัดได้: {energy_saved_kWh:.2f} kWh/ปี
- ปริมาณการลดก๊าซคาร์บอน (CO2 Reduction): {co2_reduced_kg:.2f} kgCO2e/ปี
--------------------------------------------------
*สร้างโดยระบบ Advanced PFC Analyzer (Python & Streamlit)*
"""

st.download_button(
    label="📥 ดาวน์โหลดรายงานผลการคำนวณ (.txt)",
    data=report_text,
    file_name="PFC_Engineering_Report.txt",
    mime="text/plain",
    type="primary"
)