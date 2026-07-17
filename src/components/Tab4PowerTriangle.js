"use client";

import { calculate_q_and_c } from "../utils/engineering";

export default function Tab4PowerTriangle({ inputs }) {
  const { pKw, pf1, pf2, phase, voltage, frequency } = inputs;
  const res = calculate_q_and_c(pKw, voltage, frequency, pf1, pf2, phase);
  
  // S1 = Initial Apparent Power, S2 = Final Apparent Power
  // Q1 = Initial Reactive Power, Q2 = Final Reactive Power
  // P = Real Power (Constant)
  const P = pKw;
  const S1 = res.S1;
  const S2 = res.S2;
  const Q1 = res.Q1;
  const Q2 = res.Q2;
  const Qc = res.Qc_total_kVAR;

  // Scale factors for SVG
  // Max width 600, max height 400
  const maxWidth = 500;
  const maxHeight = 300;
  const scale = Math.min(maxWidth / P, maxHeight / Q1);
  
  const wP = P * scale;
  const hQ1 = Q1 * scale;
  const hQ2 = Q2 * scale;
  const hQc = Qc * scale;

  return (
    <div className="animate-fade-in" style={{ padding: '1rem 0' }}>
      <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase' }}>
        📐 4. Power Triangle (กราฟสามเหลี่ยมกำลังไฟฟ้า)
      </h3>

      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', alignItems: 'center' }}>
        
        {/* SVG Drawing */}
        <div style={{ flex: '1 1 400px', background: 'var(--surface-color)', borderRadius: '8px', padding: '2rem', display: 'flex', justifyContent: 'center' }}>
          <svg width={wP + 50} height={hQ1 + 50} style={{ overflow: 'visible' }}>
            {/* Real Power (P) - Horizontal */}
            <line x1={0} y1={hQ1} x2={wP} y2={hQ1} stroke="#10b981" strokeWidth={3} />
            <text x={wP/2} y={hQ1 + 25} fill="#10b981" fontSize="14" textAnchor="middle">P = {P.toFixed(1)} kW</text>

            {/* Initial Reactive Power (Q1) - Vertical */}
            <line x1={wP} y1={hQ1} x2={wP} y2={0} stroke="#ef4444" strokeWidth={2} strokeDasharray="5,5" />
            <text x={wP + 10} y={hQ1/2} fill="#ef4444" fontSize="14">Q1 = {Q1.toFixed(1)} kVAR</text>

            {/* Initial Apparent Power (S1) - Hypotenuse */}
            <line x1={0} y1={hQ1} x2={wP} y2={0} stroke="#64748b" strokeWidth={2} strokeDasharray="5,5" />
            
            {/* Final Reactive Power (Q2) - Vertical */}
            <line x1={wP} y1={hQ1} x2={wP} y2={hQ1 - hQ2} stroke="#3b82f6" strokeWidth={3} />
            <text x={wP + 10} y={hQ1 - hQ2/2} fill="#3b82f6" fontSize="14">Q2 = {Q2.toFixed(1)} kVAR</text>

            {/* Final Apparent Power (S2) - Hypotenuse */}
            <line x1={0} y1={hQ1} x2={wP} y2={hQ1 - hQ2} stroke="#0ea5e9" strokeWidth={3} />
            
            {/* Cap Bank (Qc) - Downwards Arrow */}
            <line x1={wP - 10} y1={0} x2={wP - 10} y2={hQ1 - hQ2} stroke="#f59e0b" strokeWidth={3} markerEnd="url(#arrow)" />
            <text x={wP - 20} y={hQ1 - hQc/2} fill="#f59e0b" fontSize="14" textAnchor="end">Qc = {Qc.toFixed(1)} kVAR</text>

            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
              </marker>
            </defs>
          </svg>
        </div>

        {/* Legend */}
        <div style={{ flex: '1 1 250px' }}>
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <li style={{ color: '#10b981', display: 'flex', gap: '1rem' }}>
              <strong>P:</strong> <span>Real Power (คงที่ตลอดการทำงาน)</span>
            </li>
            <li style={{ color: '#64748b', display: 'flex', gap: '1rem' }}>
              <strong>S1:</strong> <span>Apparent Power เดิม (ก่อนปรับปรุง) = {S1.toFixed(1)} kVA</span>
            </li>
            <li style={{ color: '#0ea5e9', display: 'flex', gap: '1rem' }}>
              <strong>S2:</strong> <span>Apparent Power ใหม่ (หลังปรับปรุง) = {S2.toFixed(1)} kVA</span>
            </li>
            <li style={{ color: '#ef4444', display: 'flex', gap: '1rem' }}>
              <strong>Q1:</strong> <span>Reactive Power เดิม = {Q1.toFixed(1)} kVAR</span>
            </li>
            <li style={{ color: '#3b82f6', display: 'flex', gap: '1rem' }}>
              <strong>Q2:</strong> <span>Reactive Power ใหม่ = {Q2.toFixed(1)} kVAR</span>
            </li>
            <li style={{ color: '#f59e0b', display: 'flex', gap: '1rem' }}>
              <strong>Qc:</strong> <span>ขนาด Capacitor Bank = {Qc.toFixed(1)} kVAR</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
