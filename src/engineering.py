import math

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

def check_harmonic_resonance(qc_kvar: float, trafo_kva: float, z_percent: float, v: float = 400.0) -> dict:
    if z_percent <= 0 or trafo_kva <= 0 or qc_kvar <= 0:
        return {"h_r": 0, "risk": "N/A", "message": "Invalid parameters", "tuning_factor": "-", "u_c_voltage": v, "detuned_p": 0.0}
        
    s_sc = trafo_kva / (z_percent / 100)
    h_r = math.sqrt(s_sc / qc_kvar)
    
    risk = "Low"
    message = "ปลอดภัยจาก Harmonic Resonance ทั่วไป"
    tuning_factor = "ไม่จำเป็น (0%)"
    detuned_p = 0.0
    
    # Check 5th (h=5) and 7th (h=7) which are common in 3-phase rectifiers
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

def calculate_detail_engineering(i_c_A: float, i_load_A: float, qc_kvar: float, trafo_kva: float, z_percent: float) -> dict:
    """
    Calculates detailed parameters: Cable sizing, Ventilation, CT ratio, and Short Circuit according to EIT 022001-22.
    """
    cable_amp_req = i_c_A * 1.35
    cb_amp_req = i_c_A * 1.43
    fuse_amp_req = i_c_A * 1.65
    
    # Standard IEC sizes (sq.mm) and approximate ampacity for THW in conduit
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
            
    # CT Ratio
    ct_primaries = [50, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1250, 1500, 2000, 2500, 3200, 4000]
    ct_primary = next((x for x in ct_primaries if x >= i_load_A * 1.2), ct_primaries[-1])
    ct_ratio = f"{ct_primary}/5A"
    
    # Ventilation
    watt_loss = qc_kvar * 5.0
    cfm_required = watt_loss / 3.0
    
    # Short Circuit
    trafo_fla = (trafo_kva * 1000) / (math.sqrt(3) * 400) 
    i_sc_A = trafo_fla / (z_percent / 100)
    i_sc_kA = i_sc_A / 1000.0
    
    standard_ka = [10, 16, 25, 36, 50, 65, 85, 100]
    recommended_ka = next((x for x in standard_ka if x >= i_sc_kA), standard_ka[-1])
    
    # Contactor per Step (Assuming 5 steps)
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
