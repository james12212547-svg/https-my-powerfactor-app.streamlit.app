import streamlit as st
import math

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Power Factor Calculator", layout="centered")

st.title("⚡ โปรแกรมคำนวณปรับปรุง Power Factor")
st.markdown("โปรแกรมสำหรับคำนวณหาขนาด Capacitor เพื่อปรับปรุงค่า PF ให้ได้ตามเป้าหมาย (รองรับ 1 เฟส และ 3 เฟส)")

st.divider()

# สร้าง Layout แบ่งเป็น 2 คอลัมน์สำหรับรับค่า Input
col1, col2 = st.columns(2)

with col1:
    st.subheader("พารามิเตอร์ระบบ")
    # เพิ่มตัวเลือก ระบบไฟฟ้า
    phase_type = st.radio("ระบบไฟฟ้า", ["1 เฟส", "3 เฟส"], horizontal=True)
    
    P = st.number_input("กำลังไฟฟ้าจริง P (kW)", min_value=0.1, value=10.0, step=0.5)
    
    # ถ้าเลือก 3 เฟส ให้ค่าเริ่มต้นแรงดันเป็น 380V (Line-to-Line) ถ้า 1 เฟสเป็น 220V
    default_v = 380 if phase_type == "3 เฟส" else 220
    V = st.number_input("แรงดันไฟฟ้า V (Volt)", min_value=1, value=default_v)
    
    f = st.number_input("ความถี่ f (Hz)", min_value=1, value=50)

with col2:
    st.subheader("เป้าหมายการปรับปรุง")
    pf1 = st.number_input("Power Factor เดิม", min_value=0.10, max_value=0.99, value=0.70, step=0.01)
    pf2 = st.number_input("Power Factor เป้าหมาย", min_value=0.10, max_value=1.00, value=0.95, step=0.01)

st.divider()

# ปุ่มกดคำนวณ
if st.button("🧮 คำนวณขนาด Capacitor", type="primary", use_container_width=True):
    if pf2 <= pf1:
        st.error("⚠️ Power Factor เป้าหมาย ต้องมีค่ามากกว่า Power Factor เดิมครับ")
    else:
        # 1. หาระยะห่างของมุมเฟส
        theta1 = math.acos(pf1)
        theta2 = math.acos(pf2)
        
        # 2. คำนวณหา Qc รวม (kVAR)
        Qc_total = P * (math.tan(theta1) - math.tan(theta2))
        
        # 3. คำนวณหา ค่า C (Farad) -> แปลงเป็น Microfarad (µF)
        if phase_type == "1 เฟส":
            C_farad = (Qc_total * 1000) / (2 * math.pi * f * (V**2))
            phase_text = "ต่อ 1 ระบบ"
        else:
            # สำหรับ 3 เฟส นิยมต่อ Capacitor แบบ Delta 
            C_farad = (Qc_total * 1000) / (3 * 2 * math.pi * f * (V**2))
            phase_text = "ต่อ 1 เฟส (ต้องใช้ 3 ตัวต่อแบบ Delta)"
            
        C_microfarad = C_farad * 1_000_000
        
        # แสดงผลลัพธ์
        st.success(f"✅ คำนวณสำเร็จ! สำหรับระบบ {phase_type}")
        
        res_col1, res_col2 = st.columns(2)
        res_col1.metric("รีแอคทีฟที่ต้องชดเชยรวม (Qc)", f"{Qc_total:.2f} kVAR")
        res_col2.metric(f"ขนาด Capacitor ({phase_text})", f"{C_microfarad:.2f} µF")
        
        # เพิ่มคำอธิบายเพิ่มเติมสำหรับ 3 เฟส
        if phase_type == "3 เฟส":
            st.info("💡 หมายเหตุ: การคำนวณขนาด $\mu F$ สำหรับ 3 เฟสในแอปนี้ อ้างอิงจากการต่อตัวเก็บประจุแบบเดลต้า (Delta Connection) ซึ่งเป็นรูปแบบมาตรฐานที่นิยมใช้ใน Capacitor Bank")