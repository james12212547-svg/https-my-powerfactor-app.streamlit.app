// ─────────────────────────────────────────────
// 1. Power Factor & Capacitor Core Calculation
// ─────────────────────────────────────────────
export function calculate_q_and_c(p, v, f, pf1, pf2, phase) {
  const theta1 = Math.acos(pf1);
  const theta2 = Math.acos(pf2);
  
  let Qc_total = p * (Math.tan(theta1) - Math.tan(theta2));
  if (Qc_total < 0) {
      Qc_total = 0.0;
  }
      
  const Q1 = p * Math.tan(theta1);
  const Q2 = p * Math.tan(theta2);
  const S1 = p / pf1;
  const S2 = p / pf2;
  
  let c_farad, i_c, i_load;
  
  if (phase === 3) {
      c_farad = (Qc_total * 1000) / (3 * 2 * Math.PI * f * Math.pow(v, 2));
      i_c = (Qc_total * 1000) / (Math.sqrt(3) * v);
      i_load = (p * 1000) / (Math.sqrt(3) * v * pf1);
  } else {
      c_farad = (Qc_total * 1000) / (2 * Math.PI * f * Math.pow(v, 2));
      i_c = (Qc_total * 1000) / v;
      i_load = (p * 1000) / (v * pf1);
  }
      
  const c_microfarad = c_farad * 1000000;
  const cb_rating = i_c * 1.35;
  
  const standard_cb = [16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000];
  let recommended_cb = standard_cb[standard_cb.length - 1];
  for (let x of standard_cb) {
      if (x >= cb_rating) {
          recommended_cb = x;
          break;
      }
  }
  
  return {
      Qc_total_kVAR: Qc_total,
      C_microfarad: c_microfarad,
      I_c_A: i_c,
      I_load_A: i_load,
      recommended_cb_AT: recommended_cb,
      cb_calc_A: cb_rating,
      Q1, Q2, S1, S2
  };
}

// ─────────────────────────────────────────────
// 2. Harmonic Resonance Check (Transformer-based)
// ─────────────────────────────────────────────
export function check_harmonic_resonance(qc_kvar, trafo_kva, z_percent, v = 400.0) {
  if (z_percent <= 0 || trafo_kva <= 0 || qc_kvar <= 0) {
      return { h_r: 0, risk: "N/A", message: "Invalid parameters", tuning_factor: "-", u_c_voltage: v, detuned_p: 0.0 };
  }
      
  const s_sc = trafo_kva / (z_percent / 100);
  const h_r = Math.sqrt(s_sc / qc_kvar);
  
  let risk = "Low";
  let message = "ปลอดภัยจาก Harmonic Resonance ทั่วไป";
  let tuning_factor = "ไม่จำเป็น (0%)";
  let detuned_p = 0.0;
  
  if (h_r >= 4.0 && h_r <= 6.0) {
      risk = "High";
      message = `อันตราย: เสี่ยงเรโซแนนซ์กับฮาร์มอนิกลำดับที่ 5 (h_r = ${h_r.toFixed(2)})`;
      tuning_factor = "7% (สำหรับโหลดฮาร์มอนิก 5)";
      detuned_p = 0.07;
  } else if (h_r >= 6.1 && h_r <= 8.0) {
      risk = "High";
      message = `อันตราย: เสี่ยงเรโซแนนซ์กับฮาร์มอนิกลำดับที่ 7 (h_r = ${h_r.toFixed(2)})`;
      tuning_factor = "6% หรือ 7%";
      detuned_p = 0.07;
  } else if (h_r < 4.0) {
      risk = "High";
      message = `อันตราย: ค่า h_r ต่ำมาก (${h_r.toFixed(2)}) เสี่ยงต่อฮาร์มอนิกลำดับที่ 3`;
      tuning_factor = "14% (สำหรับโหลด 1 เฟส/ฮาร์มอนิก 3)";
      detuned_p = 0.14;
  }
      
  const u_c_voltage = detuned_p > 0 ? v / (1 - detuned_p) : v;
          
  return {
      h_r, 
      risk, 
      message, 
      tuning_factor,
      u_c_voltage,
      detuned_p
  };
}

