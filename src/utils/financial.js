export function calculate_roi(p_kw, pf1, pf2, qc_kvar, penalty_rate = 56.07, cost_per_kvar = 1500, energy_rate = 4.5, demand_charge = 0.0, p_base = 0.0, pf_base = 1.0, hrs_peak = 24.0, hrs_base = 0.0) {
  const total_investment = qc_kvar * cost_per_kvar;
  
  const q_limit = 0.6197 * p_kw; // PEA/MEA limit is approx 61.97% (when PF = 0.85)
  const q_current = p_kw * Math.tan(Math.acos(pf1));
  const q_future  = p_kw * Math.tan(Math.acos(pf2));
  
  const current_penalty_kvar = Math.max(0, q_current - q_limit);
  const future_penalty_kvar  = Math.max(0, q_future  - q_limit);
  
  const monthly_penalty_saved = (current_penalty_kvar - future_penalty_kvar) * penalty_rate;
  const yearly_penalty_saved  = monthly_penalty_saved * 12;
  
  // KVA Demand Saving
  const s_current = p_kw / pf1;
  const s_future = p_kw / pf2;
  const monthly_kva_saved = Math.max(0, s_current - s_future) * demand_charge;
  const yearly_kva_saved = monthly_kva_saved * 12;
  
  // Loss reduction formula
  const loss_reduction_peak = p_kw * 0.02 * Math.max(0, (1 - Math.pow(pf1/pf2, 2)));
  const loss_reduction_base = p_base > 0 ? p_base * 0.02 * Math.max(0, (1 - Math.pow(pf_base/pf2, 2))) : 0;
  
  // 300 working days per year assumption
  const energy_saved_kwh = (loss_reduction_peak * hrs_peak * 300) + (loss_reduction_base * hrs_base * 300);
  const energy_cost_saving = energy_saved_kwh * energy_rate;
  
  const total_yearly_saving = yearly_penalty_saved + energy_cost_saving + yearly_kva_saved;
  const payback_months = total_yearly_saving > 0 ? (total_investment / total_yearly_saving) * 12 : 0;
      
  return {
      investment_thb:        total_investment,
      yearly_saving_thb:     total_yearly_saving,
      monthly_penalty_saved: monthly_penalty_saved,
      monthly_kva_saved:     monthly_kva_saved,
      energy_saved_kwh_yr:   energy_saved_kwh,
      payback_months:        payback_months,
  };
}

const PRICE_DB = {
  cap_unit: { 2.5: 1200, 5: 2000, 7.5: 2800, 10: 3500, 12.5: 4200, 15: 5000, 20: 6200, 25: 7500, 30: 8800, 50: 13000, 60: 15000, 75: 18000, 100: 23000 },
  contactor: { 25: 1800, 40: 2500, 63: 3200, 95: 4800, 120: 6000, 150: 7500, 185: 9000, 225: 11000, 300: 14000 },
  pf_controller: 18000,
  reactor_7pct: { 10: 3500, 25: 7000, 50: 12000, 75: 16000, 100: 20000 },
  discharge_resistor: 350,
  mccb: { 100: 3500, 160: 5000, 250: 7500, 400: 12000, 630: 18000, 800: 25000 },
  hrc_fuse: { 100: 600, 160: 850, 250: 1200, 400: 1800, 630: 2500 },
  cable_thw_per_m: {
      "2.5 sq.mm": 15, "4 sq.mm": 22, "6 sq.mm": 32, "10 sq.mm": 48, "16 sq.mm": 72, "25 sq.mm": 110,
      "35 sq.mm": 148, "50 sq.mm": 200, "70 sq.mm": 275, "95 sq.mm": 360, "120 sq.mm": 430, "150 sq.mm": 510,
      "185 sq.mm": 610, "240 sq.mm": 790, "300 sq.mm": 960,
  },
  ct: { 100: 800, 200: 1000, 300: 1200, 400: 1500, 500: 1800, 800: 2500, 1000: 3000, 1500: 4500, 2000: 6000 },
  panel_enclosure: 12000,
  wiring_lump_per_kvar: 120,
  labor_pct: 0.18,
  engineering_pct: 0.08,
};

function nearest_price(price_dict, value) {
  const keys = Object.keys(price_dict).map(Number).sort((a,b) => a-b);
  for(let k of keys) {
      if(k >= value) return price_dict[k];
  }
  return price_dict[keys[keys.length-1]];
}

