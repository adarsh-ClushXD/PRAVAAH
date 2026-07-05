# PRAVAAH 🌊

> **PRAVAAH** (meaning *Flow* or *Current* in Sanskrit) is a real-time Flood Risk Analytics and Decision-Support platform. It leverages **Explainable AI (XAI) powered by Gemma 4** to predict flood severity, quantify risk across 23 districts of West Bengal, and synthesize actionable emergency response plans for disaster management officers.

---

## 🚀 Key Features

*   **Explainable AI (XAI) Reasoning**: Real-time flood risk assessment powered by **Gemma 4** (supports both local Ollama deployment and cloud Google AI Studio API).
*   **Dynamic Interactive Map**: Color-coded risk map of West Bengal with live river gauge status and historical context overlays.
*   **Deterministic Mathematical Backup**: Employs a hybrid Python-AI pipeline calculating a composite risk index mathematically to ensure zero hallucination in critical statistics.
*   **Role-Based Access Control (RBAC)**: Secure access gating. Guests can browse telemetry, while authenticated District Disaster Management Officers (DDMOs) can run AI analyses and sync states.
*   **Real-time Alert Ticker**: Dynamic banner notifying operators of active Orange/Red alerts across West Bengal.

---

## 🛠️ Tech Stack

*   **Frontend**: React (Vite), Tailwind CSS, Leaflet Maps, Zustand (State Management), Lucide Icons.
*   **Backend**: FastAPI (Python), SQLAlchemy, SQLite, Pydantic, HTTPX.
*   **AI Engine**: Google AI REST API (Gemma 4 / Gemma 2) / Local Ollama (`gemma4:latest`).

---

## 📐 Architecture Flow

```mermaid
graph TD
    A[React Frontend] -->|API Requests| B[FastAPI Backend]
    B -->|Cache / Database| C[(SQLite + Cache)]
    B -->|Telemetry| D[Weather & River Gauge APIs]
    B -->|Strategy Pattern Factory| E[AI Provider Factory]
    E -->|AI_PROVIDER=ollama| F[Local Ollama (Gemma 4)]
    E -->|AI_PROVIDER=gemma_api| G[Google AI API (Gemma 4)]
```

---

## ⚙️ Configuration & Environment Setup

### Backend Config
Create a `.env` file in the `backend/` directory:
```ini
# Options: "ollama" | "gemma_api"
AI_PROVIDER=ollama

# Ollama Settings (Local Development)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:latest

# Google AI API Settings (Cloud Production)
GEMMA_API_KEY=your_google_ai_studio_api_key_here
GEMMA_API_MODEL=gemma-2-27b-it
```

### Frontend Config
Create a `.env` file in the `frontend/` directory:
```ini
# Production API Base URL (defaults to http://localhost:8000 if blank)
VITE_API_URL=http://localhost:8000
```

---

## 🏃 Running Locally

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   python run.py
   ```
   *The API will be live at `http://localhost:8000`*

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The dashboard will be live at `http://localhost:5173`*

---

## 🔒 Demo Credentials
To login as an Officer and access analysis features:
*   **Username**: `Admin`
*   **Password**: `Clush@232774`

---

## 🌎 Deployment

*   **Frontend**: Push your code to GitHub and import it directly into **[Vercel](https://vercel.com/)** or **[Netlify](https://netlify.com/)** (remember to set the `VITE_API_URL` environment variable).
*   **Backend**: Can be hosted easily on **[Render](https://render.com/)** or **[Railway](https://railway.app/)** with `AI_PROVIDER=gemma_api` and `GEMMA_API_KEY` injected.
