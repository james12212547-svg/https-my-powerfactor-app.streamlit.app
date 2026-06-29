import math


def calculate_roi(p_kw: float, pf1: float, pf2: float, qc_kvar: float, penalty_rate: float, cost_per_kvar: float) -> dict:
    """
    Estimates the return on investment (ROI) and payback period.
    """
    total_investment = qc_kvar * cost_per_kvar
    
    q_limit = 0.6197 * p_kw
    q_current = p_kw * math.tan(math.acos(pf1))
    q_future  = p_kw * math.tan(math.acos(pf2))
    
    current_penalty_kvar = max(0, q_current - q_limit)
    future_penalty_kvar  = max(0, q_future  - q_limit)
    
    monthly_penalty_saved = (current_penalty_kvar - future_penalty_kvar) * penalty_rate
    yearly_penalty_saved  = monthly_penalty_saved * 12
    
    loss_reduction_kw  = p_kw * 0.02 * (1 - (pf1/pf2)**2)
    hours_per_year     = 300 * 12
    energy_saved_kwh   = loss_reduction_kw * hours_per_year
    energy_cost_saving = energy_saved_kwh * 4.5
    
    total_yearly_saving = yearly_penalty_saved + energy_cost_saving
    payback_months = (total_investment / total_yearly_saving) * 12 if total_yearly_saving > 0 else 0
        
    return {
        "investment_thb":        total_investment,
        "yearly_saving_thb":     total_yearly_saving,
        "monthly_penalty_saved": monthly_penalty_saved,
        "energy_saved_kwh_yr":   energy_saved_kwh,
        "payback_months":        payback_months,
    }


# ─────────────────────────────────────────────
# [NEW] BOQ / Bill of Quantities Generator
# ─────────────────────────────────────────────

# Component price database (THB, mid-market 2024-2025)
PRICE_DB = {
    # Capacitors (per unit, dry film, self-healing)
    "cap_unit": {
        2.5:  1_200,  5:    2_000,  7.5:  2_800,  10:   3_500,
        12.5: 4_200,  15:   5_000,  20:   6_200,  25:   7_500,
        30:   8_800,  50:  13_000,  60:  15_000,  75:  18_000,
        100: 23_000,
    },
    # Magnetic contactors AC-6b (per step)
    "contactor": {
        25:  1_800,  40:  2_500,  63:  3_200,  95:  4_800,
        120: 6_000,  150: 7_500,  185: 9_000,  225: 11_000,
        300: 14_000,
    },
    # Power factor controller relay (1 per panel)
    "pf_controller": 18_000,
    # Detuned reactor (per step, 7%)
    "reactor_7pct": {
        10: 3_500,  25: 7_000,  50: 12_000,  75: 16_000,  100: 20_000,
    },
    # Discharge resistor (per step)
    "discharge_resistor": 350,
    # Main circuit breaker (MCCB)
    "mccb": {
        100: 3_500,  160: 5_000,  250: 7_500,
        400: 12_000, 630: 18_000, 800: 25_000,
    },
    # HRC fuse (per set of 3)
    "hrc_fuse": {
        100: 600,  160: 850,  250: 1_200,
        400: 1_800, 630: 2_500,
    },
    # Cable THW (THB per meter, 3-phase run 10m assumed)
    "cable_thw_per_m": {
        "2.5 sq.mm":  15, "4 sq.mm":   22,  "6 sq.mm":   32,
        "10 sq.mm":   48, "16 sq.mm":  72,  "25 sq.mm": 110,
        "35 sq.mm":  148, "50 sq.mm": 200,  "70 sq.mm": 275,
        "95 sq.mm":  360, "120 sq.mm":430,  "150 sq.mm":510,
        "185 sq.mm": 610, "240 sq.mm":790,  "300 sq.mm":960,
    },
    # CT (current transformer)
    "ct": {
        100: 800,  200: 1_000,  300: 1_200,  400: 1_500,
        500: 1_800, 800: 2_500, 1000: 3_000, 1500: 4_500, 2000: 6_000,
    },
    # Panel enclosure (IP31, steel, per panel)
    "panel_enclosure": 12_000,
    # Busbar & wiring lump
    "wiring_lump_per_kvar": 120,
    # Installation labor (% of material cost)
    "labor_pct": 0.18,
    # Engineering & commissioning
    "engineering_pct": 0.08,
}


