"use client";

import { Printer } from "lucide-react";
import jsPDF from "jspdf";
import "jspdf-autotable";
import { calculate_q_and_c, calculate_detail_engineering } from "../utils/engineering";

export default function Tab7Solar({ inputs, qcTotal }) {
  const generatePDF = () => {
    const doc = new jsPDF();
    
    doc.setFontSize(18);
    doc.text("PFC PRO ANALYZER - Engineering Report", 14, 20);
    
    doc.setFontSize(12);
    doc.text(`Project Parameters:`, 14, 30);
    
    const params = [
      ["Parameter", "Value"],
      ["System Phase", `${inputs.phase} Phase`],
      ["Active Power (kW)", `${inputs.pKw} kW`],
      ["Current PF", `${inputs.pf1}`],
      ["Target PF", `${inputs.pf2}`],
      ["Voltage (V)", `${inputs.voltage} V`],
      ["Frequency (Hz)", `${inputs.frequency} Hz`],
    ];
    
    doc.autoTable({
      startY: 35,
      head: [params[0]],
      body: params.slice(1),
      theme: 'grid',
    });

    const q_and_c = calculate_q_and_c(inputs.pKw, inputs.voltage, inputs.frequency, inputs.pf1, inputs.pf2, inputs.phase);
    const detail = calculate_detail_engineering(q_and_c.I_c_A, q_and_c.I_load_A, qcTotal, inputs.trafoKva, inputs.zPercent);

    doc.text(`Engineering Results:`, 14, doc.lastAutoTable.finalY + 10);
    const engData = [
      ["Metric", "Value"],
      ["Required Qc (kVAR)", `${qcTotal.toFixed(2)} kVAR`],
      ["Capacitance (uF)", `${q_and_c.C_microfarad.toFixed(2)} uF`],
      ["Capacitor Current (A)", `${q_and_c.I_c_A.toFixed(2)} A`],
      ["Main Breaker (AT)", `${q_and_c.recommended_cb_AT} AT`],
      ["Cable Size", `${detail.cable_size}`],
      ["CT Ratio", `${detail.ct_ratio}`],
      ["Voltage Rise (%)", `${detail.voltage_rise_pct.toFixed(2)} %`],
    ];

    doc.autoTable({
      startY: doc.lastAutoTable.finalY + 15,
      head: [engData[0]],
      body: engData.slice(1),
      theme: 'striped',
    });

    doc.save("PFC_Engineering_Report.pdf");
  };

  return (
    <div className="animate-fade-in" style={{ padding: '1rem 0' }}>
      <h3 style={{ fontSize: '0.9rem', color: '#f97316', marginBottom: '1rem', textTransform: 'uppercase' }}>
        ☀️ 7. ผลกระทบของ Solar PV ต่อค่า Power Factor
      </h3>

      <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)', marginBottom: '2rem' }}>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem' }}>
          โรงงานที่ติดตั้ง Solar PV Rooftop มักประสบปัญหาค่า Power Factor ตกต่ำลงอย่างรุนแรง และถูกการไฟฟ้าฯ ปรับเงิน ทั้งที่ไม่เคยโดนปรับมาก่อน
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          <strong style={{ color: 'var(--text-main)' }}>กลไกที่เกิดขึ้น:</strong> อินเวอร์เตอร์โซลาร์เซลล์โดยทั่วไปจะอัดฉีดเฉพาะกำลังไฟฟ้าจริง (kW) แต่ไม่จ่ายกำลังไฟฟ้ารีแอคทีฟ (kVar) ทำให้โรงงานดึง kW จากการไฟฟ้าน้อยลง แต่ยังคงดึง kVar เท่าเดิม สัดส่วน kVar/kW จึงพุ่งสูงขึ้นจนทะลุเกณฑ์ของการไฟฟ้าฯ
        </p>
      </div>

      <h4 style={{ fontSize: '0.9rem', color: 'var(--primary)', marginBottom: '1rem', textTransform: 'uppercase' }}>
        🛠️ กลยุทธ์การแก้ปัญหา (Mitigation Strategies)
      </h4>

      <div style={{ overflowX: 'auto', marginBottom: '2rem' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
          <thead style={{ background: 'var(--border-color)', color: 'var(--text-muted)' }}>
            <tr>
              <th style={{ padding: '1rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>กลยุทธ์</th>
              <th style={{ padding: '1rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>กลไก</th>
              <th style={{ padding: '1rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>งบประมาณ</th>
              <th style={{ padding: '1rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>ความเหมาะสม</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>1. ย้ายจุดเชื่อมต่อโซลาร์ / ย้าย CT</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>ย้าย CT ของตู้ Cap Bank ให้มาอยู่ก่อนจุดที่โซลาร์เซลล์จะจ่ายไฟ</td>
              <td style={{ padding: '1rem' }}>ต่ำ (5k - 30k)</td>
              <td style={{ padding: '1rem' }}>ตู้ Cap Bank เดิมยังมีสภาพดี</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>2. อัพเกรดเป็น APFC แบบ 4-Quadrant</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>เปลี่ยนรีเลย์ให้เป็นรุ่นที่วัดกระแสย้อนกลับได้</td>
              <td style={{ padding: '1rem' }}>ปานกลาง (50k - 200k)</td>
              <td style={{ padding: '1rem' }}>ตู้เก่าใช้รีเลย์ที่ไม่รองรับโหลดสองทิศทาง</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>3. โหมดชดเชย kVar จาก Inverter</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>ตั้งค่าอินเวอร์เตอร์โซลาร์ให้จ่าย kVar ออกมาช่วย</td>
              <td style={{ padding: '1rem' }}>0 บาท (เสีย kW 5-10%)</td>
              <td style={{ padding: '1rem' }}>อินเวอร์เตอร์รองรับ</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>4. ติดตั้ง Static Var Generator (SVG)</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>ใช้อิเล็กทรอนิกส์กำลังชดเชย kVar แบบ Stepless</td>
              <td style={{ padding: '1rem' }}>สูง (&gt; 1 ล้านบาท)</td>
              <td style={{ padding: '1rem' }}>โหลดผันผวนสูงมาก</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h4 style={{ color: 'var(--text-main)', margin: 0, marginBottom: '0.25rem' }}>📄 ออกรายงานวิศวกรรม PDF</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>ดาวน์โหลดรายงานผลการคำนวณทั้งหมดเพื่อนำไปใช้อ้างอิง</p>
        </div>
        <button onClick={generatePDF} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Printer size={16} /> สร้างรายงาน PDF
        </button>
      </div>

    </div>
  );
}
