def calculate_roi(p_kw: float, pf1: float, pf2: float, qc_kvar: float, penalty_rate: float, cost_per_kvar: float) -> dict:
    """
    Estimates the return on investment (ROI) and payback period.
    """
    # 1. Cost Estimation
    total_investment = qc_kvar * cost_per_kvar
    
    # 2. Penalty Avoidance (Assuming penalty applies if PF < 0.85)
    # PEA/MEA standard: Q_limit = 0.6197 * P (which corresponds to PF = 0.85)
    # Penalty is applied per excess kVAR per month.
    
    q_limit = 0.6197 * p_kw
    
    import math
    q_current = p_kw * math.tan(math.acos(pf1))
    q_future = p_kw * math.tan(math.acos(pf2))
    
    current_penalty_kvar = max(0, q_current - q_limit)
    future_penalty_kvar = max(0, q_future - q_limit)
    
    monthly_penalty_saved = (current_penalty_kvar - future_penalty_kvar) * penalty_rate
    yearly_penalty_saved = monthly_penalty_saved * 12
    
    # 3. Energy Saving from Line Loss (estimated at 2% line loss reduction)
    loss_reduction_kw = p_kw * 0.02 * (1 - (pf1/pf2)**2)
    hours_per_year = 300 * 12 # 300 days, 12 hrs
    energy_saved_kwh = loss_reduction_kw * hours_per_year
    energy_cost_saving = energy_saved_kwh * 4.5 # Assume 4.5 THB/kWh
    
    total_yearly_saving = yearly_penalty_saved + energy_cost_saving
    
    payback_months = 0
    if total_yearly_saving > 0:
        payback_months = (total_investment / total_yearly_saving) * 12
        
    return {
        "investment_thb": total_investment,
        "yearly_saving_thb": total_yearly_saving,
        "monthly_penalty_saved": monthly_penalty_saved,
        "energy_saved_kwh_yr": energy_saved_kwh,
        "payback_months": payback_months
    }
