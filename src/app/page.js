"use client";

import { useState, useEffect, useRef } from "react";
import { Moon, Sun, Download, Upload, LogIn, Settings, ChevronRight } from "lucide-react";
import Tab1Engineering from "../components/Tab1Engineering";
import Tab2StepConfig from "../components/Tab2StepConfig";
import Tab3Harmonic from "../components/Tab3Harmonic";
import Tab4PowerTriangle from "../components/Tab4PowerTriangle";
import Tab5ROI from "../components/Tab5ROI";
import Tab6BOQ from "../components/Tab6BOQ";
import Tab7Solar from "../components/Tab7Solar";
import AIChat from "../components/AIChat";
import { calculate_q_and_c } from "../utils/engineering";

const TABS = [
  "⚙️ Detail Engineering",
  "🔋 Step Configuration",
  "📡 IEEE 519 Harmonic",
  "📐 Power Triangle",
  "💰 ROI & สิ่งแวดล้อม",
  "📋 BOQ / ใบเสนอราคา",
  "☀️ Solar & PDF"
];

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLightMode, setIsLightMode] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  const [activeTab, setActiveTab] = useState(0);
  const [inputs, setInputs] = useState({
    phase: 3,
    pKw: 150.0,
    pf1: 0.75,
    pf2: 0.95,
    voltage: 380.0,
    frequency: 50.0,
    trafoKva: 500.0,
    zPercent: 4.0,
    
    // Advanced Load Profile
    enableLoadProfile: false,
    pBase: 45.0,
    pfBase: 0.65,
    hrsPeak: 8.0,
    hrsBase: 16.0,
    
    // Harmonic & IEEE 519
    enableIeee519: true,
    thdiPct: 12.0,
    thdvPct: 3.5,
    iscIl: 20.0,
    vlKey: "LV",
    dominants: ["5th", "7th"],
    
    // Step & BOQ Config
    numStepsPref: 5,
    useDetuned: false,
    energyRate: 4.5,
    demandCharge: 0.0,
    penaltyRate: 56.07,
    costPerKvar: 1500.0,
    overheadPct: 0.1,
  });

  // Handle Theme Toggle
  useEffect(() => {
    if (isLightMode) {
      document.documentElement.classList.add("light-mode");
    } else {
      document.documentElement.classList.remove("light-mode");
    }
  }, [isLightMode]);

  const tabsRef = useRef(null);

  useEffect(() => {
    const el = tabsRef.current;
    if (!el) return;
    
    const handleWheel = (e) => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        el.scrollLeft += e.deltaY;
      }
    };
    
    // Use passive: false so we can preventDefault() and stop vertical page scroll
    el.addEventListener("wheel", handleWheel, { passive: false });
    return () => el.removeEventListener("wheel", handleWheel);
  }, [isAuthenticated]);

  const handleLogin = (e) => {
    e.preventDefault();
    if (password === "jaidum02357") {
      setIsAuthenticated(true);
    } else {
      setErrorMsg("รหัสผ่านไม่ถูกต้อง");
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setInputs(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : (parseFloat(value) || value) 
    }));
  };

  const saveProject = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(inputs, null, 2));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "pfc_project.json");
    dlAnchorElem.click();
  };

  const loadProject = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const loadedData = JSON.parse(event.target.result);
          setInputs(prev => ({ ...prev, ...loadedData }));
          alert("✅ โหลดโปรเจกต์สำเร็จ!");
        } catch (error) {
          alert("❌ ไม่สามารถโหลดไฟล์ได้ รูปแบบ JSON ไม่ถูกต้อง");
        }
      };
      reader.readAsText(file);
    }
  };

  if (!isAuthenticated) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: 'var(--bg-color)' }}>
        <form onSubmit={handleLogin} className="glass-panel" style={{ padding: '2.5rem', width: '100%', maxWidth: '400px', textAlign: 'center' }}>
          <h2 style={{ color: 'var(--primary)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <span>⚡</span> PFC PRO
          </h2>
          <input 
            type="password" 
            placeholder="รหัสผ่านเข้าใช้งาน" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ marginBottom: '1rem' }}
          />
          {errorMsg && <p style={{ color: '#ef4444', fontSize: '0.85rem', marginBottom: '1rem' }}>{errorMsg}</p>}
          <button type="submit" className="btn-primary" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
            <LogIn size={18} /> เข้าสู่ระบบ
          </button>
        </form>
      </div>
    );
  }

  const q_and_c_results = calculate_q_and_c(
    inputs.pKw, inputs.voltage, inputs.frequency, inputs.pf1, inputs.pf2, inputs.phase
  );
  const qcTotal = q_and_c_results.Qc_total_kVAR;

  // Render input row helper
  const renderInputRow = (label, name, min, max, step) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
      <label style={{ fontSize: '0.8rem', color: 'var(--text-main)' }}>{label}</label>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <input 
          type="number" 
          name={name} 
          value={inputs[name]} 
          onChange={handleChange} 
          step={step}
          style={{ width: '80px', padding: '0.25rem 0.5rem', background: 'var(--bg-color)', border: '1px solid var(--border-color)', color: 'var(--text-main)', borderRadius: '4px', fontSize: '0.85rem' }} 
        />
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg-color)', position: 'relative' }}>
      
      {/* Animated Sidebar Wrapper (Overlay) */}
      <div style={{ position: 'absolute', top: 0, bottom: 0, left: 0, zIndex: 100, display: 'flex', pointerEvents: 'none' }}>
        
        {/* The Sidebar Panel */}
        <div 
          style={{
            width: isSidebarOpen ? '340px' : '0px',
            transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            background: 'var(--surface-color)',
            borderRight: isSidebarOpen ? '1px solid var(--border-color)' : 'none',
            height: '100%',
            overflow: 'hidden',
            boxShadow: isSidebarOpen ? '4px 0 25px rgba(0,0,0,0.5)' : 'none',
            pointerEvents: 'auto',
          }}
        >
          {/* Inner Content (Fixed width so it doesn't wrap during animation) */}
          <div className="hide-scrollbar" style={{ 
            width: '340px', 
            height: '100%', 
            overflowY: 'auto', 
            padding: '1.5rem',
            opacity: isSidebarOpen ? 1 : 0,
            transition: 'opacity 0.2s ease',
            visibility: isSidebarOpen ? 'visible' : 'hidden'
          }}>
            
            <h2 style={{ color: 'var(--primary)', marginBottom: '2rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>⚡</span> PFC PRO
            </h2>

            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>⚙️ 1. พารามิเตอร์ระบบไฟฟ้า</h4>
              
              <div style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>ระบบไฟฟ้า</div>
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <input type="radio" name="phase" value={3} checked={inputs.phase === 3} onChange={handleChange} /> 3 เฟส
                </label>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <input type="radio" name="phase" value={1} checked={inputs.phase === 1} onChange={handleChange} /> 1 เฟส
                </label>
              </div>

              <label style={{ display: 'flex', alignItems: 'center', fontSize: '0.85rem', marginBottom: '1rem', cursor: 'pointer', color: '#f97316' }}>
                <input type="checkbox" name="enableLoadProfile" checked={inputs.enableLoadProfile} onChange={handleChange} style={{ width: 'auto', marginRight: '0.5rem' }} />
                📊 โหมดโปรไฟล์โหลด (Advance Load Profile)
              </label>
              
              {inputs.enableLoadProfile ? (
                <div className="animate-fade-in" style={{ padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
                  <div style={{ color: '#f97316', fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>🔥 Peak Load</div>
                  {renderInputRow("P (kW)", "pKw", 0, 10000, 10)}
                  {renderInputRow("PF", "pf1", 0.1, 0.99, 0.01)}
                  {renderInputRow("Hours/Day", "hrsPeak", 0, 24, 1)}

                  <div style={{ color: '#0ea5e9', fontSize: '0.8rem', fontWeight: 'bold', margin: '1rem 0 0.5rem' }}>🌙 Base Load</div>
                  {renderInputRow("P Base (kW)", "pBase", 0, 10000, 10)}
                  {renderInputRow("PF Base", "pfBase", 0.1, 0.99, 0.01)}
                  {renderInputRow("Hours/Day", "hrsBase", 0, 24, 1)}
                </div>
              ) : (
                <div style={{ marginBottom: '1rem' }}>
                  {renderInputRow("กำลังไฟฟ้าจริง P (kW)", "pKw", 0, 10000, 10)}
                  <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem', color: 'var(--primary)', marginTop: '0.5rem' }}>
                    PF ปัจจุบัน <span>{inputs.pf1}</span>
                  </label>
                  <input type="range" name="pf1" min="0.5" max="0.99" step="0.01" value={inputs.pf1} onChange={handleChange} style={{ marginBottom: '0.5rem' }} />
                </div>
              )}

              {renderInputRow("แรงดันไฟฟ้า V (Volt)", "voltage", 100, 33000, 10)}
              {renderInputRow("ความถี่ f (Hz)", "frequency", 40, 60, 1)}
            </div>

            <div style={{ marginBottom: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>🎯 2. เป้าหมายการปรับปรุง</h4>
              <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.5rem', color: 'var(--secondary)' }}>
                PF เป้าหมาย <span>{inputs.pf2}</span>
              </label>
              <input type="range" name="pf2" min="0.8" max="1.0" step="0.01" value={inputs.pf2} onChange={handleChange} />
            </div>

            <div style={{ marginBottom: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>⚠️ 3. หม้อแปลงและฮาร์มอนิก</h4>
              {renderInputRow("พิกัดหม้อแปลง (kVA)", "trafoKva", 50, 5000, 50)}
              {renderInputRow("อิมพีแดนซ์ (%Z)", "zPercent", 1, 10, 0.1)}
            </div>

            <div style={{ marginBottom: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>📡 4. ค่าฮาร์มอนิก (IEEE 519)</h4>
              <label style={{ display: 'flex', alignItems: 'center', fontSize: '0.85rem', marginBottom: '1rem', cursor: 'pointer' }}>
                <input type="checkbox" name="enableIeee519" checked={inputs.enableIeee519} onChange={handleChange} style={{ width: 'auto', marginRight: '0.5rem' }} />
                เปิดใช้งานการวิเคราะห์ IEEE 519
              </label>
              {inputs.enableIeee519 && (
                <div className="animate-fade-in" style={{ padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  {renderInputRow("THDi กระแส (%)", "thdiPct", 0, 200, 0.5)}
                  {renderInputRow("THDv แรงดัน (%)", "thdvPct", 0, 50, 0.5)}
                  {renderInputRow("Isc/IL Ratio", "iscIl", 1, 2000, 5)}

                  <div style={{ marginTop: '1rem' }}>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-main)', display: 'block', marginBottom: '0.5rem' }}>ระดับแรงดันระบบ</label>
                    <select name="vlKey" value={inputs.vlKey} onChange={handleChange} style={{ width: '100%', padding: '0.5rem', background: 'var(--bg-color)', border: '1px solid var(--border-color)', color: 'var(--text-main)', borderRadius: '4px', fontSize: '0.85rem' }}>
                      <option value="LV">LV (&lt; 1 kV)</option>
                      <option value="MV">MV (1 - 69 kV)</option>
                      <option value="HV">HV (&gt; 69 kV)</option>
                    </select>
                  </div>

                  <div style={{ marginTop: '1rem' }}>
                    <label style={{ fontSize: '0.8rem', color: 'var(--text-main)', display: 'block', marginBottom: '0.5rem' }}>ฮาร์มอนิกที่โดดเด่น (Dominant)</label>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {["3rd", "5th", "7th", "11th", "13th"].map(h => (
                        <button
                          key={h}
                          onClick={() => {
                            setInputs(prev => ({
                              ...prev,
                              dominants: prev.dominants.includes(h) 
                                ? prev.dominants.filter(d => d !== h) 
                                : [...prev.dominants, h]
                            }))
                          }}
                          style={{
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            background: inputs.dominants.includes(h) ? '#ef4444' : 'var(--surface-color)',
                            color: inputs.dominants.includes(h) ? 'white' : 'var(--text-muted)',
                            border: `1px solid ${inputs.dominants.includes(h) ? '#ef4444' : 'var(--border-color)'}`,
                            cursor: 'pointer'
                          }}
                        >
                          {h} {inputs.dominants.includes(h) && '✕'}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginBottom: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>🔧 5. การจัดสเต็ปคาปาซิเตอร์</h4>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-main)' }}>จำนวนสเต็ปที่ต้องการ</label>
                <select name="numStepsPref" value={inputs.numStepsPref} onChange={handleChange} style={{ width: '80px', padding: '0.25rem', background: 'var(--bg-color)', border: '1px solid var(--border-color)', color: 'var(--text-main)', borderRadius: '4px', fontSize: '0.85rem' }}>
                  <option value={3}>3</option>
                  <option value={4}>4</option>
                  <option value={5}>5</option>
                  <option value={6}>6</option>
                  <option value={8}>8</option>
                </select>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', fontSize: '0.85rem', cursor: 'pointer', marginTop: '0.5rem' }}>
                <input type="checkbox" name="useDetuned" checked={inputs.useDetuned} onChange={handleChange} style={{ width: 'auto', marginRight: '0.5rem' }} />
                ติดตั้ง Detuned Reactor 7%
              </label>
            </div>

            <div style={{ marginBottom: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>💰 6. พารามิเตอร์ทางการเงิน</h4>
              {renderInputRow("ค่าพลังงาน (บาท/kWh)", "energyRate", 1, 10, 0.1)}
              {renderInputRow("Demand Charge (บาท/kVA)", "demandCharge", 0, 1000, 10)}
              {renderInputRow("ค่าปรับ (บาท/kVAR/เดือน)", "penaltyRate", 0, 500, 1)}
              {renderInputRow("ราคาตู้ (บาท/kVAR)", "costPerKvar", 500, 5000, 100)}
              <label style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem', marginTop: '0.5rem' }}>
                Overhead/Profit <span>{(inputs.overheadPct * 100).toFixed(0)}%</span>
              </label>
              <input type="range" name="overheadPct" min="0" max="0.5" step="0.01" value={inputs.overheadPct} onChange={handleChange} />
            </div>

            <div style={{ marginBottom: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
              <h4 style={{ color: 'var(--primary)', marginBottom: '0.5rem', fontSize: '0.9rem' }}>💾 7. บันทึก / โหลด</h4>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={saveProject} className="btn-primary" style={{ flex: 1, padding: '0.5rem', fontSize: '0.8rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.25rem' }}>
                  <Download size={14} /> บันทึก
                </button>
                <label className="btn-primary" style={{ flex: 1, padding: '0.5rem', fontSize: '0.8rem', textAlign: 'center', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.25rem' }}>
                  <Upload size={14} /> โหลด
                  <input type="file" accept=".json" onChange={loadProject} style={{ display: 'none' }} />
                </label>
              </div>
            </div>
            
          </div>
        </div>

        {/* The Toggle Button (attached to the edge) */}
        <div style={{ display: 'flex', alignItems: 'center', pointerEvents: 'auto' }}>
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            style={{
              background: 'var(--surface-color)',
              border: '1px solid var(--border-color)',
              borderLeft: 'none',
              padding: '1.5rem 0.25rem',
              borderTopRightRadius: '8px',
              borderBottomRightRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '4px 0 10px rgba(0,0,0,0.2)',
              cursor: 'pointer',
              color: 'var(--primary)'
            }}
          >
            <div style={{ writingMode: 'vertical-rl', letterSpacing: '2px', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              SETTINGS <ChevronRight size={16} style={{ transform: isSidebarOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.3s' }} />
            </div>
          </button>
        </div>
      </div>

      {/* Main Content (pushed slightly to avoid overlap with the closed button) */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', paddingLeft: '32px' }}>
        
        {/* Scrollable Area */}
        <div style={{ flex: 1, padding: '1.5rem 2rem', overflowY: 'auto' }}>
          
          {/* Banner */}
          <div style={{ 
            background: 'var(--surface-color)', 
            border: '1px solid var(--border-color)', 
            borderRadius: '12px', 
            padding: '1.5rem', 
            marginBottom: '2rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            <div>
              <h1 style={{ fontSize: '1.5rem', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                ⚡ PFC PRO ANALYZER
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: '0.5rem 0 0 0' }}>
                ระบบวิเคราะห์และออกแบบ Power Factor ขั้นสูง · Detail Engineering Design · AI-Powered
              </p>
            </div>
            <button 
              onClick={() => setIsLightMode(!isLightMode)}
              style={{ 
                background: 'transparent', 
                border: '1px solid var(--border-color)', 
                color: 'var(--text-main)', 
                padding: '0.5rem', 
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
              title="Toggle Light/Dark Mode"
            >
              {isLightMode ? <Moon size={20} /> : <Sun size={20} />}
            </button>
          </div>
          
          {/* Tabs Navigation */}
          <div className="tabs-container" ref={tabsRef}>
            {TABS.map((tab, idx) => (
              <button
                key={idx}
                onClick={() => setActiveTab(idx)}
                className={`tab-btn ${activeTab === idx ? 'active' : ''}`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Tab Content Area */}
          <div style={{ marginBottom: '2rem' }}>
            {activeTab === 0 && <Tab1Engineering inputs={inputs} />}
            {activeTab === 1 && <Tab2StepConfig qcTotal={qcTotal} inputs={inputs} />}
            {activeTab === 2 && <Tab3Harmonic inputs={inputs} qcTotal={qcTotal} />}
            {activeTab === 3 && <Tab4PowerTriangle inputs={inputs} />}
            {activeTab === 4 && <Tab5ROI inputs={inputs} qcTotal={qcTotal} />}
            {activeTab === 5 && <Tab6BOQ inputs={inputs} qcTotal={qcTotal} />}
            {activeTab === 6 && <Tab7Solar inputs={inputs} qcTotal={qcTotal} />}
          </div>
          
          {/* AI Chat Box */}
          <div style={{ marginTop: '3rem', borderTop: '1px solid var(--border-color)', paddingTop: '2rem' }}>
             <AIChat inputs={inputs} qcTotal={qcTotal} />
          </div>

        </div>
      </main>
    </div>
  );
}
