"use client";

import { calculate_q_and_c, calculate_detail_engineering } from "../utils/engineering";

export default function Tab1Engineering({ inputs }) {
  const q_and_c_results = calculate_q_and_c(
    inputs.pKw, inputs.voltage, inputs.frequency, inputs.pf1, inputs.pf2, inputs.phase
  );

  const detail_results = calculate_detail_engineering(
    q_and_c_results.I_c_A, 
    q_and_c_results.I_load_A, 
    q_and_c_results.Qc_total_kVAR, 
    inputs.trafoKva, 
    inputs.zPercent
  );

  const MetricCard = ({ label, value, icon, color }) => (
    <div style={{
      background: 'var(--surface-color)',
      border: `1px solid ${color}30`,
      borderLeft: `3px solid ${color}`,
      borderRadius: '8px',
      padding: '1rem 1.25rem',
      flex: '1',
      minWidth: '200px'
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
          1. พิกัดกำลังไฟฟ้า (Power Sizing)
        </h3>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <MetricCard 
            label="Qc ที่ต้องการ" 
            value={`${q_and_c_results.Qc_total_kVAR.toFixed(2)} kVAR`} 
            icon="🔋" 
            color="#10b981" 
          />
          <MetricCard 
            label="คาปาซิแตนซ์" 
            value={`${q_and_c_results.C_microfarad.toFixed(2)} µF`} 
            icon="⚙️" 
            color="#0ea5e9" 
          />
          <MetricCard 
            label="กระแส Capacitor (In)" 
            value={`${q_and_c_results.I_c_A.toFixed(2)} A`} 
            icon="⚡" 
            color="#8b5cf6" 
          />
          <MetricCard 
            label="กระแสโหลดรวม (I_load)" 
            value={`${q_and_c_results.I_load_A.toFixed(2)} A`} 
            icon="🏭" 
            color="#9ca3af" 
          />
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          2. มาตรฐานสวิตช์เกียร์และสายไฟ (วสท. 022001-22) <span style={{ cursor: 'pointer' }}>🔗</span>
        </h3>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <MetricCard 
            label="สายไฟเมน (≥ 1.35 In)" 
            value={detail_results.cable_size} 
            icon="🔌" 
            color="#10b981" 
          />
          <MetricCard 
            label="Main Breaker (≥ 1.43 In)" 
            value={`${q_and_c_results.recommended_cb_AT} AT`} 
            icon="🔴" 
            color="#f97316" 
          />
          <MetricCard 
            label="พิกัด HRC (≥ 1.65 In)" 
            value={`${detail_results.fuse_amp_req.toFixed(1)} A`} 
            icon="📍" 
            color="#3b82f6" 
          />
        </div>
      </div>

    </div>
  );
}
