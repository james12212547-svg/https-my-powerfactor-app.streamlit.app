import math

# ─────────────────────────────────────────────
# 1. Power Factor & Capacitor Core Calculation
# ─────────────────────────────────────────────
def calculate_q_and_c(p: float, v: float, f: float, pf1: float, pf2: float, phase: int) -> dict:
    theta1 = math.acos(pf1)
    theta2 = math.acos(pf2)
    
    Qc_total = p * (math.tan(theta1) - math.tan(theta2))
    if Qc_total < 0:
        Qc_total = 0.0
        
    Q1 = p * math.tan(theta1)
    Q2 = p * math.tan(theta2)
    S1 = p / pf1
    S2 = p / pf2
    
    if phase == 3:
        c_farad = (Qc_total * 1000) / (3 * 2 * math.pi * f * (v**2))
        i_c = (Qc_total * 1000) / (math.sqrt(3) * v)
        i_load = (p * 1000) / (math.sqrt(3) * v * pf1)
    else:
        c_farad = (Qc_total * 1000) / (2 * math.pi * f * (v**2))
        i_c = (Qc_total * 1000) / v
        i_load = (p * 1000) / (v * pf1)
        
    c_microfarad = c_farad * 1_000_000
    cb_rating = i_c * 1.35
    
    standard_cb = [16, 20, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000]
    recommended_cb = next((x for x in standard_cb if x >= cb_rating), standard_cb[-1])
    
    return {
        "Qc_total_kVAR": Qc_total,
        "C_microfarad": c_microfarad,
        "I_c_A": i_c,
        "I_load_A": i_load,
        "recommended_cb_AT": recommended_cb,
        "cb_calc_A": cb_rating,
        "Q1": Q1, "Q2": Q2, "S1": S1, "S2": S2
    }

# ─────────────────────────────────────────────
# 2. Harmonic Resonance Check (Transformer-based)
# ─────────────────────────────────────────────
def check_harmonic_resonance(qc_kvar: float, trafo_kva: float, z_percent: float, v: float = 400.0) -> dict:
    if z_percent <= 0 or trafo_kva <= 0 or qc_kvar <= 0:
        return {"h_r": 0, "risk": "N/A", "message": "Invalid parameters", "tuning_factor": "-", "u_c_voltage": v, "detuned_p": 0.0}
        
    s_sc = trafo_kva / (z_percent / 100)
    h_r = math.sqrt(s_sc / qc_kvar)
    
    risk = "Low"
    message = "ปลอดภัยจาก Harmonic Resonance ทั่วไป"
    tuning_factor = "ไม่จำเป็น (0%)"
    detuned_p = 0.0
    
    if 4.0 <= h_r <= 6.0:
        risk = "High"
        message = f"อันตราย: เสี่ยงเรโซแนนซ์กับฮาร์มอนิกลำดับที่ 5 (h_r = {h_r:.2f})"
        tuning_factor = "7% (สำหรับโหลดฮาร์มอนิก 5)"
        detuned_p = 0.07
    elif 6.1 <= h_r <= 8.0:
        risk = "High"
        message = f"อันตราย: เสี่ยงเรโซแนนซ์กับฮาร์มอนิกลำดับที่ 7 (h_r = {h_r:.2f})"
        tuning_factor = "6% หรือ 7%"
        detuned_p = 0.07
    elif h_r < 4.0:
        risk = "High"
        message = f"อันตราย: ค่า h_r ต่ำมาก ({h_r:.2f}) เสี่ยงต่อฮาร์มอนิกลำดับที่ 3"
        tuning_factor = "14% (สำหรับโหลด 1 เฟส/ฮาร์มอนิก 3)"
        detuned_p = 0.14
        
    u_c_voltage = v / (1 - detuned_p) if detuned_p > 0 else v
            
    return {
        "h_r": h_r, 
        "risk": risk, 
        "message": message, 
        "tuning_factor": tuning_factor,
        "u_c_voltage": u_c_voltage,
        "detuned_p": detuned_p
    }

