import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPageContent, sidebarConfig } from '@/content'

type ChatRole = 'user' | 'assistant'

type ChatMessage = { role: ChatRole; content: string }

export default function ChatPanel() {
  const navigate = useNavigate()
  const navigateRef = useRef(navigate)
  navigateRef.current = navigate

  useEffect(() => {
    const chatPanel = document.getElementById('chatPanel')
    const chatToggleBtn = document.getElementById('chatToggleBtn')
    const chatCloseBtn = document.getElementById('chatCloseBtn')
    const chatClearBtn = document.getElementById('chatClearBtn')
    const chatSettingsBtn = document.getElementById('chatSettingsBtn')
    const chatSetup = document.getElementById('chatSetup')
    const chatInterface = document.getElementById('chatInterface')
    const chatApiKeyInput = document.getElementById('chatApiKeyInput') as HTMLInputElement | null
    const chatSaveKeyBtn = document.getElementById('chatSaveKeyBtn')
    const chatMessages = document.getElementById('chatMessages')
    const chatTextarea = document.getElementById('chatTextarea') as HTMLTextAreaElement | null
    const chatSendBtn = document.getElementById('chatSendBtn') as HTMLButtonElement | null
    const chatBtnDot = document.getElementById('chatBtnDot')
    const mainEl = document.querySelector('main.main')

    if (
      !chatPanel ||
      !chatToggleBtn ||
      !chatCloseBtn ||
      !chatClearBtn ||
      !chatSettingsBtn ||
      !chatSetup ||
      !chatInterface ||
      !chatApiKeyInput ||
      !chatSaveKeyBtn ||
      !chatMessages ||
      !chatTextarea ||
      !chatSendBtn ||
      !chatBtnDot ||
      !mainEl
    ) {
      return
    }

    let chatOpen = false
    let chatHistory: ChatMessage[] = []
    let chatLoading = false
    let docsContext = ''

    const getChatApiKey = () => localStorage.getItem('openai-api-key') || ''
    const setChatApiKey = (k: string) => localStorage.setItem('openai-api-key', k.trim())

    const escHTML = (s: string) =>
      s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

    const toggleChat = (forceOpen?: boolean) => {
      chatOpen = forceOpen !== undefined ? forceOpen : !chatOpen
      chatPanel.classList.toggle('open', chatOpen)
      chatToggleBtn.classList.toggle('active', chatOpen)
      mainEl.classList.toggle('chat-open', chatOpen)
    }

    const showChatSetup = () => {
      chatSetup.style.display = ''
      chatInterface.style.display = 'none'
      chatApiKeyInput.value = ''
    }

    const showChatInterface = () => {
      chatSetup.style.display = 'none'
      chatInterface.style.display = 'flex'
      chatBtnDot.classList.add('show')
    }

    const buildDocsContext = async () => {
      if (docsContext) return
      const parts: string[] = []
      for (const section of sidebarConfig.sections) {
        parts.push(`\n## ${section.title}\n`)
        for (const page of section.pages) {
          const raw = getPageContent(page.file)
          parts.push(`### ${page.title}\n[FILE: pages/${page.file}]\n${raw}\n`)
        }
      }
      docsContext = parts.join('\n')
    }

    const parseSources = (content: string) => {
      const sources: string[] = []
      const clean = content
        .replace(/\[SOURCE:([^\]]+)\]/g, (_, file) => {
          sources.push(String(file).trim())
          return ''
        })
        .trim()
      return { clean, sources: Array.from(new Set(sources)) }
    }

    const fileToPageInfo = (file: string) => {
      const normalized = file.replace(/^pages\//, '')
      for (const section of sidebarConfig.sections) {
        for (const page of section.pages) {
          if (page.file === normalized) {
            return { section: section.title, page: page.title, slug: page.slug }
          }
        }
      }
      return { section: '', page: normalized, slug: '' }
    }

    const loadPage = (file: string) => {
      const info = fileToPageInfo(file)
      if (info.slug) navigateRef.current(info.slug)
    }

    const renderChatMarkdown = (text: string) => {
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/```[\s\S]*?```/g, m => `<pre><code>${m.slice(3, -3).replace(/^\w*\n/, '')}</code></pre>`)
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/_(.+?)_/g, '<em>$1</em>')
        .replace(/^[*\-] (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        .replace(/\n{2,}/g, '</p><p>')
        .replace(/^(?!<[uo]l|<pre|<li)(.+)$/gm, (m, p) => (p ? `<p>${p}</p>` : ''))
        .replace(/<p><\/p>/g, '')
        .replace(/\n/g, '<br>')
    }

    const appendMessage = (role: ChatRole, content: string) => {
      const welcomeEl = document.getElementById('chatWelcome')
      if (welcomeEl) welcomeEl.style.display = 'none'

      const wrap = document.createElement('div')
      wrap.className = `chat-msg ${role}`

      const bubble = document.createElement('div')
      bubble.className = 'chat-bubble'

      if (role === 'assistant') {
        const { clean, sources } = parseSources(content)
        bubble.innerHTML = renderChatMarkdown(clean)

        if (sources.length > 0) {
          const citationWrap = document.createElement('div')
          citationWrap.className = 'chat-citations'
          sources.forEach(file => {
            const info = fileToPageInfo(file)
            const btn = document.createElement('button')
            btn.className = 'chat-citation-btn'
            btn.title = `Go to: ${info.section} › ${info.page}`
            btn.innerHTML = `<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M1 9L9 1M9 1H3M9 1v6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg> ${escHTML(info.page)}`
            btn.addEventListener('click', () => {
              loadPage(file)
              if (window.innerWidth <= 768) toggleChat(false)
            })
            citationWrap.appendChild(btn)
          })
          wrap.appendChild(bubble)
          wrap.appendChild(citationWrap)
        } else {
          wrap.appendChild(bubble)
        }
      } else {
        bubble.textContent = content
        wrap.appendChild(bubble)
      }

      const time = document.createElement('div')
      time.className = 'chat-msg-time'
      time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      wrap.appendChild(time)

      chatMessages.appendChild(wrap)
      chatMessages.scrollTop = chatMessages.scrollHeight
      return bubble
    }

    const appendTyping = () => {
      const wrap = document.createElement('div')
      wrap.className = 'chat-msg assistant'
      wrap.id = 'chatTypingWrap'
      const bubble = document.createElement('div')
      bubble.className = 'chat-bubble chat-typing'
      bubble.innerHTML = '<span></span><span></span><span></span>'
      wrap.appendChild(bubble)
      chatMessages.appendChild(wrap)
      chatMessages.scrollTop = chatMessages.scrollHeight
    }

    const removeTyping = () => {
      const el = document.getElementById('chatTypingWrap')
      if (el) el.remove()
    }

    const appendError = (msg: string) => {
      const el = document.createElement('div')
      el.className = 'chat-error'
      el.textContent = msg
      chatMessages.appendChild(el)
      chatMessages.scrollTop = chatMessages.scrollHeight
    }

    const sendChatMessage = async (userText: string) => {
      if (!userText.trim() || chatLoading) return

      const apiKey = getChatApiKey()
      if (!apiKey) {
        showChatSetup()
        return
      }

      await buildDocsContext()

      chatLoading = true
      chatSendBtn.disabled = true
      chatTextarea.disabled = true

      appendMessage('user', userText)
      chatHistory.push({ role: 'user', content: userText })

      appendTyping()

      const systemPrompt = `You are a documentation assistant for the FF Master Ultra Edition robot.

Your ONLY knowledge source is the documentation provided below. You must:
1. Answer questions SOLELY based on the documentation content.
2. If the answer is not found in the documentation, respond: "I don't see that information in the documentation. Please check the relevant section or contact support."
3. Do NOT use general knowledge, training data, or make assumptions beyond what the docs state.
4. Keep answers concise and accurate. Use bullet points or numbered lists when helpful.
5. At the end of every answer, on a new line, list the source page(s) you drew from using EXACTLY this format (one per line, no extra text):
   [SOURCE:pages/filename.md]
   Each section in the documentation below has a [FILE: pages/filename.md] marker right after the heading — you MUST use that exact path in your [SOURCE:...] tags. Do NOT invent or guess filenames.

<documentation>
${docsContext}
</documentation>`

      try {
        const res = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: 'gpt-4o-mini',
            max_tokens: 1024,
            messages: [{ role: 'system', content: systemPrompt }, ...chatHistory],
          }),
        })

        removeTyping()

        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          const msg = err?.error?.message || `API error ${res.status}`
          if (res.status === 401) {
            appendError('Invalid API key. Click the settings icon to update it.')
            localStorage.removeItem('openai-api-key')
            chatBtnDot.classList.remove('show')
          } else {
            appendError(`Error: ${msg}`)
          }
          chatHistory.pop()
        } else {
          const data = await res.json()
          const reply = data.choices?.[0]?.message?.content || '(empty response)'
          chatHistory.push({ role: 'assistant', content: reply })
          appendMessage('assistant', reply)
        }
      } catch (e) {
        removeTyping()
        const err = e as Error
        appendError(`Network error: ${err.message}`)
        chatHistory.pop()
      }

      chatLoading = false
      chatSendBtn.disabled = false
      chatTextarea.disabled = false
      chatTextarea.focus()
    }

    const onToggle = () => toggleChat()
    const onClose = () => toggleChat(false)
    const onSaveKey = () => {
      const key = chatApiKeyInput.value.trim()
      if (!key.startsWith('sk-')) {
        chatApiKeyInput.style.borderColor = '#c0392b'
        chatApiKeyInput.placeholder = 'Key must start with sk-…'
        return
      }
      setChatApiKey(key)
      showChatInterface()
      buildDocsContext()
    }
    const onApiKeyEnter = (e: KeyboardEvent) => {
      if (e.key === 'Enter') onSaveKey()
      chatApiKeyInput.style.borderColor = ''
    }
    const onSettings = () => {
      showChatSetup()
      chatBtnDot.classList.remove('show')
    }
    const onTextareaInput = () => {
      chatTextarea.style.height = 'auto'
      chatTextarea.style.height = Math.min(chatTextarea.scrollHeight, 120) + 'px'
      chatSendBtn.disabled = !chatTextarea.value.trim()
    }
    const onTextareaKeydown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !(e as KeyboardEvent).shiftKey) {
        e.preventDefault()
        const val = chatTextarea.value.trim()
        if (val) {
          chatTextarea.value = ''
          chatTextarea.style.height = 'auto'
          chatSendBtn.disabled = true
          sendChatMessage(val)
        }
      }
    }
    const onSendClick = () => {
      const val = chatTextarea.value.trim()
      if (val) {
        chatTextarea.value = ''
        chatTextarea.style.height = 'auto'
        chatSendBtn.disabled = true
        sendChatMessage(val)
      }
    }
    const onMessagesClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('.chat-suggestion') as HTMLButtonElement | null
      if (target) sendChatMessage(target.textContent || '')
    }
    const onClear = () => {
      chatHistory = []
      chatMessages.innerHTML = ''
      const welcome = document.createElement('div')
      welcome.id = 'chatWelcome'
      welcome.className = 'chat-welcome'
      welcome.innerHTML = `
        <div class="chat-welcome-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path d="M28 2H4a2 2 0 00-2 2v16a2 2 0 002 2h4v6l6-6h14a2 2 0 002-2V4a2 2 0 00-2-2z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
          </svg>
        </div>
        <p>Ask anything about FF Master — I'll answer based on the documentation.</p>
        <div class="chat-suggestions">
          <button class="chat-suggestion">What's in the package?</button>
          <button class="chat-suggestion">How do I charge the robot?</button>
          <button class="chat-suggestion">What are the joint limits?</button>
          <button class="chat-suggestion">How do I perform an emergency stop?</button>
        </div>`
      chatMessages.appendChild(welcome)
    }

    chatToggleBtn.addEventListener('click', onToggle)
    chatCloseBtn.addEventListener('click', onClose)
    chatSaveKeyBtn.addEventListener('click', onSaveKey)
    chatApiKeyInput.addEventListener('keydown', onApiKeyEnter)
    chatSettingsBtn.addEventListener('click', onSettings)
    chatTextarea.addEventListener('input', onTextareaInput)
    chatTextarea.addEventListener('keydown', onTextareaKeydown)
    chatSendBtn.addEventListener('click', onSendClick)
    chatMessages.addEventListener('click', onMessagesClick)
    chatClearBtn.addEventListener('click', onClear)

    if (getChatApiKey()) {
      showChatInterface()
    } else {
      showChatSetup()
    }

    return () => {
      chatToggleBtn.removeEventListener('click', onToggle)
      chatCloseBtn.removeEventListener('click', onClose)
      chatSaveKeyBtn.removeEventListener('click', onSaveKey)
      chatApiKeyInput.removeEventListener('keydown', onApiKeyEnter)
      chatSettingsBtn.removeEventListener('click', onSettings)
      chatTextarea.removeEventListener('input', onTextareaInput)
      chatTextarea.removeEventListener('keydown', onTextareaKeydown)
      chatSendBtn.removeEventListener('click', onSendClick)
      chatMessages.removeEventListener('click', onMessagesClick)
      chatClearBtn.removeEventListener('click', onClear)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="chat-panel" id="chatPanel">
      <div className="chat-header">
        <div className="chat-header-title">
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
            <path
              d="M14 1H2a1 1 0 00-1 1v8a1 1 0 001 1h2v3l3-3h7a1 1 0 001-1V2a1 1 0 00-1-1z"
              stroke="currentColor"
              strokeWidth="1.3"
              strokeLinejoin="round"
            />
            <circle cx="5" cy="6" r="0.8" fill="currentColor" />
            <circle cx="8" cy="6" r="0.8" fill="currentColor" />
            <circle cx="11" cy="6" r="0.8" fill="currentColor" />
          </svg>
          Ask AI
        </div>
        <div className="chat-header-actions">
          <button className="icon-btn" id="chatClearBtn" title="Clear conversation" style={{ width: 28, height: 28 }}>
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <path
                d="M2 4h12M5 4V2h6v2M6 7v5M10 7v5M3 4l1 10h8l1-10"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
          <button className="icon-btn" id="chatSettingsBtn" title="API key settings" style={{ width: 28, height: 28 }}>
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="2" stroke="currentColor" strokeWidth="1.3" />
              <path
                d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41"
                stroke="currentColor"
                strokeWidth="1.3"
                strokeLinecap="round"
              />
            </svg>
          </button>
          <button className="icon-btn" id="chatCloseBtn" title="Close" style={{ width: 28, height: 28 }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </div>

      <div className="chat-setup" id="chatSetup">
        <div className="chat-setup-icon">
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
            <rect x="1" y="1" width="34" height="34" rx="10" stroke="currentColor" strokeWidth="1.5" />
            <path d="M10 14h16M10 18h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="26" cy="26" r="6" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeWidth="1.5" />
            <path d="M26 23v3.5l2 1.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h3>Connect your API key</h3>
        <p>Enter your OpenAI API key to enable AI-powered Q&amp;A grounded in this documentation.</p>
        <input
          type="password"
          className="chat-setup-input"
          id="chatApiKeyInput"
          placeholder="sk-…"
          autoComplete="off"
          spellCheck={false}
        />
        <button className="chat-setup-btn" id="chatSaveKeyBtn">
          Save &amp; Start
        </button>
        <p className="chat-setup-hint">
          Your key is saved only in this browser (<code>localStorage</code>) and never sent anywhere except OpenAI&apos;s API.
          <br />
          Get a key at{' '}
          <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">
            platform.openai.com
          </a>
        </p>
      </div>

      <div id="chatInterface" style={{ display: 'none', flex: 1, flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
        <div className="chat-messages" id="chatMessages">
          <div className="chat-welcome" id="chatWelcome">
            <div className="chat-welcome-icon">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path
                  d="M28 2H4a2 2 0 00-2 2v16a2 2 0 002 2h4v6l6-6h14a2 2 0 002-2V4a2 2 0 00-2-2z"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <p>Ask anything about FF Master — I&apos;ll answer based on the documentation.</p>
            <div className="chat-suggestions">
              <button className="chat-suggestion">What&apos;s in the package?</button>
              <button className="chat-suggestion">How do I charge the robot?</button>
              <button className="chat-suggestion">What are the joint limits?</button>
              <button className="chat-suggestion">How do I perform an emergency stop?</button>
            </div>
          </div>
        </div>

        <div className="chat-input-wrap">
          <div className="chat-input-row">
            <textarea
              className="chat-textarea"
              id="chatTextarea"
              placeholder="Ask a question…"
              rows={1}
              spellCheck={false}
            />
            <button className="chat-send-btn" id="chatSendBtn" disabled>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1 7h12M7 1l6 6-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
          <p className="chat-input-hint">Answers are based solely on the manual content</p>
        </div>
      </div>
    </div>
  )
}
