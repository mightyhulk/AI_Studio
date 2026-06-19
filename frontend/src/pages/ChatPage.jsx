import { useState, useRef, useEffect } from 'react';
import { sendPrompt, getFileUrl } from '../api';
import './ChatPage.css';

const INTENT_CONFIG = {
  text_gen: {
    label: 'Research',
    icon: '📚',
    placeholder: 'Ask any question — I will search and synthesize an answer…',
    description: 'Web-augmented text generation',
    supportsFile: false,
  },
  summarize: {
    label: 'Summarize',
    icon: '✍',
    placeholder: 'Paste text or upload a document to summarize…',
    description: 'Summarize text, PDF, DOCX, or TXT files',
    supportsFile: true,
    fileTypes: '.pdf,.docx,.txt',
  },
  image_create: {
    label: 'Create Image',
    icon: '🎨',
    placeholder: 'Describe the image you want to generate…',
    description: 'AI image generation from text prompts',
    supportsFile: false,
  },
  image_editor: {
    label: 'Edit Image',
    icon: '✏️',
    placeholder: 'Describe the edits you want to apply…',
    description: 'Transform or generate images with AI',
    supportsFile: true,
    fileTypes: 'image/*',
  },
  speech_generation: {
    label: 'Speech',
    icon: '🔊',
    placeholder: 'Enter text or dialogue to convert to speech…',
    description: 'Multi-speaker text-to-speech synthesis',
    supportsFile: false,
  },
  music_generation: {
    label: 'Music',
    icon: '🎵',
    placeholder: 'Enter a song name, lyrics, or artist to find music…',
    description: 'Find and embed music from YouTube',
    supportsFile: false,
  },
};

const QUICK_ACTIONS = [
  { intent: 'text_gen', prompt: 'Explain quantum computing in simple terms' },
  { intent: 'summarize', prompt: 'Summarize the key principles of Stoic philosophy' },
  { intent: 'image_create', prompt: 'A serene Japanese garden at sunset, watercolor style' },
  { intent: 'music_generation', prompt: 'Clair de Lune by Debussy' },
];