# ─────────────────────────────────────────────
# 3. Detail Engineering (Cable, Breaker, CT, Ventilation)
# ─────────────────────────────────────────────
def calculate_detail_engineering(i_c_A: float, i_load_A: float, qc_kvar: float, trafo_kva: float, z_percent: float) -> dict:
    """
    Calculates detailed parameters: Cable sizing, Ventilation, CT ratio, and Short Circuit according to EIT 022001-22.
    """
    cable_amp_req = i_c_A * 1.35
    cb_amp_req = i_c_A * 1.43
    fuse_amp_req = i_c_A * 1.65
    
    cable_table = [
        (2.5, 21), (4, 28), (6, 36), (10, 50), (16, 68), (25, 89), 
        (35, 110), (50, 134), (70, 171), (95, 207), (120, 239), 
        (150, 272), (185, 310), (240, 364), (300, 419), (400, 502)
    ]
    
    recommended_cable = "400 sq.mm (x2 หรือบัสบาร์)"
    for size, amp in cable_table:
        if amp >= cable_amp_req:
            recommended_cable = f"{size} sq.mm"
            break
            
    ct_primaries = [50, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1250, 1500, 2000, 2500, 3200, 4000]
    ct_primary = next((x for x in ct_primaries if x >= i_load_A * 1.2), ct_primaries[-1])
    ct_ratio = f"{ct_primary}/5A"
    
    watt_loss = qc_kvar * 5.0
    cfm_required = watt_loss / 3.0
    
    trafo_fla = (trafo_kva * 1000) / (math.sqrt(3) * 400) 
    i_sc_A = trafo_fla / (z_percent / 100)
    i_sc_kA = i_sc_A / 1000.0
    
    standard_ka = [10, 16, 25, 36, 50, 65, 85, 100]
    recommended_ka = next((x for x in standard_ka if x >= i_sc_kA), standard_ka[-1])
    
    step_kvar = qc_kvar / 5.0
    
    return {
        "cable_size": recommended_cable,
        "cable_amp_req": cable_amp_req,
        "cb_amp_req": cb_amp_req,
        "fuse_amp_req": fuse_amp_req,
        "ct_ratio": ct_ratio,
        "watt_loss": watt_loss,
        "cfm_required": cfm_required,
        "short_circuit_kA_req": i_sc_kA,
        "breaker_kA": recommended_ka,
        "step_kvar": step_kvar,
        "contactor_type": "AC-6b (ทน Inrush >= 100 เท่า พร้อม Damping Resistors)",
        "discharge_resistor": "ลดแรงดันเหลือ <= 75V ภายใน 3 นาที"
    }

# ─────────────────────────────────────────────
# 4. [NEW] Smart Capacitor Step Configuration
# ─────────────────────────────────────────────
# Standard market kVAR sizes available in Thailand
MARKET_KVAR_SIZES = [2.5, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 50, 60, 75, 100]

