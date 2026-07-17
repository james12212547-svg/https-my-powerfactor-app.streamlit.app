"use client";

import { useState } from "react";
import { calculate_roi } from "../utils/financial";

export default function Tab5ROI({ inputs, qcTotal }) {
  const [showExpander, setShowExpander] = useState(false);

  // Use the full calculate_roi with all inputs from the sidebar!
  const roi = calculate_roi(
    inputs.pKw, 
    inputs.pf1, 
    inputs.pf2, 
    qcTotal, 
    inputs.penaltyRate, 
    inputs.costPerKvar,
    inputs.energyRate,
    inputs.demandCharge,
    inputs.enableLoadProfile ? inputs.pBase : 0.0,
    inputs.enableLoadProfile ? inputs.pfBase : 1.0,
    inputs.enableLoadProfile ? inputs.hrsPeak : 24.0,
    inputs.enableLoadProfile ? inputs.hrsBase : 0.0
  );

  const co2_reduction_kg = roi.energy_saved_kwh_yr * 0.4999;

  return (
    <div className="animate-fade-in" style={{ padding: '1rem 0' }}>
      <h3 style={{ fontSize: '1.2rem', color: '#0ea5e9', marginBottom: '1.5rem' }}>
        ผลตอบแทนทางการเงินและสิ่งแวดล้อม (ต่อปี)
      </h3>
      
      {/* Expander */}
      <div style={{ marginBottom: '2rem', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
        <button 
          onClick={() => setShowExpander(!showExpander)}
          style={{ width: '100%', padding: '1rem', background: 'var(--surface-color)', border: 'none', textAlign: 'left', color: 'var(--text-main)', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
        >
          <span>ℹ️ ข้อกำหนดค่าปรับ Power Factor จากการไฟฟ้า (PEA/MEA)</span>
          <span>{showExpander ? '▲' : '▼'}</span>
        </button>
        {showExpander && (
          <div style={{ padding: '1rem', background: 'var(--bg-color)', color: 'var(--text-muted)', fontSize: '0.9rem', borderTop: '1px solid var(--border-color)' }}>
            <p style={{ marginBottom: '0.5rem' }}><strong>หลักเกณฑ์การคิดค่าปรับ:</strong></p>
            <p style={{ marginBottom: '1rem' }}>การไฟฟ้าส่วนภูมิภาค (PEA) และการไฟฟ้านครหลวง (MEA) กำหนดให้ผู้ใช้ไฟฟ้าประเภทกิจการขนาดกลาง (ประเภทที่ 3) กิจการขนาดใหญ่ (ประเภทที่ 4) และกิจการเฉพาะอย่าง (ประเภทที่ 5-7) จะถูกเรียกเก็บ <strong>"ค่าปรับเพาเวอร์แฟกเตอร์"</strong> หากมีการดึงกำลังไฟฟ้ารีแอคทีฟเกินกว่า <strong>ร้อยละ 61.97</strong> ของความต้องการพลังไฟฟ้าสูงสุดในรอบเดือน</p>
            <p><strong>อัตราค่าปรับ:</strong> ถูกกำหนดไว้ที่ <strong>56.07 บาทต่อกิโลวาร์ (kVAR)</strong> สำหรับส่วนที่เกินในแต่ละเดือน</p>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        
        {/* Column 1: ROI */}
        <div>
          <div style={{ background: 'rgba(5, 150, 105, 0.08)', border: '1px solid rgba(5, 150, 105, 0.3)', borderRadius: '14px', padding: '20px 24px', marginBottom: '16px' }}>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: '#10b981', letterSpacing: '1.5px', marginBottom: '16px' }}>
              💰 ผลตอบแทนการลงทุน (ROI)
            </div>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginLeft: '0.5rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>ประมาณการเงินลงทุน (ตู้ CAP)</div>
              <div style={{ fontSize: '1.8rem', color: 'var(--text-main)', fontFamily: 'monospace' }}>฿ {roi.investment_thb.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>ประหยัดเงินได้รวม</div>
              <div style={{ fontSize: '1.8rem', color: 'var(--text-main)', fontFamily: 'monospace' }}>฿ {roi.yearly_saving_thb.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} / ปี</div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>ระยะเวลาคืนทุน (ประมาณ)</div>
              <div style={{ fontSize: '1.8rem', color: 'var(--text-main)', fontFamily: 'monospace' }}>{roi.payback_months.toFixed(1)} เดือน</div>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>รวมค่าปรับที่หลีกเลี่ยงได้ และพลังงาน/KVA ที่ประหยัดได้</div>
          </div>
        </div>

        {/* Column 2: Environment */}
        <div>
          <div style={{ background: 'rgba(2, 132, 199, 0.08)', border: '1px solid rgba(2, 132, 199, 0.3)', borderRadius: '14px', padding: '20px 24px', marginBottom: '16px' }}>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '0.75rem', color: '#0ea5e9', letterSpacing: '1.5px', marginBottom: '16px' }}>
              🌍 ผลกระทบเชิงบวกต่อสิ่งแวดล้อม
            </div>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginLeft: '0.5rem' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>พลังงานที่ประหยัดได้ (LINE LOSS)</div>
              <div style={{ fontSize: '1.8rem', color: 'var(--text-main)', fontFamily: 'monospace' }}>{roi.energy_saved_kwh_yr.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} kWh/ปี</div>
            </div>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>ลดการปล่อยคาร์บอน</div>
              <div style={{ fontSize: '1.8rem', color: 'var(--text-main)', fontFamily: 'monospace' }}>{co2_reduction_kg.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} kgCO2e/ปี</div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
