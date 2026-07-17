import pandas as pd

def process_load_profile(file) -> dict:
    """
    Processes an uploaded CSV/Excel file containing load profile.
    Expected columns: Month, ActivePower_kW, ApparentPower_kVA, PF
    Returns worst-case scenario and summary.
    """
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
            
        # Ensure required columns exist
        required_cols = ['Month', 'ActivePower_kW', 'PF']
        if not all(col in df.columns for col in required_cols):
            return {"success": False, "error": f"Missing required columns: {', '.join(required_cols)}"}
            
        # Find the month with lowest PF
        worst_pf_row = df.loc[df['PF'].idxmin()]
        
        # Calculate average P and PF
        avg_p = df['ActivePower_kW'].mean()
        avg_pf = df['PF'].mean()
        
        return {
            "success": True,
            "data": df,
            "worst_case": {
                "month": worst_pf_row['Month'],
                "p_kw": worst_pf_row['ActivePower_kW'],
                "pf": worst_pf_row['PF']
            },
            "summary": {
                "avg_p_kw": avg_p,
                "avg_pf": avg_pf
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
