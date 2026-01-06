/**
 * Language Detection Utility
 * Detects the language of user input and provides appropriate language codes
 */

/**
 * Detect if text contains Hindi/Devanagari script
 */
export const detectLanguage = (text) => {
  if (!text || typeof text !== 'string') return 'en';
  
  // Check for Hindi/Devanagari script (Unicode range: 0900-097F)
  const hindiRegex = /[\u0900-\u097F]/;
  const hasHindi = hindiRegex.test(text);
  
  // Check for common Hindi words (Romanized Hindi)
  const romanizedHindiWords = [
    'mujhe', 'aap', 'kyun', 'kya', 'kaise', 'kab', 'kahan', 'kisne', 
    'jankari', 'dijiye', 'bataye', 'samjhaiye', 'hindi', 'hindustan'
  ];
  const lowerText = text.toLowerCase();
  const hasRomanizedHindi = romanizedHindiWords.some(word => lowerText.includes(word));
  
  if (hasHindi || hasRomanizedHindi) {
    return 'hi'; // Hindi
  }
  
  return 'en'; // Default to English
};

/**
 * Get language code for speech recognition
 */
export const getSpeechRecognitionLang = (language) => {
  const langMap = {
    'en': 'en-IN', // Indian English
    'hi': 'hi-IN', // Hindi (India)
    'es': 'es-ES',
    'fr': 'fr-FR'
  };
  return langMap[language] || 'en-IN';
};

/**
 * Get language code for text-to-speech
 */
export const getSpeechSynthesisLang = (language) => {
  const langMap = {
    'en': 'en-IN', // Indian English
    'hi': 'hi-IN', // Hindi (India)
    'es': 'es-ES',
    'fr': 'fr-FR'
  };
  return langMap[language] || 'en-IN';
};

/**
 * Get language name for display
 */
export const getLanguageName = (code) => {
  const names = {
    'en': 'English',
    'hi': 'हिंदी (Hindi)',
    'es': 'Español',
    'fr': 'Français'
  };
  return names[code] || 'English';
};


