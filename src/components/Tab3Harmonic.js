"use client";

import { check_harmonic_resonance, analyze_harmonics_ieee519 } from "../utils/engineering";

export default function Tab3Harmonic({ inputs, qcTotal }) {
  const resonance = check_harmonic_resonance(qcTotal, inputs.trafoKva, inputs.zPercent, inputs.voltage);
  
  let ieee519 = null;
  if (inputs.enableIeee519) {
    ieee519 = analyze_harmonics_ieee519(
      inputs.thdiPct, 
      inputs.thdvPct, 
      inputs.iscIl, 
      inputs.vlKey
    );
  }

  const MetricCard = ({ label, value, icon, color }) => (
    <div style={{
      background: 'var(--surface-color)',
      border: `1px solid ${color}30`,
      borderLeft: `3px solid ${color}`,
      borderRadius: '8px',
      padding: '1rem 1.25rem',
      flex: '1',
      minWidth: '200px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    }}>
      <div style={{ fontSize: '0.75rem', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span>{icon}</span> {label}
      </div>
      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: color, textShadow: `0 0 10px ${color}40` }}>
        {value}
      </div>
    </div>
  );

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {inputs.enableIeee519 ? (
        <div>
          <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
            📡 การวิเคราะห์ฮาร์มอนิก IEEE 519-2014
          </h3>
          
          <div style={{ 
            background: 'var(--surface-color)', 
            border: `2px solid ${ieee519.overall_status.includes('PASS') ? '#10b981' : '#ef4444'}`, 
            borderRadius: '14px', 
            padding: '20px 28px', 
            marginBottom: '16px', 
            textAlign: 'center' 
          }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: ieee519.overall_status.includes('PASS') ? '#10b981' : '#ef4444' }}>
              {ieee519.overall_status}
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>IEEE 519-2014 Compliance Result</div>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
            <MetricCard 
              label="THDi วัดได้" 
              value={`${inputs.thdiPct.toFixed(1)}%`} 
              icon="📉" 
              color={ieee519.current_compliant ? '#10b981' : '#f97316'} 
            />
            <MetricCard 
              label="THDv วัดได้" 
              value={`${inputs.thdvPct.toFixed(1)}%`} 
              icon="📉" 
              color={ieee519.voltage_compliant ? '#10b981' : '#f97316'} 
            />
            <MetricCard 
              label="ISC/IL RATIO" 
              value={inputs.iscIl} 
              icon="⚡" 
              color="#0ea5e9" 
            />
          </div>

          <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
            ตารางความสอดคล้องมาตรฐาน IEEE 519
          </h3>
          <div style={{ background: 'var(--surface-color)', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-color)', marginBottom: '2rem' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead style={{ background: 'var(--border-color)', color: 'var(--text-muted)' }}>
                <tr>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>พารามิเตอร์</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>ค่าที่วัดได้</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>เกณฑ์ IEEE 519</th>
                  <th style={{ padding: '0.75rem', textAlign: 'left' }}>สถานะ</th>
                </tr>
              </thead>
              <tbody>
                {ieee519.compliance_table.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem' }}>{row["พารามิเตอร์"]}</td>
                    <td style={{ padding: '0.75rem' }}>{row["ค่าที่วัดได้"]}</td>
                    <td style={{ padding: '0.75rem' }}>{row["เกณฑ์ IEEE 519"]}</td>
                    <td style={{ padding: '0.75rem', fontWeight: 'bold', color: row["สถานะ"].includes('ผ่าน') && !row["สถานะ"].includes('ไม่ผ่าน') ? '#10b981' : '#ef4444' }}>{row["สถานะ"]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
            คำแนะนำ
          </h3>
          <ul style={{ marginLeft: '1.5rem', marginBottom: '1.5rem', color: 'var(--text-main)', fontSize: '0.9rem' }}>
            {ieee519.recommendations.map((rec, idx) => (
              <li key={idx} style={{ marginBottom: '0.5rem' }}>{rec}</li>
            ))}
          </ul>

          {ieee519.filter_recommendation !== "ไม่จำเป็น" && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid #ef4444', padding: '1rem', borderRadius: '8px', color: 'var(--text-main)' }}>
                🔧 <strong>อุปกรณ์ที่แนะนำ:</strong> <span style={{ color: '#ef4444' }}>{ieee519.filter_recommendation}</span>
              </div>
              <div style={{ background: 'rgba(245, 158, 11, 0.1)', borderLeft: '4px solid #f59e0b', padding: '1rem', borderRadius: '8px', color: 'var(--text-main)' }}>
                💰 <strong>ประมาณงบประมาณ:</strong> <span style={{ color: '#f59e0b' }}>{ieee519.filter_cost_estimate}</span>
              </div>
            </div>
          )}

        </div>
      ) : (
        <div>
          <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
            📡 การวิเคราะห์ฮาร์มอนิก IEEE 519-2014
          </h3>
          <div style={{ background: 'rgba(14, 165, 233, 0.1)', borderLeft: '4px solid #0ea5e9', padding: '1rem', borderRadius: '8px', marginBottom: '2rem', color: 'var(--text-main)' }}>
            ⚡ เปิดใช้งาน <strong>'การวิเคราะห์ IEEE 519'</strong> ในแถบตั้งค่าด้านซ้าย (หมวด 4) เพื่อดูผลการวิเคราะห์
          </div>

          <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
            ⚠️ ผลการประเมินเบื้องต้น (จากสเปคหม้อแปลง)
          </h3>
          
          {resonance.risk === "High" ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid #ef4444', padding: '1rem', borderRadius: '8px', color: 'var(--text-main)' }}>
                ⚠️ {resonance.message}
              </div>
              <div style={{ background: 'rgba(245, 158, 11, 0.1)', borderLeft: '4px solid #f59e0b', padding: '1rem', borderRadius: '8px', color: 'var(--text-main)' }}>
                🔧 แนะนำ <strong>Detuned Reactor</strong> สเปค: {resonance.tuning_factor}
              </div>
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid #ef4444', padding: '1rem', borderRadius: '8px', color: 'var(--text-main)' }}>
                📌 แรงดันขั้วคาปา (Uc): <strong>{resonance.u_c_voltage.toFixed(1)} V</strong> — ต้องใช้ Capacitor ≥ 440V
              </div>
            </div>
          ) : (
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', borderLeft: '4px solid #10b981', padding: '1rem', borderRadius: '8px', color: 'var(--text-main)' }}>
              ✅ {resonance.message}
            </div>
          )}
        </div>
      )}

    </div>
  );
}