def _nearest_price(price_dict: dict, value: float) -> float:
    """Return price from dict for nearest key >= value."""
    keys = sorted(price_dict.keys())
    for k in keys:
        if k >= value:
            return price_dict[k]
    return price_dict[keys[-1]]


def generate_boq(
    qc_kvar: float,
    step_config: dict,           # result from calculate_cap_steps()
    i_c_A: float,
    i_load_A: float,
    cable_size: str,
    cb_at: int,
    fuse_amp: float,
    ct_primary: int,
    use_detuned_reactor: bool = False,
    overhead_pct: float = 0.10,   # profit margin
) -> dict:
    """
    Generates a detailed Bill of Quantities (BOQ) for a capacitor bank panel.
    
    Returns line items list and total costs.
    """
    line_items = []

    # ── 1. Capacitor units ─────────────────────────────────────────
    steps = step_config.get("steps_kvar", [qc_kvar / 5] * 5)
    cap_total = 0
    for i, step_kvar in enumerate(steps):
        nearest_size = min(PRICE_DB["cap_unit"].keys(), key=lambda x: abs(x - step_kvar))
        unit_price = PRICE_DB["cap_unit"][nearest_size]
        qty = 1
        subtotal = unit_price * qty
        cap_total += subtotal
        line_items.append({
            "ลำดับ": len(line_items) + 1,
            "รายการ": f"Capacitor {nearest_size} kVAR (สเต็ป {i+1})",
            "หน่วย": "ชุด",
            "จำนวน": qty,
            "ราคาต่อหน่วย (บาท)": f"{unit_price:,.0f}",
            "รวม (บาท)": f"{subtotal:,.0f}",
            "หมวด": "คาปาซิเตอร์",
        })

    # ── 2. Magnetic contactors (1 per step) ────────────────────────
    contactor_amp = i_c_A / max(len(steps), 1)
    contactor_price = _nearest_price(PRICE_DB["contactor"], contactor_amp * 1.25)
    for i in range(len(steps)):
        qty = 1
        subtotal = contactor_price * qty
        line_items.append({
            "ลำดับ": len(line_items) + 1,
            "รายการ": f"Magnetic Contactor AC-6b (สเต็ป {i+1})",
            "หน่วย": "ตัว",
            "จำนวน": qty,
            "ราคาต่อหน่วย (บาท)": f"{contactor_price:,.0f}",
            "รวม (บาท)": f"{subtotal:,.0f}",
            "หมวด": "สวิตช์เกียร์",
        })

    # ── 3. Detuned Reactors (optional) ─────────────────────────────
    if use_detuned_reactor:
        for i, step_kvar in enumerate(steps):
            nearest_size = min(PRICE_DB["reactor_7pct"].keys(), key=lambda x: abs(x - step_kvar))
            reactor_price = PRICE_DB["reactor_7pct"][nearest_size]
            subtotal = reactor_price
            line_items.append({
                "ลำดับ": len(line_items) + 1,
                "รายการ": f"Detuned Reactor 7% {nearest_size} kVAR (สเต็ป {i+1})",
                "หน่วย": "ตัว",
                "จำนวน": 1,
                "ราคาต่อหน่วย (บาท)": f"{reactor_price:,.0f}",
                "รวม (บาท)": f"{subtotal:,.0f}",
                "หมวด": "Reactor/Filter",
            })

    # ── 4. Discharge Resistors ─────────────────────────────────────
    dr_price = PRICE_DB["discharge_resistor"]
    dr_qty   = len(steps)
    dr_total = dr_price * dr_qty
    line_items.append({
        "ลำดับ": len(line_items) + 1,
        "รายการ": "Discharge Resistor (วงจรคายประจุ)",
        "หน่วย": "ชุด",
        "จำนวน": dr_qty,
        "ราคาต่อหน่วย (บาท)": f"{dr_price:,.0f}",
        "รวม (บาท)": f"{dr_total:,.0f}",
        "หมวด": "สวิตช์เกียร์",
    })

    # ── 5. Power Factor Controller Relay ──────────────────────────
    pf_price = PRICE_DB["pf_controller"]
    line_items.append({
        "ลำดับ": len(line_items) + 1,
        "รายการ": f"Power Factor Controller Relay ({len(steps)} สเต็ป)",
        "หน่วย": "ตัว",
        "จำนวน": 1,
        "ราคาต่อหน่วย (บาท)": f"{pf_price:,.0f}",
        "รวม (บาท)": f"{pf_price:,.0f}",
        "หมวด": "อุปกรณ์ควบคุม",
    })

    # ── 6. Main Breaker (MCCB) ─────────────────────────────────────
    mccb_price = _nearest_price(PRICE_DB["mccb"], cb_at)
    line_items.append({
        "ลำดับ": len(line_items) + 1,
        "รายการ": f"MCCB Main {cb_at} AT (3P)",
        "หน่วย": "ตัว",
        "จำนวน": 1,
        "ราคาต่อหน่วย (บาท)": f"{mccb_price:,.0f}",
        "รวม (บาท)": f"{mccb_price:,.0f}",
        "หมวด": "สวิตช์เกียร์",
    })

    # ── 7. HRC Fuses ───────────────────────────────────────────────
    fuse_price = _nearest_price(PRICE_DB["hrc_fuse"], fuse_amp)
    fuse_total = fuse_price * len(steps)
    line_items.append({
        "ลำดับ": len(line_items) + 1,
        "รายการ": f"HRC Fuse {round(fuse_amp)} A (ชุด 3 เฟส x {len(steps)} สเต็ป)",
        "หน่วย": "ชุด",
        "จำนวน": len(steps),
        "ราคาต่อหน่วย (บาท)": f"{fuse_price:,.0f}",
        "รวม (บาท)": f"{fuse_total:,.0f}",
        "หมวด": "สวิตช์เกียร์",
    })

    # ── 8. Current Transformer ─────────────────────────────────────
    ct_price = _nearest_price(PRICE_DB["ct"], ct_primary)
    line_items.append({
        "ลำดับ": len(line_items) + 1,
        "รายการ": f"Current Transformer {ct_primary}/5A",
        "หน่วย": "ตัว",
        "จำนวน": 1,
        "ราคาต่อหน่วย (บาท)": f"{ct_price:,.0f}",
        "รวม (บาท)": f"{ct_price:,.0f}",
        "หมวด": "อุปกรณ์ควบคุม",
    })

    # ── 9. Main Cable ──────────────────────────────────────────────
    cable_size_key = cable_size.replace(" ", " ")
    cable_price_m  = PRICE_DB["cable_thw_per_m"].get(cable_size_key, 200)
    cable_run_m    = 10   # assume 10m run
    cable_total    = cable_price_m * cable_run_m * 3  # 3 phases
    line_items.append({
        "ลำดับ": len(line_items) + 1,
        "รายการ": f"สายไฟ THW {cable_size} x 10 เมตร (3 เส้น)",
        "หน่วย": "ชุด",
        "จำนวน": 1,
        "ราคาต่อหน่วย (บาท)": f"{cable_total:,.0f}",
        "รวม (บาท)": f"{cable_total:,.0f}",
        "หมวด": "สายไฟ",
    })

    # ── 10. Panel Enclosure & Wiring ──────────────────────────────
    enclosure_price = PRICE_DB["panel_enclosure"]
    wiring_lump     = qc_kvar * PRICE_DB["wiring_lump_per_kvar"]
    line_items.append({
        "ลำดับ": len(line_items) + 1,
        "รายการ": "ตู้ Panel + Busbar + Wiring",
        "หน่วย": "ชุด",
        "จำนวน": 1,
        "ราคาต่อหน่วย (บาท)": f"{enclosure_price + wiring_lump:,.0f}",
        "รวม (บาท)": f"{enclosure_price + wiring_lump:,.0f}",
        "หมวด": "โครงสร้าง",
    })

    # ── Totals ─────────────────────────────────────────────────────
    material_total = sum(
        float(item["รวม (บาท)"].replace(",", ""))
        for item in line_items
    )
    labor_cost       = material_total * PRICE_DB["labor_pct"]
    engineering_cost = material_total * PRICE_DB["engineering_pct"]
    subtotal_before  = material_total + labor_cost + engineering_cost
    overhead         = subtotal_before * overhead_pct
    grand_total      = subtotal_before + overhead

    return {
        "line_items":        line_items,
        "material_total":    material_total,
        "labor_cost":        labor_cost,
        "engineering_cost":  engineering_cost,
        "overhead":          overhead,
        "grand_total":       grand_total,
        "overhead_pct":      overhead_pct,
        "num_steps":         len(steps),
        "use_reactor":       use_detuned_reactor,
    }
