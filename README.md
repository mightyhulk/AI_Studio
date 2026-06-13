# Alexandria AI Studio — Multimodal Digital Curator

A premium multimodal AI application designed with the scholarly **Alexandria Editorial Design System** (serif typography, glassmorphism, clean layouts). It supports web-augmented text generation, document summarization, image creation/editing, speech synthesis, and music discovery.

---

## 📂 Project Structure

- **`backend/`**: FastAPI server handling LLM inference, API routing, and asset generation.
- **`frontend/`**: Vite + React single-page application built with custom CSS.

---

## 🛠️ Tech Stack & Models

| Component | Technology / Model |
| :--- | :--- |
| **Frontend** | React, Vite, React Router, Vanilla CSS (Alexandria Design System) |
| **Backend** | FastAPI, Uvicorn |
| **Research (Text Gen)** | `gemini-2.5-flash` + Tavily Search |
| **Summarizer** | `gemini-2.5-flash` (supports `.txt`, `.docx`, `.pdf`) |
| **Image Generation** | Hugging Face Inference API (`FLUX.1-schnell`) |
| **Image Editing** | Cloudflare AI (`flux-2-klein-4b`) |
| **Speech Generation** | `gemini-2.5-flash-preview-tts` (multi-speaker) |
| **Music Finder** | MusicBrainz API + YouTube search & embeds |

---

## 🚀 How to Run the Project

### 🔑 1. Setup Environment Variables
Ensure you have a `.env` file in the root directory containing the required API keys:
```env
gemini_api="YOUR_GEMINI_API_KEY"
gemini_api_2="YOUR_GEMINI_API_KEY"
hugging_face_api="YOUR_HUGGING_FACE_TOKEN"
cloudflare_account_id="YOUR_CF_ACCOUNT_ID"
cloudflare_api_key="YOUR_CF_API_KEY"
TAVILY_API_KEY="YOUR_TAVILY_API_KEY"
```

---

### 🐍 2. Run the Backend
1. Open a terminal in the root directory.
2. Activate the virtual environment:
   ```bash
   source studio_venv/bin/activate
   ```
3. Install dependencies if needed:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```
   *The backend will run on [http://localhost:8000](http://localhost:8000).*

---

### ⚛️ 3. Run the Frontend
1. Open a new terminal in the root directory.
2. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
3. Install dependencies:
   ```bash
   npm install
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend will run on [http://localhost:5173](http://localhost:5173).*