def calculate_cap_steps(qc_total: float, num_steps: int = 5) -> dict:
    """
    Generates an optimal capacitor step configuration using standard market kVAR sizes.
    Tries patterns: Equal, 1:2:2, 1:2:4, 1:1:2:2:4 for best fit.
    """
    # Step patterns (ratios relative to smallest step)
    patterns = {
        "เท่ากันทุกสเต็ป": [1] * num_steps,
        "1:2:2 (3 สเต็ป)": [1, 2, 2],
        "1:2:4 (3 สเต็ป)": [1, 2, 4],
        "1:1:2:2 (4 สเต็ป)": [1, 1, 2, 2],
        "1:1:2:4 (4 สเต็ป)": [1, 1, 2, 4],
        "1:2:2:4 (4 สเต็ป)": [1, 2, 2, 4],
        "1:1:2:2:4 (5 สเต็ป)": [1, 1, 2, 2, 4],
        "1:2:4:4:4 (5 สเต็ป)": [1, 2, 4, 4, 4],
        "1:1:1:2:2 (5 สเต็ป)": [1, 1, 1, 2, 2],
    }

    best_result = None
    best_error = float("inf")

    for pattern_name, ratios in patterns.items():
        ratio_sum = sum(ratios)
        base_kvar = qc_total / ratio_sum
        
        # Find nearest market size for base step
        nearest_base = min(MARKET_KVAR_SIZES, key=lambda x: abs(x - base_kvar))
        
        steps = [nearest_base * r for r in ratios]
        total_achieved = sum(steps)
        error = abs(total_achieved - qc_total)
        coverage_pct = (total_achieved / qc_total) * 100 if qc_total > 0 else 0
        
        if error < best_error:
            best_error = error
            best_result = {
                "pattern_name": pattern_name,
                "ratios": ratios,
                "base_kvar": nearest_base,
                "steps_kvar": steps,
                "total_achieved_kvar": total_achieved,
                "target_kvar": qc_total,
                "error_kvar": error,
                "coverage_pct": coverage_pct,
                "num_steps": len(steps),
                "combinations": _generate_combinations(steps),
            }

    # Also generate comparison table for all patterns
    all_patterns = []
    for pattern_name, ratios in patterns.items():
        ratio_sum = sum(ratios)
        base_kvar = qc_total / ratio_sum
        nearest_base = min(MARKET_KVAR_SIZES, key=lambda x: abs(x - base_kvar))
        steps = [nearest_base * r for r in ratios]
        total_achieved = sum(steps)
        all_patterns.append({
            "รูปแบบสเต็ป": pattern_name,
            "ขนาดฐาน (kVAR)": nearest_base,
            "จำนวนสเต็ป": len(steps),
            "รวม kVAR ที่ได้": round(total_achieved, 1),
            "เป้าหมาย (kVAR)": round(qc_total, 1),
            "ผิดพลาด (kVAR)": round(abs(total_achieved - qc_total), 1),
            "Coverage (%)": round((total_achieved / qc_total) * 100 if qc_total > 0 else 0, 1),
        })

    best_result["all_patterns"] = all_patterns
    return best_result


def _generate_combinations(steps: list) -> list:
    """Generate all possible kVAR combinations from step switching."""
    from itertools import combinations
    combos = set()
    combos.add(0)
    for r in range(1, len(steps) + 1):
        for combo in combinations(steps, r):
            combos.add(round(sum(combo), 1))
    return sorted(combos)