export function generate_boq(qc_kvar, step_config, i_c_A, i_load_A, cable_size, cb_at, fuse_amp, ct_primary, use_detuned_reactor = false, overhead_pct = 0.10) {
  const line_items = [];
  const steps = step_config && step_config.steps_kvar ? step_config.steps_kvar : Array(5).fill(qc_kvar / 5);
  
  let cap_total = 0;
  steps.forEach((step_kvar, i) => {
      const sizes = Object.keys(PRICE_DB.cap_unit).map(Number);
      const nearest_size = sizes.reduce((prev, curr) => Math.abs(curr - step_kvar) < Math.abs(prev - step_kvar) ? curr : prev);
      const unit_price = PRICE_DB.cap_unit[nearest_size];
      cap_total += unit_price;
      line_items.push({
          "ลำดับ": line_items.length + 1,
          "รายการ": `Capacitor ${nearest_size} kVAR (สเต็ป ${i+1})`,
          "หน่วย": "ชุด",
          "จำนวน": 1,
          "ราคาต่อหน่วย": unit_price,
          "รวม": unit_price,
          "หมวด": "คาปาซิเตอร์",
      });
  });

  const contactor_amp = i_c_A / Math.max(steps.length, 1);
  const contactor_price = nearest_price(PRICE_DB.contactor, contactor_amp * 1.25);
  steps.forEach((_, i) => {
      line_items.push({
          "ลำดับ": line_items.length + 1,
          "รายการ": `Magnetic Contactor AC-6b (สเต็ป ${i+1})`,
          "หน่วย": "ตัว",
          "จำนวน": 1,
          "ราคาต่อหน่วย": contactor_price,
          "รวม": contactor_price,
          "หมวด": "สวิตช์เกียร์",
      });
  });

  if (use_detuned_reactor) {
      steps.forEach((step_kvar, i) => {
          const sizes = Object.keys(PRICE_DB.reactor_7pct).map(Number);
          const nearest_size = sizes.reduce((prev, curr) => Math.abs(curr - step_kvar) < Math.abs(prev - step_kvar) ? curr : prev);
          const reactor_price = PRICE_DB.reactor_7pct[nearest_size];
          line_items.push({
              "ลำดับ": line_items.length + 1,
              "รายการ": `Detuned Reactor 7% ${nearest_size} kVAR (สเต็ป ${i+1})`,
              "หน่วย": "ตัว",
              "จำนวน": 1,
              "ราคาต่อหน่วย": reactor_price,
              "รวม": reactor_price,
              "หมวด": "Reactor/Filter",
          });
      });
  }

  const dr_price = PRICE_DB.discharge_resistor;
  line_items.push({
      "ลำดับ": line_items.length + 1,
      "รายการ": "Discharge Resistor (วงจรคายประจุ)",
      "หน่วย": "ชุด",
      "จำนวน": steps.length,
      "ราคาต่อหน่วย": dr_price,
      "รวม": dr_price * steps.length,
      "หมวด": "สวิตช์เกียร์",
  });

  const pf_price = PRICE_DB.pf_controller;
  line_items.push({
      "ลำดับ": line_items.length + 1,
      "รายการ": `Power Factor Controller Relay (${steps.length} สเต็ป)`,
      "หน่วย": "ตัว",
      "จำนวน": 1,
      "ราคาต่อหน่วย": pf_price,
      "รวม": pf_price,
      "หมวด": "อุปกรณ์ควบคุม",
  });

  const mccb_price = nearest_price(PRICE_DB.mccb, cb_at);
  line_items.push({
      "ลำดับ": line_items.length + 1,
      "รายการ": `MCCB Main ${cb_at} AT (3P)`,
      "หน่วย": "ตัว",
      "จำนวน": 1,
      "ราคาต่อหน่วย": mccb_price,
      "รวม": mccb_price,
      "หมวด": "สวิตช์เกียร์",
  });

  const fuse_price = nearest_price(PRICE_DB.hrc_fuse, fuse_amp);
  line_items.push({
      "ลำดับ": line_items.length + 1,
      "รายการ": `HRC Fuse ${Math.round(fuse_amp)} A (ชุด 3 เฟส x ${steps.length} สเต็ป)`,
      "หน่วย": "ชุด",
      "จำนวน": steps.length,
      "ราคาต่อหน่วย": fuse_price,
      "รวม": fuse_price * steps.length,
      "หมวด": "สวิตช์เกียร์",
  });

  // Basic fallback if ct_primary is not passed properly or parses weird
  const ct_val = ct_primary ? parseInt(ct_primary.toString().split('/')[0]) : 400;
  const ct_price = nearest_price(PRICE_DB.ct, ct_val || 400);
  line_items.push({
      "ลำดับ": line_items.length + 1,
      "รายการ": `Current Transformer ${ct_val}/5A`,
      "หน่วย": "ตัว",
      "จำนวน": 1,
      "ราคาต่อหน่วย": ct_price,
      "รวม": ct_price,
      "หมวด": "อุปกรณ์ควบคุม",
  });

  const cable_size_key = cable_size.replace(" ", " ");
  const cable_price_m = PRICE_DB.cable_thw_per_m[cable_size_key] || 200;
  const cable_total = cable_price_m * 10 * 3;
  line_items.push({
      "ลำดับ": line_items.length + 1,
      "รายการ": `สายไฟ THW ${cable_size} x 10 เมตร (3 เส้น)`,
      "หน่วย": "ชุด",
      "จำนวน": 1,
      "ราคาต่อหน่วย": cable_total,
      "รวม": cable_total,
      "หมวด": "สายไฟ",
  });

  const enclosure_price = PRICE_DB.panel_enclosure;
  const wiring_lump = qc_kvar * PRICE_DB.wiring_lump_per_kvar;
  line_items.push({
      "ลำดับ": line_items.length + 1,
      "รายการ": "ตู้ Panel + Busbar + Wiring",
      "หน่วย": "ชุด",
      "จำนวน": 1,
      "ราคาต่อหน่วย": enclosure_price + wiring_lump,
      "รวม": enclosure_price + wiring_lump,
      "หมวด": "โครงสร้าง",
  });

  const material_total = line_items.reduce((sum, item) => sum + item["รวม"], 0);
  const labor_cost = material_total * PRICE_DB.labor_pct;
  const engineering_cost = material_total * PRICE_DB.engineering_pct;
  const subtotal_before = material_total + labor_cost + engineering_cost;
  const overhead = subtotal_before * overhead_pct;
  const grand_total = subtotal_before + overhead;

  return {
      line_items,
      material_total,
      labor_cost,
      engineering_cost,
      overhead,
      grand_total,
      overhead_pct,
      num_steps: steps.length,
      use_reactor: use_detuned_reactor,
  };
}
