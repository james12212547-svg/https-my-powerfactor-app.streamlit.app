import streamlit as st
import math
import plotly.graph_objects as go

# ---------------------------------------------------------
# Constants (ค่าคงที่ — ไม่ควรกระจายอยู่ในโค้ด)
# ---------------------------------------------------------
CO2_FACTOR        = 0.4999   # kgCO2/kWh (ค่าการปล่อย CO2 ของ กฟผ. ปี 2024)
OPERATING_HOURS   = 3_600    # ชั่วโมง/ปี (300 วัน x 12 ชม.)
CB_SAFETY_FACTOR  = 1.35     # ตัวคูณความปลอดภัยเบรกเกอร์ (มาตรฐาน วสท.)
LINE_LOSS_FACTOR  = 0.02     # สมมติฐานการสูญเสียในสายส่ง 2%
STANDARD_CB       = [16, 20, 32, 40, 50, 63, 80, 100, 125, 160,
                     200, 250, 320, 400, 500, 630, 800, 1000]
MARKET_CAP_SIZES  = [5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100]  # kVAR

# ---------------------------------------------------------
# ตั้งค่าหน้าเว็บ
# ---------------------------------------------------------
st.set_page_config(page_title="Advanced PFC Analyzer", layout="wide")

st.title("⚡ ระบบวิเคราะห์การปรับปรุง Power Factor ขั้นสูง")
st.markdown("ประเมินขนาด Capacitor Bank, อุปกรณ์ป้องกัน และการวิเคราะห์ทางการเงิน")
st.divider()

# ---------------------------------------------------------
# ส่วนที่ 1: รับค่าตัวแปร (Sidebar)
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ พารามิเตอร์ทางไฟฟ้า")
    phase_type = st.radio("ระบบไฟฟ้า", ["3 เฟส (อุตสาหกรรม)", "1 เฟส"])
    P = st.number_input("กำลังไฟฟ้าจริง P (kW)", min_value=1.0, value=150.0, step=10.0)

    default_v = 380 if "3" in phase_type else 220
    V = st.number_input("แรงดันไฟฟ้า V (Volt)", min_value=1, value=default_v)
    f = st.number_input("ความถี่ f (Hz)", min_value=1, value=50)

    st.header("🎯 เป้าหมาย")
    pf1 = st.slider("Power Factor ปัจจุบัน",  min_value=0.50, max_value=0.99, value=0.75, step=0.01)
    pf2 = st.slider("Power Factor เป้าหมาย", min_value=0.50, max_value=1.00, value=0.95, step=0.01)

    st.header("📉 พารามิเตอร์คุณภาพไฟฟ้า")
    has_harmonics = st.checkbox("มีโหลด Non-linear (เช่น Inverter, VSD)", value=False)

    st.header("💰 พารามิเตอร์ทางการเงิน")
    cost_per_kvar = st.number_input("งบประมาณติดตั้ง (บาท/kVAR)", min_value=100, value=1500, step=100)
    penalty_rate  = st.number_input("อัตราค่าปรับ PF (บาท/kVAR/เดือน)", min_value=10.0, value=56.07, step=1.0)

# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
if pf2 <= pf1:
    st.error("⚠️ ข้อผิดพลาด: Power Factor เป้าหมายต้องมีค่า **มากกว่า** ค่าปัจจุบัน")
    st.stop()

# ---------------------------------------------------------
# ส่วนที่ 2: การคำนวณทางคณิตศาสตร์วิศวกรรม
# ---------------------------------------------------------

# --- 1. กำลังไฟฟ้า ---
theta1 = math.acos(pf1)
theta2 = math.acos(pf2)

Q1 = P * math.tan(theta1)   # kVAR ก่อนปรับปรุง
Q2 = P * math.tan(theta2)   # kVAR หลังปรับปรุง
Qc_total = Q1 - Q2          # kVAR ที่ต้องชดเชย

S1 = P / pf1                # kVA ก่อนปรับปรุง
S2 = P / pf2                # kVA หลังปรับปรุง

# --- 2. ขนาดตัวเก็บประจุ ---
# สูตรใช้ได้กับทั้ง Star (Y) และ Delta (Δ) configuration ที่แรงดัน Line-to-Line
if "3" in phase_type:
    # 3 เฟส: C_total per phase (Delta config: Q = 3 * ω * C * V_line²)
    C_farad = (Qc_total * 1_000) / (2 * math.pi * f * (V ** 2))
    I_c     = (Qc_total * 1_000) / (math.sqrt(3) * V)
else:
    # 1 เฟส: Q = ω * C * V²
    C_farad = (Qc_total * 1_000) / (2 * math.pi * f * (V ** 2))
    I_c     = (Qc_total * 1_000) / V

C_microfarad = C_farad * 1_000_000

# --- 3. เบรกเกอร์ตามมาตรฐาน วสท. ---
cb_rating_calc = I_c * CB_SAFETY_FACTOR
recommended_cb = next((x for x in STANDARD_CB if x >= cb_rating_calc), STANDARD_CB[-1])

