import re

with open('frontend/src/pages/ChatPage.jsx', 'r', encoding='utf-8') as f:
    code = f.read()

# Import locales
code = code.replace("import logo from '../assets/logo.png';", "import logo from '../assets/logo.png';\nimport locales from '../locales.json';")

# Update language state
code = code.replace(
    "const [language, setLanguage] = useState('en');",
    "const [language, setLanguage] = useState(localStorage.getItem('sewasaathi_lang') || 'en');\n  useEffect(() => { document.documentElement.lang = language; localStorage.setItem('sewasaathi_lang', language); }, [language]);\n  const t = locales[language] || locales['en'];"
)

# Update SpeechRecognition lang
code = code.replace(
    "recognition.lang = language === 'hi' ? 'hi-IN' : language === 'pa' ? 'pa-IN' : 'en-IN';",
    "recognition.lang = t.recognitionLang;"
)

# Update SpeechSynthesis lang
code = code.replace(
    "const utterance = new SpeechSynthesisUtterance(text);",
    "const utterance = new SpeechSynthesisUtterance(text);\n      utterance.lang = t.speechLang;"
)

# Update body of /ask
code = code.replace(
    "body: JSON.stringify({ question, history: recentHistory })",
    "body: JSON.stringify({ question, history: recentHistory, language: language })"
)

new_return = """  return (
    <div data-contrast={highContrast ? 'high' : 'normal'} style={{ fontSize: `${fontSize}px`, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="tricolor"><span style={{background:'#E2962B'}}></span><span style={{background:'#FBF7EC'}}></span><span style={{background:'#4F6B54'}}></span></div>
      <header>
        <div className="brand">
          <img className="brand-mark" src={logo} alt="SewaSaathi logo" />
          <div className="brand-name">SewaSaathi<small>सेवा साथी · ਸੇਵਾ ਸਾਥੀ</small></div>
        </div>
        <div className="header-tools">
          <Link to="/" className="tool-btn" style={{ textDecoration: 'none' }}>{t.home}</Link>
          <button className="tool-btn" onClick={decreaseFontSize} aria-label="Decrease font size">A-</button>
          <button className="tool-btn" onClick={increaseFontSize} aria-label="Increase font size">A+</button>
          <button className={`tool-btn ${highContrast ? 'active' : ''}`} onClick={() => setHighContrast(!highContrast)}>
            {highContrast ? '☀️ Light' : `🌗 ${t.contrast}`}
          </button>
          <select className="lang-select" value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="hi">हिंदी</option>
            <option value="pa">ਪੰਜਾਬੀ</option>
          </select>
        </div>
      </header>

      <main>
        <div style={{textAlign:'center', padding: '25px 0 35px', animation: 'fadeUp 0.3s ease'}}>
          <img src={logo} alt="SewaSaathi logo" style={{width:'88px', height:'86px', objectFit:'contain', marginBottom:'10px'}} />
          <div style={{fontFamily:'"Fraunces",serif', fontSize:'1.3rem', fontWeight:'600', color:'var(--indigo)'}}>{t.welcomeTitle}</div>
          <div style={{color:'var(--ink-soft)', fontSize:'0.92rem', marginTop:'2px'}}>सेवा साथी · ਸੇਵਾ ਸਾਥੀ</div>
        </div>
        
        {messages.map(msg => (
          <div key={msg.id} className={`msg-row ${msg.sender}`}>
            {msg.sender === 'bot' && (
              <div className="bot-avatar">
                <svg viewBox="0 0 24 24" fill="none" style={{width:'18px', height:'18px'}}><circle cx="12" cy="12" r="3" fill="#E2962B"/><g stroke="#E2962B" strokeWidth="1.6"><line x1="12" y1="3" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="21"/><line x1="3" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="21" y2="12"/></g></svg>
              </div>
            )}
            <div className={`bubble ${msg.sender}`}>
              {msg.sender === 'bot' ? (
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.id === 1 ? t.greeting : msg.text}</ReactMarkdown>
                </div>
              ) : (
                msg.text
              )}
              
              {msg.sender === 'bot' && (
                <div className="msg-meta">
                  <button className="read-aloud-btn" onClick={() => handleReadAloud(msg.id === 1 ? t.greeting : msg.text)} title={t.readAloud}>
                    🔊 {t.readAloud}
                  </button>
                  {msg.sources && msg.sources.length > 0 && msg.sources.map((src, i) => (
                    <span key={i} className="source-pill">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        <polyline points="9 12 11 14 15 10"></polyline>
                      </svg>
                      {t.source}: {src}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="msg-row bot">
            <div className="bot-avatar">
              <svg viewBox="0 0 24 24" fill="none" style={{width:'18px', height:'18px'}}><circle cx="12" cy="12" r="3" fill="#E2962B"/><g stroke="#E2962B" strokeWidth="1.6"><line x1="12" y1="3" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="21"/><line x1="3" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="21" y2="12"/></g></svg>
            </div>
            <div className="typing-bubble">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <div className="bottom-area">
        <div className="chips">
          {t.suggestedQuestions.map((q, i) => (
            <button key={i} className="chip" onClick={() => handleSend(q)}>
              {q}
            </button>
          ))}
        </div>
        
        <div className="input-row">
          <button 
            className={`mic-btn ${isListening ? 'listening' : ''}`} 
            onClick={startListening} 
            title="Use Microphone"
          >
            🎤
          </button>
          <input 
            type="text"
            className="text-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend(input)}
            placeholder={t.askPlaceholder}
          />
          <button className="send-btn" onClick={() => handleSend(input)}>
            {t.send}
          </button>
        </div>
      </div>
      <footer>
        {t.footerDisclaimer}
      </footer>
    </div>
  );
"""

code = code[:code.find("  return (")] + new_return + "\n}\n\nexport default ChatPage;\n"

with open('frontend/src/pages/ChatPage.jsx', 'w', encoding='utf-8') as f:
    f.write(code)
print('Patch successful.')