// ─────────────────────────────────────────────
// 3. Detail Engineering (Cable, Breaker, CT, Ventilation)
// ─────────────────────────────────────────────
export function calculate_detail_engineering(i_c_A, i_load_A, qc_kvar, trafo_kva, z_percent) {
  const cable_amp_req = i_c_A * 1.35;
  const cb_amp_req = i_c_A * 1.43;
  const fuse_amp_req = i_c_A * 1.65;
  
  const cable_table = [
      [2.5, 21], [4, 28], [6, 36], [10, 50], [16, 68], [25, 89], 
      [35, 110], [50, 134], [70, 171], [95, 207], [120, 239], 
      [150, 272], [185, 310], [240, 364], [300, 419], [400, 502]
  ];
  
  let recommended_cable = "400 sq.mm (x2 หรือบัสบาร์)";
  for (let [size, amp] of cable_table) {
      if (amp >= cable_amp_req) {
          recommended_cable = `${size} sq.mm`;
          break;
      }
  }
          
  const ct_primaries = [50, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1250, 1500, 2000, 2500, 3200, 4000];
  let ct_primary = ct_primaries[ct_primaries.length - 1];
  for(let x of ct_primaries) {
      if (x >= i_load_A * 1.2) {
          ct_primary = x;
          break;
      }
  }
  const ct_ratio = `${ct_primary}/5A`;
  
  const watt_loss = qc_kvar * 5.0;
  const cfm_required = watt_loss / 3.0;
  
  const trafo_fla = (trafo_kva * 1000) / (Math.sqrt(3) * 400);
  const i_sc_A = trafo_fla / (z_percent / 100);
  const i_sc_kA = i_sc_A / 1000.0;
  
  const standard_ka = [10, 16, 25, 36, 50, 65, 85, 100];
  let recommended_ka = standard_ka[standard_ka.length - 1];
  for(let x of standard_ka) {
      if (x >= i_sc_kA) {
          recommended_ka = x;
          break;
      }
  }
  
  const step_kvar = qc_kvar / 5.0;
  
  return {
      cable_size: recommended_cable,
      cable_amp_req,
      cb_amp_req,
      fuse_amp_req,
      ct_ratio,
      watt_loss,
      cfm_required,
      short_circuit_kA_req: i_sc_kA,
      breaker_kA: recommended_ka,
      step_kvar,
      contactor_type: "AC-6b (ทน Inrush >= 100 เท่า พร้อม Damping Resistors)",
      discharge_resistor: "ลดแรงดันเหลือ <= 75V ภายใน 3 นาที"
  };
}

// ─────────────────────────────────────────────
// 4. [NEW] Smart Capacitor Step Configuration
// ─────────────────────────────────────────────
const MARKET_KVAR_SIZES = [2.5, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 50, 60, 75, 100];

function generate_combinations(steps) {
  // Simple combination generator logic equivalent for JS
  const combos = new Set();
  combos.add(0);
  
  const getSubsets = (array) => array.reduce(
    (subsets, value) => subsets.concat(
      subsets.map(set => [value,...set])
    ),
    [[]]
  );
  
  const subsets = getSubsets(steps);
  for(let subset of subsets) {
    let sum = subset.reduce((a,b) => a+b, 0);
    combos.add(Math.round(sum * 10)/10);
  }
  return Array.from(combos).sort((a,b) => a-b);
}

export function calculate_cap_steps(qc_total, num_steps = 5) {
  const patterns = {
      "เท่ากันทุกสเต็ป": Array(num_steps).fill(1),
      "1:2:2 (3 สเต็ป)": [1, 2, 2],
      "1:2:4 (3 สเต็ป)": [1, 2, 4],
      "1:1:2:2 (4 สเต็ป)": [1, 1, 2, 2],
      "1:1:2:4 (4 สเต็ป)": [1, 1, 2, 4],
      "1:2:2:4 (4 สเต็ป)": [1, 2, 2, 4],
      "1:1:2:2:4 (5 สเต็ป)": [1, 1, 2, 2, 4],
      "1:2:4:4:4 (5 สเต็ป)": [1, 2, 4, 4, 4],
      "1:1:1:2:2 (5 สเต็ป)": [1, 1, 1, 2, 2],
  };

  let best_result = null;
  let best_error = Infinity;
  let all_patterns = [];

  for (const [pattern_name, ratios] of Object.entries(patterns)) {
      const ratio_sum = ratios.reduce((a, b) => a + b, 0);
      const base_kvar = qc_total / ratio_sum;
      
      const nearest_base = MARKET_KVAR_SIZES.reduce((prev, curr) => 
        Math.abs(curr - base_kvar) < Math.abs(prev - base_kvar) ? curr : prev
      );
      
      const steps = ratios.map(r => nearest_base * r);
      const total_achieved = steps.reduce((a, b) => a + b, 0);
      const error = Math.abs(total_achieved - qc_total);
      const coverage_pct = qc_total > 0 ? (total_achieved / qc_total) * 100 : 0;
      
      if (error < best_error) {
          best_error = error;
          best_result = {
              pattern_name,
              ratios,
              base_kvar: nearest_base,
              steps_kvar: steps,
              total_achieved_kvar: total_achieved,
              target_kvar: qc_total,
              error_kvar: error,
              coverage_pct,
              num_steps: steps.length,
              combinations: generate_combinations(steps),
          };
      }
      
      all_patterns.push({
          "รูปแบบสเต็ป": pattern_name,
          "ขนาดฐาน (kVAR)": nearest_base,
          "จำนวนสเต็ป": steps.length,
          "รวม kVAR ที่ได้": Math.round(total_achieved * 10) / 10,
          "เป้าหมาย (kVAR)": Math.round(qc_total * 10) / 10,
          "ผิดพลาด (kVAR)": Math.round(Math.abs(total_achieved - qc_total) * 10) / 10,
          "Coverage (%)": qc_total > 0 ? Math.round((total_achieved / qc_total) * 1000) / 10 : 0,
      });
  }

  best_result.all_patterns = all_patterns;
  return best_result;
}

