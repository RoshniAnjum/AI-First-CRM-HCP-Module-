import React from 'react'
import InteractionForm from './components/InteractionForm'
import ChatPanel from './components/ChatPanel'
import './styles/app.css'

export default function App() {
  return (
    <div className="app-root">
      <main className="app-main">
        <section className="panel panel-left" aria-label="Interaction Form">
          <InteractionForm />
        </section>
        <section className="panel panel-right" aria-label="AI Assistant">
          <ChatPanel />
        </section>
      </main>
    </div>
  )
}
