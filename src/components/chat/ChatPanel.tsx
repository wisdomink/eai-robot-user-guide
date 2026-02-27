import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

type ChatRole = 'user' | 'assistant'

type ChatMessage = { role: ChatRole; content: string }

interface RAGSource {
  title: string
  section: string
  header_path: string
  url_path: string
  file_path: string
}

const CHAT_API_URL = import.meta.env.VITE_CHAT_API_URL || 'http://localhost:8000'

export default function ChatPanel() {
  const navigate = useNavigate()
  const navigateRef = useRef(navigate)
  navigateRef.current = navigate

  useEffect(() => {
    const chatPanel = document.getElementById('chatPanel')
    const chatToggleBtn = document.getElementById('chatToggleBtn')
    const chatCloseBtn = document.getElementById('chatCloseBtn')
    const chatClearBtn = document.getElementById('chatClearBtn')
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

    const escHTML = (s: string) =>
      s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

    const toggleChat = (forceOpen?: boolean) => {
      chatOpen = forceOpen !== undefined ? forceOpen : !chatOpen
      chatPanel.classList.toggle('open', chatOpen)
      chatToggleBtn.classList.toggle('active', chatOpen)
      mainEl.classList.toggle('chat-open', chatOpen)
    }

    chatBtnDot.classList.add('show')

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
        .replace(/^(?!<[uo]l|<pre|<li)(.+)$/gm, (_, p) => (p ? `<p>${p}</p>` : ''))
        .replace(/<p><\/p>/g, '')
        .replace(/\n/g, '<br>')
    }

    const appendUserMessage = (content: string) => {
      const welcomeEl = document.getElementById('chatWelcome')
      if (welcomeEl) welcomeEl.style.display = 'none'

      const wrap = document.createElement('div')
      wrap.className = 'chat-msg user'

      const bubble = document.createElement('div')
      bubble.className = 'chat-bubble'
      bubble.textContent = content
      wrap.appendChild(bubble)

      const time = document.createElement('div')
      time.className = 'chat-msg-time'
      time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      wrap.appendChild(time)

      chatMessages.appendChild(wrap)
      chatMessages.scrollTop = chatMessages.scrollHeight
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

    const addCitations = (wrap: HTMLDivElement, sources: RAGSource[]) => {
      if (sources.length === 0) return

      const citationWrap = document.createElement('div')
      citationWrap.className = 'chat-citations'
      sources.forEach(src => {
        const btn = document.createElement('button')
        btn.className = 'chat-citation-btn'
        btn.title = `${src.section} › ${src.title}`
        btn.innerHTML = `<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M1 9L9 1M9 1H3M9 1v6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg> ${escHTML(src.title)}`
        btn.addEventListener('click', () => {
          if (src.url_path) navigateRef.current(src.url_path)
          if (window.innerWidth <= 768) toggleChat(false)
        })
        citationWrap.appendChild(btn)
      })
      wrap.appendChild(citationWrap)
    }

    const addTimestamp = (wrap: HTMLDivElement) => {
      const time = document.createElement('div')
      time.className = 'chat-msg-time'
      time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      wrap.appendChild(time)
    }

    const sendChatMessage = async (userText: string) => {
      if (!userText.trim() || chatLoading) return

      chatLoading = true
      chatSendBtn.disabled = true
      chatTextarea.disabled = true

      appendUserMessage(userText)
      chatHistory.push({ role: 'user', content: userText })

      appendTyping()

      try {
        const res = await fetch(`${CHAT_API_URL}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: userText }),
        })

        if (!res.ok) {
          removeTyping()
          const err = await res.json().catch(() => ({}))
          appendError(`Error: ${err?.detail || `API error ${res.status}`}`)
          chatHistory.pop()
          chatLoading = false
          chatSendBtn.disabled = false
          chatTextarea.disabled = false
          chatTextarea.focus()
          return
        }

        const reader = res.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let fullContent = ''
        let sources: RAGSource[] = []
        let wrap: HTMLDivElement | null = null
        let bubble: HTMLDivElement | null = null

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const parts = buffer.split('\n\n')
          buffer = parts.pop() || ''

          for (const part of parts) {
            const match = part.match(/^data:\s*(.+)$/m)
            if (!match) continue

            try {
              const event = JSON.parse(match[1])

              if (event.type === 'token') {
                if (!bubble) {
                  removeTyping()
                  const welcomeEl = document.getElementById('chatWelcome')
                  if (welcomeEl) welcomeEl.style.display = 'none'

                  wrap = document.createElement('div')
                  wrap.className = 'chat-msg assistant'
                  bubble = document.createElement('div')
                  bubble.className = 'chat-bubble'
                  wrap.appendChild(bubble)
                  chatMessages.appendChild(wrap)
                }
                fullContent += event.content
                bubble.innerHTML = renderChatMarkdown(fullContent)
                chatMessages.scrollTop = chatMessages.scrollHeight
              } else if (event.type === 'sources') {
                sources = event.sources || []
              }
            } catch {
              /* ignore malformed SSE lines */
            }
          }
        }

        if (wrap) {
          addCitations(wrap, sources)
          addTimestamp(wrap)
          chatHistory.push({ role: 'assistant', content: fullContent })
        } else {
          removeTyping()
          appendError('No response received from server.')
          chatHistory.pop()
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
    chatTextarea.addEventListener('input', onTextareaInput)
    chatTextarea.addEventListener('keydown', onTextareaKeydown)
    chatSendBtn.addEventListener('click', onSendClick)
    chatMessages.addEventListener('click', onMessagesClick)
    chatClearBtn.addEventListener('click', onClear)

    return () => {
      chatToggleBtn.removeEventListener('click', onToggle)
      chatCloseBtn.removeEventListener('click', onClose)
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
          <button className="icon-btn" id="chatCloseBtn" title="Close" style={{ width: 28, height: 28 }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </div>

      <div id="chatInterface" style={{ display: 'flex', flex: 1, flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
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
