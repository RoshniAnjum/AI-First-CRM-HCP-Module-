import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { sendChatMessage, addUserMessage } from '../store/chatSlice'
import { v4 as uuidv4 } from 'uuid'
import ChatMessage from './ChatMessage'
import '../styles/chat.css'

const SESSION_ID = (() => {
  const key = 'crm_session_id'
  let id = localStorage.getItem(key)
  if (!id) {
    id = uuidv4()
    localStorage.setItem(key, id)
  }
  return id
})()

export default function ChatPanel() {
  const dispatch = useDispatch()
  const { messages, isLoading } = useSelector((state) => state.chat)
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSend = useCallback(() => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    setInput('')
    dispatch(addUserMessage(trimmed))
    dispatch(sendChatMessage({ message: trimmed, sessionId: SESSION_ID }))
    inputRef.current?.focus()
  }, [input, isLoading, dispatch])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-title">
          <span className="chat-header-icon">&#9654;</span>
          AI Assistant
        </div>
        <div className="chat-header-sub">Log Interaction details here via chat</div>
      </div>

      <div className="chat-messages" role="log" aria-live="polite">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {isLoading && (
          <div className="message message--assistant">
            <div className="message-bubble message-bubble--assistant">
              <div className="typing-indicator">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe Interaction..."
            rows={2}
            disabled={isLoading}
            aria-label="Describe interaction"
          />
          <button
            className={`log-btn ${isLoading || !input.trim() ? 'log-btn--disabled' : ''}`}
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            aria-label="Log interaction"
          >
            {isLoading ? <span className="send-spinner" /> : (
              <>
                <span className="log-btn-icon">&#9654;</span>
                Log
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
