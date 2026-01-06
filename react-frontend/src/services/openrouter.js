/**
 * OpenRouter API Service
 * Connects to OpenRouter API for chatbot functionality
 */

const OPENROUTER_API_KEY = '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';
const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions';
// Model: User requested google/gemini-2.5-flash-lite
// If this model doesn't work, try: 'google/gemini-2.0-flash-exp:free'
const MODEL = 'google/gemini-2.5-flash-lite';

/**
 * Send a message to the chatbot via OpenRouter
 * @param {string} message - User's message
 * @param {Array} conversationHistory - Previous messages in the conversation
 * @returns {Promise<Object>} - Response from the API
 */
export const sendChatMessage = async (message, conversationHistory = [], userLanguage = 'en') => {
  try {
    // Detect language from message if not provided
    const detectLanguage = (text) => {
      if (!text || typeof text !== 'string') return 'en';
      const hindiRegex = /[\u0900-\u097F]/;
      const romanizedHindiWords = ['mujhe', 'aap', 'kyun', 'kya', 'kaise', 'jankari', 'dijiye', 'bataye', 'samjhaiye'];
      const lowerText = text.toLowerCase();
      return (hindiRegex.test(text) || romanizedHindiWords.some(word => lowerText.includes(word))) ? 'hi' : 'en';
    };
    
    const detectedLang = detectLanguage(message);
    const responseLanguage = detectedLang === 'hi' ? 'hi' : userLanguage;
    
    // Format conversation history for OpenRouter
            // Determine if user is a lawyer based on conversation context or explicit role
            const isLawyer = conversationHistory.some(msg => 
              msg.role === 'system' && (msg.content?.includes('lawyer') || msg.content?.includes('lawyer_india'))
            ) || false;

            // Multilingual system prompts
            const systemPrompt = isLawyer
              ? responseLanguage === 'hi'
                ? 'आप LexSaksham के लिए एक पेशेवर कानूनी अनुसंधान सहायक हैं, जो एक भारतीय अनुबंध विश्लेषण प्लेटफॉर्म है। आप भारतीय कानून में विशेषज्ञ हैं और वकीलों की मदद करते हैं:\n\n1. भारतीय अनुबंध अधिनियम, 1872 के तहत अनुबंधों को समझना\n2. भारतीय कानूनों (कंपनी अधिनियम, 2013, उपभोक्ता संरक्षण अधिनियम, आदि) के साथ जोखिम और अनुपालन का विश्लेषण\n3. भारत के सर्वोच्च न्यायालय के निर्णयों और उच्च न्यायालय के मिसालों को खोजना और समझाना\n4. भारतीय अदालतों (SC, HC, NCLT, आदि) से केस लॉ संदर्भ प्रदान करना\n5. भारतीय कानूनी मिसालों को विशिष्ट खंडों पर कैसे लागू किया जाए, यह समझाना\n6. भारतीय अनुबंध कानून, वाणिज्यिक कानून और कॉर्पोरेट कानून पर कानूनी अनुसंधान\n7. भारतीय नियमों (SEBI, RBI, GST, आदि) के साथ अनुपालन\n\nमहत्वपूर्ण: हमेशा भारतीय कानूनों, भारत के सर्वोच्च न्यायालय के निर्णयों और भारतीय कानूनी मिसालों का संदर्भ दें। भारतीय कानूनी शब्दावली का उपयोग करें। केस उद्धरण के लिए भारतीय केस उद्धरण प्रारूप का उपयोग करें। पेशेवर, सटीक रहें और भारतीय कानूनी स्रोतों का उल्लेख करें।'
                : 'You are a professional legal research assistant for LexSaksham, an Indian contract analysis platform. You specialize in Indian law and help lawyers with:\n\n1. Understanding contracts under the Indian Contract Act, 1872\n2. Analyzing risks and compliance with Indian laws (Companies Act, 2013, Consumer Protection Act, etc.)\n3. Finding and explaining relevant Supreme Court of India judgments and High Court precedents\n4. Providing case law references from Indian courts (SC, HC, NCLT, etc.)\n5. Explaining how Indian legal precedents apply to specific clauses\n6. Legal research on Indian contract law, commercial law, and corporate law\n7. Compliance with Indian regulations (SEBI, RBI, GST, etc.)\n\nIMPORTANT: Always reference Indian laws, Supreme Court of India judgments, and Indian legal precedents. Use Indian legal terminology (e.g., "agreement", "consideration", "void", "voidable" as per Indian Contract Act). When citing cases, use Indian case citation format (e.g., "AIR 2020 SC 1234" or "2020 SCC Online SC 123"). Be professional, accurate, and cite Indian legal sources.'
              : responseLanguage === 'hi'
                ? 'आप LexSaksham के लिए एक सहायक कानूनी सहायक हैं, जो एक भारतीय अनुबंध विश्लेषण प्लेटफॉर्म है। आप उपयोगकर्ताओं को भारतीय कानून के तहत अनुबंधों को समझने, भारतीय अनुबंध अधिनियम, 1872 के अनुसार कानूनी खंडों का विश्लेषण करने, जोखिमों का आकलन करने और भारतीय कानूनी संदर्भ में अनुबंध प्रबंधन पर मार्गदर्शन प्रदान करने में मदद करते हैं।\n\nमहत्वपूर्ण: हमेशा भारतीय कानूनों और नियमों के आधार पर सलाह दें। भारतीय कानूनी अवधारणाओं, भारत के सर्वोच्च न्यायालय के निर्णयों (जब प्रासंगिक हो) और भारतीय अनुपालन आवश्यकताओं का संदर्भ दें। भारतीय कानूनी शब्दावली का उपयोग करें और अवधारणाओं को भारतीय कानून के संदर्भ में समझाएं। संक्षिप्त, पेशेवर और सटीक रहें।'
                : 'You are a helpful legal assistant for LexSaksham, an Indian contract analysis platform. You help users understand contracts under Indian law, analyze legal clauses as per the Indian Contract Act, 1872, assess risks, and provide guidance on contract management in the Indian legal context.\n\nIMPORTANT: Always provide advice based on Indian laws and regulations. Reference Indian legal concepts, Supreme Court of India judgments when relevant, and Indian compliance requirements. Use Indian legal terminology and explain concepts in the context of Indian law. Be concise, professional, and accurate.';

            // Add language instruction to system prompt
            const languageInstruction = responseLanguage === 'hi' 
              ? '\n\nCRITICAL: The user is communicating in Hindi. You MUST respond in Hindi (हिंदी). Use Devanagari script when possible, or Romanized Hindi if needed. Always maintain the same language as the user.'
              : '\n\nCRITICAL: Respond in the same language as the user. If user writes in English, respond in English. If user writes in Hindi, respond in Hindi.';

            const messages = [
              {
                role: 'system',
                content: systemPrompt + languageInstruction
              },
      ...conversationHistory.map(msg => ({
        role: msg.role || (msg.type === 'user' ? 'user' : 'assistant'),
        content: msg.content || msg.message
      })),
      {
        role: 'user',
        content: message
      }
    ];

    console.log('Sending request to OpenRouter:', { model: MODEL, messageCount: messages.length });

    const response = await fetch(OPENROUTER_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'HTTP-Referer': window.location.origin,
        'X-Title': 'LexSaksham Contract Assistant'
      },
      body: JSON.stringify({
        model: MODEL,
        messages: messages,
        temperature: 0.7,
        max_tokens: 1000
      })
    });

    console.log('OpenRouter response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ 
        error: `HTTP ${response.status}: ${response.statusText}` 
      }));
      console.error('OpenRouter API error response:', errorData);
      
      // Better error message extraction
      const errorMessage = errorData.error?.message || 
                         errorData.error?.text || 
                         errorData.error || 
                         errorData.message ||
                         `Failed to get response: ${response.status} ${response.statusText}`;
      
      throw new Error(errorMessage);
    }

    const data = await response.json();
    console.log('OpenRouter API response:', data);
    
    // Handle different response structures
    if (data.choices && data.choices.length > 0) {
      const content = data.choices[0].message?.content || 
                     data.choices[0].text || 
                     data.choices[0].delta?.content;
      
      if (content) {
        return {
          success: true,
          message: content,
          usage: data.usage,
          model: data.model || MODEL
        };
      } else {
        console.error('No content in response:', data.choices[0]);
        throw new Error('Response received but no content found');
      }
    } else if (data.message) {
      // Some APIs return message directly
      return {
        success: true,
        message: data.message,
        usage: data.usage,
        model: data.model || MODEL
      };
    } else {
      console.error('Unexpected response structure:', data);
      throw new Error('Unexpected response format from API');
    }
  } catch (error) {
    console.error('OpenRouter API error:', error);
    
    // Provide more helpful error messages
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      throw new Error('API key is invalid or expired. Please check your OpenRouter API key.');
    } else if (error.message.includes('429')) {
      throw new Error('Rate limit exceeded. Please try again in a moment.');
    } else if (error.message.includes('model')) {
      throw new Error(`Model "${MODEL}" may not be available. Please check the model name.`);
    } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
      throw new Error('Network error. Please check your internet connection.');
    }
    
    throw error;
  }
};

/**
 * Check if OpenRouter API is accessible
 */
export const checkOpenRouterConnection = async () => {
  try {
    const response = await fetch(OPENROUTER_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'user', content: 'test' }],
        max_tokens: 5
      })
    });
    return response.ok;
  } catch (error) {
    return false;
  }
};

