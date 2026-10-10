/*
* This module handles all external communication with the Gemini LLM service
* for stable translation and clean simplification, bypassing fragile Python libraries.
*/
const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent";
const API_KEY = "" // API key is automatically provided by the platform

export async function translateAndSimplify(text) {
    const systemPrompt = `You are an expert legal assistant. Your task is to analyze the input text.
    1. Translate the text into clear English.
    2. Identify the core legal topic and risk level (High/Medium/Low).
    3. Provide a clear, simple English paraphrase suitable for a non-lawyer.
    
    Format the output strictly as a JSON object with keys: english_text, simple_summary, risk_level.
    `;
    
    const userQuery = `Analyze this legal clause: "${text}"`;
    
    const payload = {
        contents: [{ parts: [{ text: userQuery }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] },
        generationConfig: {
            responseMimeType: "application/json",
            responseSchema: {
                type: "OBJECT",
                properties: {
                    "english_text": { "type": "STRING", description: "The clear English translation of the input." },
                    "simple_summary": { "type": "STRING", description: "A simple, non-jargon explanation of the clause." },
                    "risk_level": { "type": "STRING", description: "The predicted risk level (High, Medium, or Low)." }
                }
            }
        }
    };
    
    try {
        const response = await fetch(`${GEMINI_API_URL}?key=${API_KEY}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        
        if (!response.ok) {
            throw new Error(`API call failed with status: ${response.status}`);
        }

        const result = await response.json();
        const jsonText = result.candidates?.[0]?.content?.parts?.[0]?.text;
        
        if (jsonText) {
            return JSON.parse(jsonText);
        }
        throw new Error("Invalid response structure from LLM.");

    } catch (error) {
        console.error("Gemini API Error:", error);
        // Fallback for severe errors
        return {
            english_text: "Translation Failed. Analyzing original text.",
            simple_summary: "Multilingual analysis failed. Check network or retry.",
            risk_level: "Medium"
        };
    }
}