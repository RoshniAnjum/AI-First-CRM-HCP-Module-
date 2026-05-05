import React from 'react'
import { useSelector } from 'react-redux'
import '../styles/form.css'

const SENTIMENT_CONFIG = {
  positive: { label: 'Positive', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' },
  neutral:  { label: 'Neutral',  color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
  negative: { label: 'Negative', color: '#dc2626', bg: '#fff1f2', border: '#fecdd3' },
}

export default function InteractionForm() {
  const form = useSelector((state) => state.form)
  const {
    hcp_name, interaction_type, date, time,
    attendees, discussion_topic, sentiment,
    materials_shared, brochure_shared, follow_up, validation, summary,
  } = form

  const sentimentConfig = sentiment ? SENTIMENT_CONFIG[sentiment] : null

  const formatDate = (d) => {
    if (!d) return ''
    try {
      return new Date(d + 'T00:00:00').toLocaleDateString('en-US', {
        month: '2-digit', day: '2-digit', year: 'numeric',
      })
    } catch { return d }
  }

  const formatTime = (t) => {
    if (!t) return ''
    try {
      const [h, m] = t.split(':')
      const hour = parseInt(h)
      const ampm = hour >= 12 ? 'PM' : 'AM'
      const h12 = hour % 12 || 12
      return `${h12}:${m} ${ampm}`
    } catch { return t }
  }

  return (
    <div className="form-container">
      <div className="form-header">
        <h1 className="form-title">Log HCP Interaction</h1>
      </div>

      <div className="form-body">
        <div className="form-section-label">Interaction Details</div>

        {/* Row 1: HCP Name + Interaction Type */}
        <div className="form-row">
          <div className="form-field">
            <label className="field-label">HCP Name</label>
            <div className={`field-input ${!hcp_name ? 'field-input--placeholder' : ''}`}>
              {hcp_name || 'Search or select HCP...'}
            </div>
          </div>
          <div className="form-field">
            <label className="field-label">Interaction Type</label>
            <div className={`field-input field-input--select ${!interaction_type ? 'field-input--placeholder' : ''}`}>
              <span>{interaction_type || 'Meeting'}</span>
              <span className="select-caret">&#8964;</span>
            </div>
          </div>
        </div>

        {/* Row 2: Date + Time */}
        <div className="form-row">
          <div className="form-field">
            <label className="field-label">Date</label>
            <div className={`field-input field-input--icon ${!date ? 'field-input--placeholder' : ''}`}>
              <span>{date ? formatDate(date) : 'MM/DD/YYYY'}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="4" width="18" height="18" rx="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
            </div>
          </div>
          <div className="form-field">
            <label className="field-label">Time</label>
            <div className={`field-input field-input--icon ${!time ? 'field-input--placeholder' : ''}`}>
              <span>{time ? formatTime(time) : '--:-- --'}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
          </div>
        </div>

        {/* Attendees */}
        <div className="form-field">
          <label className="field-label">Attendees</label>
          <div className={`field-input ${!attendees ? 'field-input--placeholder' : ''}`}>
            {attendees || 'Enter names or search...'}
          </div>
        </div>

        {/* Topics Discussed */}
        <div className="form-field">
          <label className="field-label">Topics Discussed</label>
          <div className={`field-input field-input--textarea ${!discussion_topic ? 'field-input--placeholder' : ''}`}>
            {discussion_topic || 'Enter key discussion points...'}
          </div>
        </div>

        {/* Sentiment — only shown when set */}
        {sentiment && sentimentConfig && (
          <div className="form-field">
            <label className="field-label">Sentiment</label>
            <div className="field-input">
              <span
                className="sentiment-tag"
                style={{ color: sentimentConfig.color, backgroundColor: sentimentConfig.bg, borderColor: sentimentConfig.border }}
              >
                {sentimentConfig.label}
              </span>
            </div>
          </div>
        )}

        {/* Materials Shared */}
        <div className="form-section-label" style={{ marginTop: '6px' }}>
          Materials Shared / Samples Distributed
        </div>
        <div className="form-section-sublabel">Materials Shared</div>

        {materials_shared || brochure_shared ? (
          <div className="materials-list">
            <div className="material-item">
              {materials_shared || 'Brochure shared'}
            </div>
          </div>
        ) : (
          <div className="materials-empty">No materials added.</div>
        )}

        <div className="materials-footer">
          <button className="btn-search-add" disabled tabIndex={-1}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            Search/Add
          </button>
        </div>

        {/* Follow-up */}
        {follow_up && (
          <div className="followup-card">
            <div className="followup-label">Follow-up Suggestion</div>
            <p className="followup-text">{follow_up}</p>
          </div>
        )}

        {/* Summary */}
        {summary && (
          <div className="summary-card">
            <div className="summary-label">Interaction Summary</div>
            <p className="summary-text">{summary}</p>
          </div>
        )}

        {/* Validation */}
        {validation && (
          <div className={`validation-card ${validation.is_valid ? 'validation-card--valid' : 'validation-card--invalid'}`}>
            <div className="validation-label">
              {validation.is_valid ? 'Form Complete' : 'Incomplete Form'}
            </div>
            {!validation.is_valid && validation.missing_fields?.length > 0 && (
              <ul className="validation-list">
                {validation.missing_fields.map((f) => (
                  <li key={f}>{f.replace(/_/g, ' ')}</li>
                ))}
              </ul>
            )}
            {validation.message && (
              <p className="validation-message">{validation.message}</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
