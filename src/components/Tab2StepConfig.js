"use client";

import { calculate_cap_steps } from "../utils/engineering";

export default function Tab2StepConfig({ qcTotal, inputs }) {
  // Use inputs.numStepsPref if provided, default to 5
  const numSteps = inputs?.numStepsPref || 5;
  const stepsResult = calculate_cap_steps(qcTotal, numSteps);

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
    <div className="animate-fade-in">
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
          🔋 การจัดสเต็ปคาปาซิเตอร์ (SMART STEP CONFIGURATION)
        </h3>
        
        {stepsResult ? (
          <>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
              <MetricCard 
                label="รูปแบบที่ดีที่สุด" 
                value={`${stepsResult.pattern_name} (${stepsResult.steps_kvar.length} สเต็ป)`} 
                icon="⏳" 
                color="#10b981" 
              />
              <MetricCard 
                label="kVAR ที่สร้าง" 
                value={`${stepsResult.total_achieved_kvar.toFixed(1)} kVAR`} 
                icon="✅" 
                color="#0ea5e9" 
              />
              <MetricCard 
                label="COVERAGE" 
                value={`${((stepsResult.total_achieved_kvar / qcTotal) * 100).toFixed(1)}%`} 
                icon="📊" 
                color="#8b5cf6" 
              />
            </div>

            <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
              รายการสเต็ปที่แนะนำ
            </h3>
            
            <div style={{ background: 'var(--surface-color)', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                <thead style={{ background: 'var(--border-color)', color: 'var(--text-muted)' }}>
                  <tr>
                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>ขนาด (kVAR)</th>
                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>หมายเหตุ</th>
                  </tr>
                </thead>
                <tbody>
                  {stepsResult.steps_kvar.map((step, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.75rem' }}>{step}</td>
                      <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>
                        {inputs?.useDetuned ? 'Capacitor with Detuned Reactor 7%' : 'Dry Film Capacitor'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p>รอข้อมูล Qc...</p>
        )}
      </div>
    </div>
  );
}