# --- 4. ออกแบบสเต็ป Capacitor (อิงสเปคตลาด) ---
raw_step_size    = Qc_total / 5
step_exceeds_max = raw_step_size > max(MARKET_CAP_SIZES)
market_step_size = next(
    (size for size in MARKET_CAP_SIZES if size >= raw_step_size),
    MARKET_CAP_SIZES[-1]
)
installed_Qc = market_step_size * 5

# --- 5. การวิเคราะห์ทางการเงิน ---
total_investment      = installed_Qc * cost_per_kvar
monthly_penalty_saved = Qc_total * penalty_rate
payback_months        = (total_investment / monthly_penalty_saved
                         if monthly_penalty_saved > 0 else 0)

# --- 6. การประเมินการลดคาร์บอน ---
# สูตรที่ถูกต้อง: ΔP_loss ∝ I² → ΔP_loss = P * k * (1/pf1² - 1/pf2²)
loss_reduction_kW = P * LINE_LOSS_FACTOR * ((1 / pf1 ** 2) - (1 / pf2 ** 2))
energy_saved_kWh  = loss_reduction_kW * OPERATING_HOURS
co2_reduced_kg    = energy_saved_kWh * CO2_FACTOR

# ---------------------------------------------------------
# ส่วนที่ 3: การแสดงผล
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 สรุปผลวิศวกรรม & อุปกรณ์",
    "📐 Power Triangle",
    "💰 วิเคราะห์ความคุ้มทุน & สิ่งแวดล้อม"
])

