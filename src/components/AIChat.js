"use client";

import { useState } from "react";
import { Send, Bot, User, Trash2 } from "lucide-react";

export default function AIChat({ inputs, qcTotal }) {
  const [history, setHistory] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  const buildContext = () => {
    return `
• กำลังไฟฟ้าจริง (P) = ${inputs.pKw} kW
• แรงดันไฟฟ้า (V) = ${inputs.voltage} V | ความถี่ = ${inputs.frequency} Hz
• Power Factor ปัจจุบัน (PF1) = ${inputs.pf1}
• Power Factor เป้าหมาย (PF2) = ${inputs.pf2}
• Qc ที่ต้องการติดตั้ง = ${qcTotal} kVAR
`;
  };

  const handleSend = async () => {
    if (!prompt.trim()) return;

    const userMessage = { role: "user", content: prompt };
    setHistory(prev => [...prev, userMessage]);
    setPrompt("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          history,
          prompt: userMessage.content,
          context: buildContext()
        })
      });

      const data = await res.json();
      if (res.ok) {
        setHistory(prev => [...prev, { role: "assistant", content: data.result }]);
      } else {
        setHistory(prev => [...prev, { role: "assistant", content: `❌ Error: ${data.error}` }]);
      }
    } catch (err) {
      setHistory(prev => [...prev, { role: "assistant", content: `❌ Request failed: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: 'var(--surface-color)', borderRadius: '12px', border: '1px solid var(--border-color)', padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <Bot size={24} color="var(--accent)" />
        <h3 style={{ margin: 0, color: 'var(--accent)', fontSize: '1.1rem' }}>AI ENGINEERING ASSISTANT</h3>
        <span style={{ marginLeft: 'auto', background: 'rgba(139, 92, 246, 0.1)', color: 'var(--accent)', padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.75rem', fontWeight: 'bold' }}>
          POWERED BY GEMINI
        </span>
      </div>

      <div style={{ 
        background: 'var(--bg-color)', 
        borderRadius: '8px', 
        height: '300px', 
        overflowY: 'auto', 
        padding: '1rem', 
        marginBottom: '1rem',
        border: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem'
      }}>
        {history.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: 'auto', marginBottom: 'auto', fontSize: '0.9rem' }}>
            ถามวิศวกร AI ได้เลยครับ เช่น 'ทำไมต้องใช้ Detuned Reactor?' หรือ 'ROI คุ้มไหม?'
          </div>
        ) : (
          history.map((msg, idx) => (
            <div key={idx} style={{ 
              display: 'flex', 
              gap: '0.75rem', 
              alignItems: 'flex-start',
              background: msg.role === 'user' ? 'rgba(14, 165, 233, 0.1)' : 'rgba(139, 92, 246, 0.1)',
              padding: '1rem',
              borderRadius: '8px',
              border: `1px solid ${msg.role === 'user' ? 'rgba(14, 165, 233, 0.2)' : 'rgba(139, 92, 246, 0.2)'}`
            }}>
              {msg.role === 'user' ? <User size={20} color="var(--primary)" /> : <Bot size={20} color="var(--accent)" />}
              <div style={{ color: 'var(--text-main)', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start', padding: '1rem' }}>
            <Bot size={20} color="var(--accent)" />
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>กำลังคิด...</div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <input 
          type="text" 
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="พิมพ์คำถามของคุณที่นี่..."
          style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-color)', color: 'var(--text-main)' }}
        />
        <button onClick={handleSend} disabled={loading} className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--accent)' }}>
          <Send size={18} />
        </button>
        {history.length > 0 && (
          <button onClick={() => setHistory([])} style={{ background: 'transparent', border: '1px solid var(--border-color)', color: '#ef4444', padding: '0 1rem', borderRadius: '8px' }}>
            <Trash2 size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
