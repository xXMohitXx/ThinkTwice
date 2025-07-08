# ThinkTwice - Local Setup Guide

## Requirements
- Python 3.8+
- Node.js 14+ and Yarn (or npm)
- (Optional) MongoDB for persistent analytics/settings

## Backend Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **(Optional) For persistent analytics/settings:**
   - Install and run MongoDB locally.
   - Create a `.env` file in the `backend/` directory with:
     ```env
     MONGO_URL=mongodb://localhost:27017
     DB_NAME=thinktwice
     ```
   - If you skip this, the app will run in fully offline mode (analytics/settings reset on restart).

3. **Start the backend server:**
   ```bash
   uvicorn server:app --reload --port 8001
   ```

## Frontend Setup

1. **Install dependencies:**
   ```bash
   cd ../frontend
   yarn install
   # or: npm install
   ```

2. **Start the frontend:**
   ```bash
   yarn start
   # or: npm start
   ```

3. **Open your browser:**
   - Go to [http://localhost:3000](http://localhost:3000)

## Usage
- Type a message in the box. The app will analyze it in real time.
- Adjust the "Regret Threshold" slider to change sensitivity.
- If your message is risky, a warning will appear.
- All processing is local. No text is sent to the cloud.

## Notes
- If MongoDB is not running or not configured, the app will log a warning and use in-memory storage (all analytics/settings will reset on server restart).
- For GPU acceleration, ensure PyTorch is installed with CUDA support and a compatible GPU is available. 