# ── Tab 1: ผลวิศวกรรม ──────────────────────────────────
with tab1:
    st.subheader("ผลการคำนวณกำลังไฟฟ้ารีแอคทีฟ (เชิงทฤษฎี)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("พิกัด Qc ขั้นต่ำ",          f"{Qc_total:.2f} kVAR")
    col2.metric("ลด Apparent Power (S)",       f"{(S1 - S2):.2f} kVA",   f"ลดลงจาก {S1:.1f} kVA")
    col3.metric("กระแสพิกัด Ic (ขั้นต่ำ)",    f"{I_c:.2f} A")
    col4.metric("ขนาดตัวเก็บประจุ C",          f"{C_microfarad:.2f} µF")  # ✅ แสดงค่าที่คำนวณได้

    st.divider()
    st.subheader("🛠️ การออกแบบติดตั้ง (สเปคมาตรฐานอุตสาหกรรม)")

    if has_harmonics:
        st.warning(
            "⚠️ **ระบบมีการแจ้งเตือน Harmonics:** แนะนำให้ติดตั้ง Capacitor Bank "
            "ร่วมกับ **Detuned Filter Reactor (เช่น 7%)** เพื่อป้องกัน Resonance "
            "และยืดอายุการใช้งานของอุปกรณ์"
        )

    # ✅ แจ้งเตือนเมื่อ step size เกินขนาดที่มีในตลาด
    if step_exceeds_max:
        st.warning(
            f"⚠️ ขนาดสเต็ปที่ต้องการ ({raw_step_size:.1f} kVAR/สเต็ป) "
            f"เกินขนาดมาตรฐานในตลาด ({max(MARKET_CAP_SIZES)} kVAR) — "
            "แนะนำให้เพิ่มจำนวนสเต็ปหรือปรึกษาวิศวกร"
        )

    req_col1, req_col2 = st.columns(2)
    with req_col1:
        st.info(
            f"**ขนาดเบรกเกอร์แนะนำ (CB):** {recommended_cb} AT\n\n"
            f"*พิกัดกระแสคำนวณ = {cb_rating_calc:.1f} A "
            f"(Ic × {CB_SAFETY_FACTOR} ตามมาตรฐาน วสท.)*"
        )
    with req_col2:
        st.success(
            f"**แนะนำสเต็ปตู้ APFC:** 5 สเต็ป | สเต็ปละ {market_step_size} kVAR\n\n"
            f"*พิกัดรวมติดตั้งจริง (Installed Capacity): **{installed_Qc} kVAR***"
        )

# ── Tab 2: Power Triangle ───────────────────────────────
with tab2:
    st.subheader("กราฟสามเหลี่ยมกำลังไฟฟ้า")

    fig = go.Figure()

    # สามเหลี่ยมก่อนปรับปรุง
    fig.add_trace(go.Scatter(
        x=[0, P, P, 0], y=[0, 0, Q1, 0],
        fill="toself",
        name=f"ก่อนปรับปรุง (PF={pf1})",
        marker=dict(color="rgba(255, 99, 132, 0.5)")
    ))

    # สามเหลี่ยมหลังปรับปรุง
    fig.add_trace(go.Scatter(
        x=[0, P, P, 0], y=[0, 0, Q2, 0],
        fill="toself",
        name=f"หลังปรับปรุง (PF={pf2})",
        marker=dict(color="rgba(75, 192, 192, 0.7)")
    ))

    # ✅ เส้นแสดงขนาด Qc ที่ติดตั้ง พร้อม annotation
    fig.add_trace(go.Scatter(
        x=[P, P], y=[Q2, Q1],
        mode="lines",
        line=dict(color="orange", width=3, dash="dash"),
        name=f"Qc = {Qc_total:.1f} kVAR"
    ))
    fig.add_annotation(
        x=P, y=(Q1 + Q2) / 2,
        text=f"  Qc = {Qc_total:.1f} kVAR",
        showarrow=True, arrowhead=2,
        arrowcolor="orange", font=dict(color="orange", size=13),
        xshift=10
    )

    fig.update_layout(
        title="ความสัมพันธ์ระหว่าง Active (P) และ Reactive (Q) Power",
        xaxis_title="Active Power (kW)",
        yaxis_title="Reactive Power (kVAR)",
        showlegend=True,
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Tab 3: ความคุ้มทุน & สิ่งแวดล้อม ───────────────────
with tab3:
    st.subheader("การประเมินจุดคุ้มทุน (Payback Period)")

    fin_col1, fin_col2, fin_col3 = st.columns(3)
    fin_col1.metric("งบประมาณลงทุนรวม",        f"{total_investment:,.2f} บาท",       f"{installed_Qc} kVAR รวมติดตั้ง")
    fin_col2.metric("ประหยัดค่าปรับ (รายเดือน)", f"{monthly_penalty_saved:,.2f} บาท/เดือน")
    fin_col3.metric("ระยะเวลาคืนทุนโดยประมาณ",  f"{payback_months:.1f} เดือน")

    st.divider()
    st.subheader("🌍 ผลกระทบเชิงบวกต่อสิ่งแวดล้อม")
    st.write(f"- **ลดกำลังสูญเสียในสายส่ง:** {loss_reduction_kW:.3f} kW")
    st.write(f"- **ประหยัดพลังงาน:** {energy_saved_kWh:,.2f} kWh/ปี  "
             f"*(คำนวณจาก {OPERATING_HOURS:,} ชม./ปี)*")
    st.write(f"- **ลดปริมาณ CO₂:** {co2_reduced_kg:,.2f} kgCO₂e/ปี  "
             f"*(ค่า Emission Factor: {CO2_FACTOR} kgCO₂/kWh)*")

# ---------------------------------------------------------
# ส่วนที่ 4: ส่งออกรายงาน
# ---------------------------------------------------------
st.divider()
st.subheader("📄 ส่งออกรายงาน")

harmonics_status = ("มีการตรวจพบ (แนะนำใช้ Detuned Reactor 7%)"
                    if has_harmonics else "ปกติ (Linear Load)")

report_text = f"""รายงานวิเคราะห์การปรับปรุง Power Factor & จุดคุ้มทุน
==================================================
[พารามิเตอร์ระบบ]
  ระบบ              : {phase_type}
  กำลังไฟฟ้าจริง P  : {P} kW
  แรงดัน V          : {V} V
  ความถี่ f         : {f} Hz
  Power Factor      : {pf1} → {pf2}
  สถานะ Harmonics   : {harmonics_status}

[ผลการคำนวณ]
  Qc ที่ต้องชดเชย   : {Qc_total:.2f} kVAR
  Apparent Power ลด  : {S1:.2f} → {S2:.2f} kVA  (ลด {S1-S2:.2f} kVA)
  กระแสพิกัด Ic      : {I_c:.2f} A
  ขนาดตัวเก็บประจุ C : {C_microfarad:.2f} µF

[สเปคการติดตั้งที่แนะนำ]
  Capacitor Bank     : 5 สเต็ป × {market_step_size} kVAR = {installed_Qc} kVAR
  เซอร์กิตเบรกเกอร์  : {recommended_cb} AT  (พิกัดคำนวณ {cb_rating_calc:.1f} A × {CB_SAFETY_FACTOR})

[การวิเคราะห์ความคุ้มทุน (ROI)]
  งบประมาณลงทุนรวม    : {total_investment:,.2f} บาท
  ประหยัดค่าปรับ/เดือน : {monthly_penalty_saved:,.2f} บาท
  ระยะเวลาคืนทุน       : {payback_months:.1f} เดือน

[ผลกระทบต่อสิ่งแวดล้อม]
  ลดกำลังสูญเสีย       : {loss_reduction_kW:.3f} kW
  ประหยัดพลังงาน       : {energy_saved_kWh:,.2f} kWh/ปี
  ลด CO₂               : {co2_reduced_kg:,.2f} kgCO₂e/ปี
==================================================
*สร้างโดยระบบ Advanced PFC Analyzer (Python & Streamlit)*
"""

st.download_button(
    label="📥 ดาวน์โหลดรายงานฉบับสมบูรณ์ (.txt)",
    data=report_text,
    file_name="PFC_Full_Report.txt",
    mime="text/plain",
    type="primary"
)
