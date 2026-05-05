import React from 'react'
import '../styles/chat.css'

const TOOL_LABELS = {
  LogInteractionTool:      'Interaction Logged',
  MergeInteractionTool:    'Details Merged',
  SummarizeInteractionTool:'Summary Generated',
  EditInteractionTool:     'Form Updated',
  ClearFormTool:           'Form Cleared',
  SuggestFollowUpTool:     'Follow-up Generated',
  ValidateInteractionTool: 'Validation Complete',
}

export default function ChatMessage({ message }) {
  const { role, content, tool_called, isError, timestamp } = message
  const isUser = role === 'user'

  const renderContent = (text) =>
    text.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {i > 0 && <br />}
        {line}
      </React.Fragment>
    ))

  const timeStr = timestamp
    ? new Date(timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    : ''

  return (
    <div className={`message ${isUser ? 'message--user' : 'message--assistant'}`}>
      <div className="message-content">
        {!isUser && tool_called && TOOL_LABELS[tool_called] && (
          <div className="message-tool-label">{TOOL_LABELS[tool_called]}</div>
        )}
        <div className={`message-bubble ${isUser ? 'message-bubble--user' : 'message-bubble--assistant'} ${isError ? 'message-bubble--error' : ''}`}>
          {renderContent(content)}
        </div>
        <div className={`message-time ${isUser ? 'message-time--right' : ''}`}>
          {timeStr}
        </div>
      </div>
    </div>
  )
}
