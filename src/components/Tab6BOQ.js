"use client";

import { generate_boq } from "../utils/financial";
import { calculate_q_and_c, calculate_detail_engineering, calculate_cap_steps } from "../utils/engineering";
import * as XLSX from 'xlsx';
import { Download } from "lucide-react";

export default function Tab6BOQ({ inputs, qcTotal }) {
  // Re-calculate some stuff because BOQ needs everything
  const q_and_c = calculate_q_and_c(inputs.pKw, inputs.voltage, inputs.frequency, inputs.pf1, inputs.pf2, inputs.phase);
  const detail = calculate_detail_engineering(q_and_c.I_c_A, q_and_c.I_load_A, qcTotal, inputs.trafoKva, inputs.zPercent);
  const steps_config = calculate_cap_steps(qcTotal, inputs.numStepsPref);

  const boq = generate_boq(
    qcTotal, 
    steps_config, 
    q_and_c.I_c_A, 
    q_and_c.I_load_A, 
    detail.cable_size, 
    q_and_c.recommended_cb_AT, 
    detail.fuse_amp_req, 
    detail.ct_ratio, 
    inputs.useDetuned, // Corrected to use inputs from sidebar
    inputs.overheadPct
  );

  const exportToExcel = () => {
    const ws_data = boq.line_items;
    const ws = XLSX.utils.json_to_sheet(ws_data);
    
    const summary_data = [
      { "หมวด": "วัสดุและอุปกรณ์", "จำนวน (บาท)": boq.material_total },
      { "หมวด": "ค่าแรงติดตั้ง", "จำนวน (บาท)": boq.labor_cost },
      { "หมวด": "ค่าวิศวกรรม", "จำนวน (บาท)": boq.engineering_cost },
      { "หมวด": "Overhead/Profit", "จำนวน (บาท)": boq.overhead },
      { "หมวด": "ยอดรวมสุทธิ", "จำนวน (บาท)": boq.grand_total }
    ];
    const ws_summary = XLSX.utils.json_to_sheet(summary_data);
    
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "BOQ Items");
    XLSX.utils.book_append_sheet(wb, ws_summary, "Summary");
    
    XLSX.writeFile(wb, "PFC_BOQ_Report.xlsx");
  };

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
    <div className="animate-fade-in" style={{ padding: '1rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', color: '#0ea5e9', textTransform: 'uppercase', margin: 0 }}>
          📋 BILL OF QUANTITIES (BOQ) / ใบเสนอราคาเบื้องต้น
        </h3>
        <button onClick={exportToExcel} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
          <Download size={16} /> ดาวน์โหลด BOQ (.xlsx)
        </button>
      </div>

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '2rem' }}>
        <MetricCard label="ค่าวัสดุรวม" value={`฿${boq.material_total.toLocaleString(undefined, {maximumFractionDigits:0})}`} icon="🔩" color="#00c8ff" />
        <MetricCard label="ค่าแรง + วิศวกรรม" value={`฿${(boq.labor_cost + boq.engineering_cost).toLocaleString(undefined, {maximumFractionDigits:0})}`} icon="👷" color="#7dd4fc" />
        <MetricCard label="OVERHEAD / กำไร" value={`฿${boq.overhead.toLocaleString(undefined, {maximumFractionDigits:0})}`} icon="📈" color="#a78bfa" />
        <MetricCard label="รวมทั้งสิ้น" value={`฿${boq.grand_total.toLocaleString(undefined, {maximumFractionDigits:0})}`} icon="💰" color="#00ffcc" />
      </div>

      <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem' }}>
        รายการวัสดุและอุปกรณ์
      </h3>

      <div style={{ background: 'var(--surface-color)', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-color)', marginBottom: '2rem' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead style={{ background: 'var(--border-color)', color: 'var(--text-muted)' }}>
              <tr>
                <th style={{ padding: '0.75rem', textAlign: 'center', borderBottom: '1px solid var(--border-color)' }}>ลำดับ</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>รายการ</th>
                <th style={{ padding: '0.75rem', textAlign: 'center', borderBottom: '1px solid var(--border-color)' }}>หน่วย</th>
                <th style={{ padding: '0.75rem', textAlign: 'center', borderBottom: '1px solid var(--border-color)' }}>จำนวน</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>ราคาต่อหน่วย (บาท)</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', borderBottom: '1px solid var(--border-color)' }}>รวม (บาท)</th>
                <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>หมวด</th>
              </tr>
            </thead>
            <tbody>
              {boq.line_items.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>{item["ลำดับ"]}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'left' }}>{item["รายการ"]}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>{item["หน่วย"]}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>{item["จำนวน"]}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)' }}>{item["ราคาต่อหน่วย"].toLocaleString()}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 'bold' }}>{item["รวม"].toLocaleString()}</td>
                  <td style={{ padding: '0.75rem', textAlign: 'left', color: 'var(--text-muted)' }}>{item["หมวด"]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <h3 style={{ fontSize: '0.9rem', color: '#0ea5e9', marginBottom: '1rem' }}>
        สรุปงบประมาณ
      </h3>

      <div style={{ background: 'var(--surface-color)', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead style={{ background: 'var(--border-color)', color: 'var(--text-muted)' }}>
            <tr>
              <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>หมวด</th>
              <th style={{ padding: '0.75rem', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>จำนวน (บาท)</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '0.75rem' }}>วัสดุและอุปกรณ์ (Material)</td>
              <td style={{ padding: '0.75rem' }}>฿ {boq.material_total.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '0.75rem' }}>ค่าแรงติดตั้ง (18%)</td>
              <td style={{ padding: '0.75rem' }}>฿ {boq.labor_cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '0.75rem' }}>ค่าวิศวกรรม + Commissioning (8%)</td>
              <td style={{ padding: '0.75rem' }}>฿ {boq.engineering_cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '0.75rem' }}>Overhead / กำไร ({(inputs.overheadPct*100).toFixed(0)}%)</td>
              <td style={{ padding: '0.75rem' }}>฿ {boq.overhead.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            </tr>
            <tr>
              <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#f59e0b', fontSize: '1rem' }}>💰 ราคาเสนอรวม (Grand Total)</td>
              <td style={{ padding: '0.75rem', fontWeight: 'bold', color: '#f59e0b', fontSize: '1rem' }}>฿ {boq.grand_total.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  );
}
