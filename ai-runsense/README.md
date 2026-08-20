# AI RunSense

AI RunSense is an advanced biomechanical running analysis application that uses computer vision to track running form, analyze gait, and provide personalized AI coaching.

## 🚀 Features

- **Computer Vision Tracking:** Uses MediaPipe to extract 3D pose landmarks and analyze running biomechanics (cadence, vertical oscillation, symmetry).
- **Cinematic Web Interface:** A highly interactive, premium dashboard built with React and Vite, featuring dynamic glassmorphism and looping video backgrounds.
- **Smart Form Analysis:** Automatically detects form deviations, heel striking, overstriding, and identifies the "peak flaw zone" in your run.
- **Animated Voice Coach:** An integrated AI voice narrator and animated coach avatar that reads out your primary focus areas and gives you real-time feedback.
- **Gemini AI Integration:** Generates comprehensive coaching scripts and running style DNA analysis based on your biomechanical data.

## 🛠️ Technology Stack

- **Frontend:** React, TypeScript, Vite, Recharts, Lucide Icons, CSS3
- **Backend:** Python, FastAPI, OpenCV, Google MediaPipe, Google Gemini API
- **Data & Video Processing:** FFmpeg, OpenCV (libx264 faststart encoding for instant web streaming)

## 📦 Setup & Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ai-runsense
```

### 2. Backend Setup
Navigate to the backend directory and set up a Python virtual environment:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

**Environment Variables:**
Create a `.env` file in the `backend` directory and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_api_key_here
```

**Run the Backend Server:**
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
Navigate to the frontend directory:
```bash
cd ../frontend
npm install
```

**Run the Frontend Development Server:**
```bash
npm run dev
```

The application will be available at `http://localhost:5173/`.

## 🏃‍♂️ Usage

1. Open the web interface.
2. Log in or create a new user profile.
3. Upload a side-angle video of your running form.
4. Wait for the biomechanical pipeline to process and track your skeletal data.
5. Review your personalized dashboard, listen to the animated AI coach, and replay your critical breakdown zones.

## 📝 License
MIT License