export default function ChatPage({ user, onLogout }) {
  const loadInitialSessions = () => {
    if (!user?.email) return [];
    const normalizedEmail = user.email.toLowerCase();
    try {
      const savedSessions = localStorage.getItem(`alexandria_sessions_${normalizedEmail}`);
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

      if (savedSessions) {
        return JSON.parse(savedSessions)
          .filter((session) => new Date(session.updatedAt) >= thirtyDaysAgo)
          .map((session) => ({
            ...session,
            updatedAt: new Date(session.updatedAt),
            messages: session.messages.map((msg) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            })),
          }));
      }

      // Legacy fallback
      const savedChat = localStorage.getItem(`alexandria_chat_${normalizedEmail}`);
      if (savedChat) {
        const parsed = JSON.parse(savedChat);
        const filteredMessages = parsed
          .filter((msg) => new Date(msg.timestamp) >= thirtyDaysAgo)
          .map((msg) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          }));
        if (filteredMessages.length > 0) {
          const userMsg = filteredMessages.find((m) => m.role === 'user');
          const title = userMsg ? userMsg.content.substring(0, 25) + '...' : 'Legacy Session';
          return [
            {
              id: Date.now(),
              title,
              updatedAt: new Date(),
              messages: filteredMessages.filter((m) => m.role !== 'divider'),
            },
          ];
        }
      }
      return [];
    } catch (e) {
      console.error('Failed to load chat history', e);
      return [];
    }
  };

  const [activeIntent, setActiveIntent] = useState('text_gen');
  const [prompt, setPrompt] = useState('');
  const [file, setFile] = useState(null);
  
  const [sessions, setSessions] = useState(loadInitialSessions);
  const [currentSessionId, setCurrentSessionId] = useState(() => {
    const initialSessions = loadInitialSessions();
    return initialSessions.length > 0 ? initialSessions[0].id : null;
  });

  const messages = sessions.find((s) => s.id === currentSessionId)?.messages || [];

  // Save sessions to local storage whenever they change
  useEffect(() => {
    if (user?.email) {
      const normalizedEmail = user.email.toLowerCase();
      localStorage.setItem(`alexandria_sessions_${normalizedEmail}`, JSON.stringify(sessions));
    }
  }, [sessions, user?.email]);

  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  const config = INTENT_CONFIG[activeIntent];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 160) + 'px';
    }
  }, [prompt]);

  const handleSend = async (customPrompt, customIntent) => {
    const intentToUse = customIntent || activeIntent;
    const promptToUse = customPrompt || prompt.trim();

    if (!promptToUse && !file) return;

    // Validate that Edit Image has a file attached
    if (intentToUse === 'image_editor' && !file) {
      const errorMessage = {
        id: Date.now(),
        role: 'error',
        content: 'Please attach an image file before using the Edit Image feature.',
        timestamp: new Date(),
      };
      let targetSessionId = currentSessionId;
      if (!targetSessionId) {
        targetSessionId = Date.now();
        setCurrentSessionId(targetSessionId);
        setSessions((prev) => [
          { id: targetSessionId, title: promptToUse.substring(0, 25) + '...', updatedAt: new Date(), activeIntent: intentToUse, messages: [{ id: Date.now(), role: 'user', intent: intentToUse, content: promptToUse, fileName: null, timestamp: new Date() }, errorMessage] },
          ...prev,
        ]);
      } else {
        setSessions((prev) => prev.map((s) => s.id === targetSessionId ? { ...s, messages: [...s.messages, { id: Date.now(), role: 'user', intent: intentToUse, content: promptToUse, fileName: null, timestamp: new Date() }, errorMessage], updatedAt: new Date() } : s));
      }
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: 'user',
      intent: intentToUse,
      content: promptToUse,
      fileName: file?.name || null,
      timestamp: new Date(),
    };

    let targetSessionId = currentSessionId;
    if (!targetSessionId) {
      targetSessionId = Date.now();
      setCurrentSessionId(targetSessionId);
      setSessions((prev) => [
        {
          id: targetSessionId,
          title: promptToUse.substring(0, 25) + '...',
          updatedAt: new Date(),
          activeIntent: intentToUse,
          messages: [userMessage],
        },
        ...prev,
      ]);
    } else {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === targetSessionId
            ? { ...s, messages: [...s.messages, userMessage], updatedAt: new Date() }
            : s
        )
      );
    }

    setPrompt('');
    setIsLoading(true);

    try {
      const response = await sendPrompt(intentToUse, promptToUse, file);

      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        intent: response.intent,
        content: response.result,
        timestamp: new Date(),
      };

      setSessions((prev) =>
        prev.map((s) =>
          s.id === targetSessionId
            ? { ...s, messages: [...s.messages, aiMessage], updatedAt: new Date() }
            : s
        )
      );
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        role: 'error',
        content: err.message || 'Something went wrong. Please try again.',
        timestamp: new Date(),
      };
      setSessions((prev) =>
        prev.map((s) =>
          s.id === targetSessionId
            ? { ...s, messages: [...s.messages, errorMessage], updatedAt: new Date() }
            : s
        )
      );
    } finally {
      setIsLoading(false);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setPrompt('');
    setFile(null);
    textareaRef.current?.focus();
  };

  const handleDeleteSession = (sessionId) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null);
      setPrompt('');
      setFile(null);
    }
  };

  const handleDownloadImage = async (fileUrl, fileName) => {
    try {
      const response = await fetch(fileUrl);
      if (!response.ok) throw new Error('Network response was not ok');
      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      // Extract just the filename if it's a path
      const name = fileName.split('/').pop() || 'downloaded_image.png';
      link.download = name;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(objectUrl);
      document.body.removeChild(link);
    } catch (err) {
      console.error('Failed to download image:', err);
      window.open(fileUrl, '_blank'); // Fallback
    }
  };

  const renderMessageContent = (msg) => {
    if (msg.role === 'divider') {
      return null;
    }

    if (msg.role === 'error') {
      return <div className="message-error-text">{msg.content}</div>;
    }

    if (msg.role === 'user') {
      return (
        <div className="message-user-text">
          {msg.fileName && (
            <div className="message-file-badge">
              <span className="file-icon">📎</span>
              {msg.fileName}
            </div>
          )}
          <p>{msg.content}</p>
        </div>
      );
    }

    // Assistant message — render based on intent
    const { intent, content } = msg;

    if (typeof content === 'string') {
      const renderLineWithHighlights = (line) => {
        if (!line) return <br />;
        const parts = line.split(/(\*\*.*?\*\*)/g);
        return parts.map((part, index) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            const text = part.slice(2, -2);
            return <strong key={index}>{text}</strong>;
          }
          return <span key={index}>{part}</span>;
        });
      };

      return (
        <div className="message-ai-text">
          {content.split('\n').map((line, i) => (
            <p key={i}>{renderLineWithHighlights(line)}</p>
          ))}
        </div>
      );
    }

    // Image result
    if (intent === 'image_create' || intent === 'image_editor') {
      return (
        <div className="message-image-result">
          {content.file && (
            <div className="generated-image-container">
              <img
                src={getFileUrl(content.file)}
                alt={content.prompt || 'Generated image'}
                className="generated-image"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
              <div className="image-fallback" style={{ display: 'none' }}>
                <span>🖼️</span>
                <p>Image generated successfully</p>
                <p className="image-path">{content.file}</p>
              </div>
            </div>
          )}
          <div className="image-meta">
            {content.prompt && <p className="meta-prompt">"{content.prompt}"</p>}
            {content.width && content.height && (
              <span className="meta-dims">{content.width}×{content.height}</span>
            )}
            {content.mode && (
              <span className="badge badge-primary">{content.mode}</span>
            )}
            {content.file && (
              <button
                className="btn btn-tertiary image-download-btn"
                onClick={() => handleDownloadImage(getFileUrl(content.file), content.file)}
                title="Download Image"
              >
                <span className="download-icon" style={{ marginRight: '6px' }}>⬇</span>
                Download
              </button>
            )}
          </div>
        </div>
      );
    }

    // Speech result
    if (intent === 'speech_generation') {
      return (
        <div className="message-speech-result">
          {content.file && (
            <audio controls src={getFileUrl(content.file)} className="speech-audio">
              Your browser does not support the audio element.
            </audio>
          )}
          {content.speakers && (
            <div className="speech-speakers">
              <span className="label">Speakers:</span>
              {content.speakers.map((s, i) => (
                <span key={i} className="badge badge-gold">
                  {s.name} ({s.gender})
                </span>
              ))}
            </div>
          )}
          {content.prompt && (
            <details className="speech-script">
              <summary>View generated script</summary>
              <div className="script-content">
                {content.prompt.split('\n').map((line, i) => (
                  <p key={i}>{line || <br />}</p>
                ))}
              </div>
            </details>
          )}
        </div>
      );
    }

    // Music result
    if (intent === 'music_generation') {
      return (
        <div className="message-music-result">
          <div className="music-card">
            <div className="music-info">
              <h4 className="music-title">{content.title || 'Unknown Track'}</h4>
              <p className="music-artist">{content.artist || 'Unknown Artist'}</p>
            </div>
            {content.youtube_embed ? (
              <div className="music-embed">
                <iframe
                  src={content.youtube_embed}
                  title={content.title || 'Music'}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="youtube-iframe"
                />
              </div>
            ) : (
              <div className="music-no-embed">
                <span className="music-no-embed-icon">🎵</span>
                <p>Embed not available — listen directly on YouTube</p>
              </div>
            )}
            {content.youtube_search && (
              <a
                href={content.youtube_search}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary music-link"
              >
                ▶ Open on YouTube
              </a>
            )}
          </div>
        </div>
      );
    }

    // Summarize or text_gen with object result
    if (typeof content === 'object') {
      return (
        <div className="message-ai-text">
          <pre className="message-json">{JSON.stringify(content, null, 2)}</pre>
        </div>
      );
    }

    return <div className="message-ai-text"><p>{String(content)}</p></div>;
  };

  return (
    <div className="chat-page">
      {/* Sidebar */}
      <aside className={`chat-sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <span className="brand-glyph">✦</span>
            <div className="brand-text">
              <h1 className="brand-name">Alexandria AI</h1>
              <span className="badge badge-gold">Premium Curator</span>
            </div>
          </div>
          <button
            className="btn-icon sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>

        {sidebarOpen && (
          <>
            <button
              className="btn btn-primary new-chat-btn"
              onClick={handleNewChat}
            >
              <span>+</span>
              New Inquiry
            </button>

            <nav className="sidebar-nav">
              <div className="nav-section">
                <span className="label nav-label">Capabilities</span>
                {Object.entries(INTENT_CONFIG).map(([key, cfg]) => (
                  <button
                    key={key}
                    className={`nav-item ${activeIntent === key ? 'active' : ''}`}
                    onClick={() => setActiveIntent(key)}
                  >
                    <span className="nav-icon">{cfg.icon}</span>
                    <span className="nav-text">{cfg.label}</span>
                  </button>
                ))}
              </div>

              {sessions.length > 0 && (
                <div className="nav-section">
                  <span className="label nav-label">Past Inquiries</span>
                  {sessions.map(session => (
                    <div
                      key={session.id}
                      className={`nav-item ${currentSessionId === session.id ? 'active' : ''}`}
                      onClick={() => {
                        setCurrentSessionId(session.id);
                        // Restore the session's capability
                        if (session.activeIntent && INTENT_CONFIG[session.activeIntent]) {
                          setActiveIntent(session.activeIntent);
                        }
                      }}
                      style={{ paddingRight: '8px' }}
                    >
                      <span className="nav-icon">{session.activeIntent && INTENT_CONFIG[session.activeIntent] ? INTENT_CONFIG[session.activeIntent].icon : '💬'}</span>
                      <span className="nav-text" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                        {session.title || 'Inquiry'}
                      </span>
                      <button
                        className="btn-icon delete-session-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSession(session.id);
                        }}
                        title="Delete Inquiry"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </nav>

            <div className="sidebar-footer">
              <div className="sidebar-user">
                <div className="user-avatar">
                  {(user?.name || 'S').charAt(0).toUpperCase()}
                </div>
                <div className="user-info">
                  <span className="user-name">{user?.name || 'Scholar'}</span>
                  <span className="user-plan">{user?.plan || 'Premium'} Account</span>
                </div>
              </div>
              <button className="btn btn-tertiary logout-btn" onClick={onLogout}>
                Sign Out
              </button>
            </div>
          </>
        )}
      </aside>

      {/* Main content */}
      <main className="chat-main">
        {/* Messages area */}
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-welcome animate-fade-in-up">
              <div className="welcome-header">
                <div className="welcome-badge">
                  <span className="welcome-glyph">✦</span>
                </div>
                <h2 className="welcome-title">Welcome to Alexandria</h2>
                <p className="welcome-subtitle">
                  I am your Digital Curator. How might I assist you in exploring dense knowledge
                  or crafting refined narratives today?
                </p>
              </div>

              {/* Quick action chips */}
              <div className="quick-actions">
                <span className="label">Try an inquiry</span>
                <div className="quick-action-grid">
                  {QUICK_ACTIONS.map((qa, i) => (
                    <button
                      key={i}
                      className="quick-action-card card card-elevated"
                      onClick={() => {
                        setActiveIntent(qa.intent);
                        handleSend(qa.prompt, qa.intent);
                      }}
                    >
                      <span className="qa-icon">{INTENT_CONFIG[qa.intent].icon}</span>
                      <span className="qa-label">{INTENT_CONFIG[qa.intent].label}</span>
                      <p className="qa-prompt">{qa.prompt}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Intent pills */}
              <div className="intent-pills">
                {Object.entries(INTENT_CONFIG).map(([key, cfg]) => (
                  <button
                    key={key}
                    className={`intent-pill ${activeIntent === key ? 'active' : ''}`}
                    onClick={() => setActiveIntent(key)}
                  >
                    <span>{cfg.icon}</span>
                    <span>{cfg.label}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message message-${msg.role} animate-fade-in`}
                >
                  <div className="message-avatar">
                    {msg.role === 'user' ? (
                      <div className="avatar-user">
                        {(user?.name || 'S').charAt(0).toUpperCase()}
                      </div>
                    ) : msg.role === 'error' ? (
                      <div className="avatar-error">⚠</div>
                    ) : (
                      <div className="avatar-ai">✦</div>
                    )}
                  </div>
                  <div className="message-body">
                    <div className="message-header">
                      <span className="message-sender">
                        {msg.role === 'user' ? (user?.name || 'You') : msg.role === 'error' ? 'Error' : 'Alexandria AI'}
                      </span>
                      {msg.intent && (
                        <span className="badge badge-primary message-intent">
                          {INTENT_CONFIG[msg.intent]?.icon} {INTENT_CONFIG[msg.intent]?.label}
                        </span>
                      )}
                      <span className="message-time">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div className="message-content">
                      {renderMessageContent(msg)}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="message message-assistant animate-fade-in">
                  <div className="message-avatar">
                    <div className="avatar-ai">✦</div>
                  </div>
                  <div className="message-body">
                    <div className="message-header">
                      <span className="message-sender">Alexandria AI</span>
                    </div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span className="typing-dot"></span>
                        <span className="typing-dot"></span>
                        <span className="typing-dot"></span>
                        <span className="typing-text">Curating a response…</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="chat-input-area">
          <div className="chat-input-container glass">
            {/* Active mode indicator */}
            <div className="input-mode-bar">
              <span className="input-mode-icon">{config.icon}</span>
              <span className="input-mode-label">{config.label}</span>
              <span className="input-mode-description">{config.description}</span>
            </div>

            {/* File attachment preview */}
            {file && (
              <div className="file-preview">
                <span className="file-icon">📎</span>
                <span className="file-name">{file.name}</span>
                <button
                  className="file-remove"
                  onClick={() => {
                    setFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = '';
                  }}
                >
                  ✕
                </button>
              </div>
            )}

            <div className="input-row">
              {/* File upload button */}
              {config.supportsFile && (
                <>
                  <button
                    className="btn-icon attach-btn"
                    onClick={() => fileInputRef.current?.click()}
                    title="Attach file"
                  >
                    📎
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={config.fileTypes}
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                </>
              )}

              <textarea
                ref={textareaRef}
                className="chat-textarea"
                placeholder={config.placeholder}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={isLoading}
              />

              <button
                className="btn btn-primary send-btn"
                onClick={() => handleSend()}
                disabled={isLoading || (!prompt.trim() && !file)}
                title="Send"
              >
                {isLoading ? (
                  <span className="spinner" style={{ width: 18, height: 18 }}></span>
                ) : (
                  '→'
                )}
              </button>
            </div>
          </div>

          <p className="chat-disclaimer">
            Alexandria AI may occasionally misinterpret nuance. Verify critical archival or scholarly claims.
          </p>
        </div>
      </main>
    </div>
  );
}