// ─────────────────────────────────────────────
// 5. [NEW] IEEE 519 Harmonic Analysis
// ─────────────────────────────────────────────
export function analyze_harmonics_ieee519(thdi_pct, thdv_pct, isc_il_ratio, voltage_level = "LV") {
  let tdd_limit, limit_label;
  if (isc_il_ratio < 20) {
      tdd_limit = 5.0; limit_label = "< 20";
  } else if (isc_il_ratio < 50) {
      tdd_limit = 8.0; limit_label = "20–50";
  } else if (isc_il_ratio < 100) {
      tdd_limit = 12.0; limit_label = "50–100";
  } else if (isc_il_ratio < 1000) {
      tdd_limit = 15.0; limit_label = "100–1000";
  } else {
      tdd_limit = 20.0; limit_label = "> 1000";
  }

  let thdv_limit, indv_v_limit;
  if (voltage_level === "LV") {
      thdv_limit = 8.0; indv_v_limit = 5.0;
  } else if (voltage_level === "MV") {
      thdv_limit = 5.0; indv_v_limit = 3.0;
  } else {
      thdv_limit = 2.5; indv_v_limit = 1.5;
  }

  const current_ok = thdi_pct <= tdd_limit;
  const voltage_ok = thdv_pct <= thdv_limit;

  const recommendations = [];
  let overall_status = "PASS ✅";
  
  if (!current_ok) {
      overall_status = "FAIL ❌";
      const excess_pct = thdi_pct - tdd_limit;
      if (excess_pct > 10) {
          recommendations.push("🔴 THDi สูงมาก: แนะนำ **Active Harmonic Filter (AHF)** เพื่อลด THDi แบบ Real-time");
          recommendations.push("⚠️ พิจารณาแยก Bus Bar สำหรับโหลด Non-linear ออกจากระบบหลัก");
      } else {
          recommendations.push("🟡 THDi เกินเกณฑ์เล็กน้อย: แนะนำ **Passive Harmonic Filter** หรือ **Detuned Reactor 7%**");
      }
  }
          
  if (!voltage_ok) {
      if(current_ok) overall_status = "FAIL ❌";
      recommendations.push("🔴 THDv สูง: สัญญาณว่าระบบไฟฟ้ามีฮาร์มอนิกรุนแรง ควรตรวจสอบแหล่งกำเนิดฮาร์มอนิก");
  }
      
  if (current_ok && voltage_ok) {
      recommendations.push("✅ ระบบอยู่ในเกณฑ์มาตรฐาน IEEE 519 ไม่จำเป็นต้องเพิ่มอุปกรณ์แก้ฮาร์มอนิก");
      if (thdi_pct > tdd_limit * 0.8) {
          recommendations.push("💡 THDi ใกล้เกณฑ์: ควรติดตามและวัดซ้ำหากมีการเพิ่มโหลด Non-linear");
      }
  }

  let filter_recommendation = "ไม่จำเป็น";
  let filter_cost_estimate = "0";
  if (!current_ok || !voltage_ok) {
      if (thdi_pct > tdd_limit + 10 || thdv_pct > thdv_limit + 3) {
          filter_recommendation = "Active Harmonic Filter (AHF)";
          filter_cost_estimate = "800,000 – 2,500,000 บาท";
      } else {
          filter_recommendation = "Passive Detuned Filter / Reactor 7%";
          filter_cost_estimate = "50,000 – 200,000 บาท";
      }
  }

  return {
      thdi_measured: thdi_pct,
      thdv_measured: thdv_pct,
      tdd_limit,
      thdv_limit,
      isc_il_ratio,
      limit_label,
      current_compliant: current_ok,
      voltage_compliant: voltage_ok,
      overall_status,
      recommendations,
      filter_recommendation,
      filter_cost_estimate,
      compliance_table: [
          {"พารามิเตอร์": "THDi (กระแส)", "ค่าที่วัดได้": `${thdi_pct.toFixed(1)}%`, "เกณฑ์ IEEE 519": `≤ ${tdd_limit.toFixed(0)}%`, "สถานะ": current_ok ? "✅ ผ่าน" : "❌ ไม่ผ่าน"},
          {"พารามิเตอร์": "THDv (แรงดัน)", "ค่าที่วัดได้": `${thdv_pct.toFixed(1)}%`, "เกณฑ์ IEEE 519": `≤ ${thdv_limit.toFixed(0)}%`, "สถานะ": voltage_ok ? "✅ ผ่าน" : "❌ ไม่ผ่าน"},
      ]
  };
}
