from fpdf import FPDF
import datetime
import os

class PFCReport(FPDF):
    def header(self):
        # We assume fonts are already added before add_page()
        try:
            self.set_font('Tahoma', 'B', 15)
        except:
            self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, 'Advanced PFC Analyzer - PRO Engineering Report', 0, 1, 'C')
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        try:
            self.set_font('Tahoma', '', 8)
        except:
            self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def clean_text(text: str) -> str:
    import re
    return re.sub(r'[\u0E00-\u0E7F]+', '', str(text)).replace('()', '').strip()

def generate_report(params: dict, output_path: str):
    pdf = PFCReport()
    
    font_path = r"C:\Windows\Fonts\tahoma.ttf"
    font_bold = r"C:\Windows\Fonts\tahomabd.ttf"
    has_tahoma = os.path.exists(font_path) and os.path.exists(font_bold)
    
    if has_tahoma:
        pdf.add_font('Tahoma', '', font_path)
        pdf.add_font('Tahoma', 'B', font_bold)
    else:
        # If no Thai font, remove Thai characters to prevent crash
        for k, v in params.items():
            if isinstance(v, str):
                params[k] = clean_text(v)

    pdf.add_page()
    
    def set_font(style, size):
        if has_tahoma:
            pdf.set_font('Tahoma', style, size)
        else:
            pdf.set_font('Helvetica', style, size)
            
    # Meta
    set_font('', 10)
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'R')
    
    # 1. System Parameters
    set_font('B', 12)
    pdf.cell(0, 10, "1. System Parameters", 0, 1)
    set_font('', 10)
    pdf.cell(0, 8, f"- Active Power (P): {params['p_kw']:.2f} kW", 0, 1)
    pdf.cell(0, 8, f"- Voltage: {params['voltage']} V", 0, 1)
    pdf.cell(0, 8, f"- Current Power Factor: {params['pf1']}", 0, 1)
    pdf.cell(0, 8, f"- Target Power Factor: {params['pf2']}", 0, 1)
    pdf.ln(5)
    
    # 2. Engineering Results & Detail Design
    set_font('B', 12)
    pdf.cell(0, 10, "2. Detailed Engineering Design", 0, 1)
    set_font('', 10)
    pdf.cell(0, 8, f"- Required Reactive Power (Qc): {params['qc_kvar']:.2f} kVAR", 0, 1)
    pdf.cell(0, 8, f"- Rated Current (In): {params['i_c']:.2f} A", 0, 1)
    pdf.cell(0, 8, f"- Main Breaker: {params['cb_rating']} AT (Short Circuit >= {params['breaker_ka']} kA)", 0, 1)
    pdf.cell(0, 8, f"- Recommended Main Cable: {params['cable_size']}", 0, 1)
    pdf.cell(0, 8, f"- Required CT Ratio: {params['ct_ratio']}", 0, 1)
    pdf.cell(0, 8, f"- Enclosure Ventilation Req: >= {params['cfm']:.0f} CFM", 0, 1)
    pdf.ln(5)
    
    # 3. Harmonics
    if 'h_r' in params and params['h_r'] > 0:
        set_font('B', 12)
        pdf.cell(0, 10, "3. Harmonic Resonance Risk Assessment", 0, 1)
        set_font('', 10)
        pdf.cell(0, 8, f"- Resonance Order (h_r): {params['h_r']:.2f}", 0, 1)
        pdf.cell(0, 8, f"- Risk Level: {params['risk']} ({params['risk_msg']})", 0, 1)
        pdf.cell(0, 8, f"- Detuned Reactor Spec: {params['tuning_factor']}", 0, 1)
        pdf.ln(5)
        
    # 4. Financials
    if 'roi' in params:
        set_font('B', 12)
        pdf.cell(0, 10, "4. Financial & Environmental Impact", 0, 1)
        set_font('', 10)
        roi = params['roi']
        pdf.cell(0, 8, f"- Estimated Investment: {roi['investment_thb']:,.2f} THB", 0, 1)
        pdf.cell(0, 8, f"- Yearly Total Savings: {roi['yearly_saving_thb']:,.2f} THB/Year", 0, 1)
        pdf.cell(0, 8, f"- Estimated Payback Period: {roi['payback_months']:.1f} Months", 0, 1)
        pdf.cell(0, 8, f"- CO2 Emission Reduction: {params['co2']:.2f} kgCO2e/Year", 0, 1)

    pdf.output(output_path)
    return output_path
