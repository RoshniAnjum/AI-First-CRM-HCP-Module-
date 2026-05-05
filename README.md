# AI-First CRM HCP Log Interaction System

## Tech Stack
- **Frontend**: React + Redux Toolkit + Vite
- **Backend**: Python + FastAPI + LangGraph
- **LLM**: Groq API (gemma2-9b-it)
- **Database**: PostgreSQL
- **Styling**: Google Inter font + custom CSS

## Project Structure
```
crm-hcp-system/
├── frontend/          # React + Redux Toolkit
└── backend/           # FastAPI + LangGraph
```

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL running locally
- Groq API key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Fill in your credentials
python init_db.py         # Initialize database
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env      # Set VITE_API_URL
npm run dev
```

## Environment Variables

### Backend `.env`
```
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/crm_hcp
```

### Frontend `.env`
```
VITE_API_URL=http://localhost:8000
```
