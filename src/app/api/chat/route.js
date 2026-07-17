import { NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';

export async function POST(req) {
  try {
    const { history, prompt, context } = await req.json();

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: 'GEMINI_API_KEY is not set in environment variables.' },
        { status: 500 }
      );
    }

    const ai = new GoogleGenAI({ apiKey });

    const systemInstruction = `
คุณเป็น "AI วิศวกรผู้เชี่ยวชาญด้าน Power Factor Correction" ที่ถูกฝังอยู่ในระบบวิเคราะห์ PFC ขั้นสูง
คุณต้องตอบเป็นภาษาไทยเสมอ ยกเว้นคำศัพท์เทคนิคที่ไม่มีคำแปลที่เหมาะสม
ข้อมูลบริบทระบบปัจจุบัน:
${context}
ตอบคำถามให้กระชับ ถูกต้อง และมีมาตรฐานทางวิศวกรรมอ้างอิง
`;

    // Convert history to genai format
    const contents = history.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'model',
      parts: [{ text: msg.content }]
    }));
    
    // Add current prompt
    contents.push({
      role: 'user',
      parts: [{ text: prompt }]
    });

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: contents,
      config: {
        systemInstruction: systemInstruction,
        temperature: 0.7,
      }
    });

    return NextResponse.json({ result: response.text });

  } catch (error) {
    console.error("Chat API Error:", error);
    return NextResponse.json(
      { error: error.message || 'An error occurred during AI generation' },
      { status: 500 }
    );
  }
}