# ─────────────────────────────────────────────
# 5. [NEW] IEEE 519 Harmonic Analysis (from measured THD)
# ─────────────────────────────────────────────
def analyze_harmonics_ieee519(thdi_pct: float, thdv_pct: float, isc_il_ratio: float, voltage_level: str = "LV") -> dict:
    """
    Analyzes harmonic compliance per IEEE 519-2014 standard.
    
    Args:
        thdi_pct: Total Harmonic Distortion of Current (%)
        thdv_pct: Total Harmonic Distortion of Voltage (%)
        isc_il_ratio: Short-circuit current / Load current ratio (Isc/IL)
        voltage_level: "LV" (<1kV), "MV" (1-69kV), "HV" (69-161kV)
    
    Returns:
        dict with compliance status and recommendations
    """
    # IEEE 519-2014 TDD limits for Current (Table 2) based on Isc/IL
    # Applies to fundamental frequency component
    if isc_il_ratio < 20:
        tdd_limit = 5.0
        limit_label = "< 20"
    elif isc_il_ratio < 50:
        tdd_limit = 8.0
        limit_label = "20–50"
    elif isc_il_ratio < 100:
        tdd_limit = 12.0
        limit_label = "50–100"
    elif isc_il_ratio < 1000:
        tdd_limit = 15.0
        limit_label = "100–1000"
    else:
        tdd_limit = 20.0
        limit_label = "> 1000"

    # IEEE 519-2014 THDv limits (Table 1)
    if voltage_level == "LV":
        thdv_limit = 8.0
        indv_v_limit = 5.0
    elif voltage_level == "MV":
        thdv_limit = 5.0
        indv_v_limit = 3.0
    else:  # HV
        thdv_limit = 2.5
        indv_v_limit = 1.5

    current_ok = thdi_pct <= tdd_limit
    voltage_ok = thdv_pct <= thdv_limit

    # Risk assessment & recommendation
    recommendations = []
    overall_status = "PASS ✅"
    
    if not current_ok:
        overall_status = "FAIL ❌"
        excess_pct = thdi_pct - tdd_limit
        if excess_pct > 10:
            recommendations.append("🔴 THDi สูงมาก: แนะนำ **Active Harmonic Filter (AHF)** เพื่อลด THDi แบบ Real-time")
            recommendations.append("⚠️ พิจารณาแยก Bus Bar สำหรับโหลด Non-linear ออกจากระบบหลัก")
        else:
            recommendations.append("🟡 THDi เกินเกณฑ์เล็กน้อย: แนะนำ **Passive Harmonic Filter** หรือ **Detuned Reactor 7%**")
            
    if not voltage_ok:
        overall_status = "FAIL ❌" if current_ok else overall_status
        recommendations.append("🔴 THDv สูง: สัญญาณว่าระบบไฟฟ้ามีฮาร์มอนิกรุนแรง ควรตรวจสอบแหล่งกำเนิดฮาร์มอนิก")
        
    if current_ok and voltage_ok:
        recommendations.append("✅ ระบบอยู่ในเกณฑ์มาตรฐาน IEEE 519 ไม่จำเป็นต้องเพิ่มอุปกรณ์แก้ฮาร์มอนิก")
        if thdi_pct > tdd_limit * 0.8:
            recommendations.append("💡 THDi ใกล้เกณฑ์: ควรติดตามและวัดซ้ำหากมีการเพิ่มโหลด Non-linear")

    # Filter recommendation
    filter_recommendation = "ไม่จำเป็น"
    filter_cost_estimate = "0"
    if not current_ok or not voltage_ok:
        if thdi_pct > tdd_limit + 10 or thdv_pct > thdv_limit + 3:
            filter_recommendation = "Active Harmonic Filter (AHF)"
            filter_cost_estimate = "800,000 – 2,500,000 บาท"
        else:
            filter_recommendation = "Passive Detuned Filter / Reactor 7%"
            filter_cost_estimate = "50,000 – 200,000 บาท"

    return {
        "thdi_measured": thdi_pct,
        "thdv_measured": thdv_pct,
        "tdd_limit": tdd_limit,
        "thdv_limit": thdv_limit,
        "isc_il_ratio": isc_il_ratio,
        "limit_label": limit_label,
        "current_compliant": current_ok,
        "voltage_compliant": voltage_ok,
        "overall_status": overall_status,
        "recommendations": recommendations,
        "filter_recommendation": filter_recommendation,
        "filter_cost_estimate": filter_cost_estimate,
        "compliance_table": [
            {"พารามิเตอร์": "THDi (กระแส)", "ค่าที่วัดได้": f"{thdi_pct:.1f}%", "เกณฑ์ IEEE 519": f"≤ {tdd_limit:.0f}%", "สถานะ": "✅ ผ่าน" if current_ok else "❌ ไม่ผ่าน"},
            {"พารามิเตอร์": "THDv (แรงดัน)", "ค่าที่วัดได้": f"{thdv_pct:.1f}%", "เกณฑ์ IEEE 519": f"≤ {thdv_limit:.0f}%", "สถานะ": "✅ ผ่าน" if voltage_ok else "❌ ไม่ผ่าน"},
        ]
    }
