# 🛑 ThinkTwice – Real-Time “Regret-Before-You-Send” NLP Engine

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

## Overview

**ThinkTwice** is a cross-platform app that helps you avoid sending harmful, offensive, or regrettable text in real time. It monitors your messages just before you send them and computes a “Regret Score” using local NLP models. If the score exceeds your chosen threshold, a subtle “⚠️ Think Twice” warning appears—helping you pause before you post.

- **All processing is local and private** (no cloud, no data leaks)
- **Works offline**
- **Minimal, modern UI**
- **Customizable regret threshold**
- **Great for parents, teens, professionals, and schools**

---

## ✨ Features
- Real-time text evaluation (toxicity, threat, insult, etc.)
- Lightweight Transformer model (Detoxify, ONNX/PyTorch)
- Cross-platform: Windows, macOS, Linux (web/desktop), mobile coming soon
- Optional GPU acceleration
- Local-only processing (privacy-first)
- Minimal UI: message box, regret threshold slider, warning overlay
- Dark mode toggle 🌙
- Analytics dashboard (local or persistent with MongoDB)

---

## ⚙️ How It Works
- **Type your message** in the box.
- The app analyzes your text in real time using a local Detoxify NLP model.
- If the “Regret Score” exceeds your threshold, a warning appears.
- All analysis is done **on your device**—no text ever leaves your computer.
- Adjust the threshold to match your communication style.

---

## 🚀 Quickstart

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

#### (Optional) Persistent Analytics/Settings
- Install and run MongoDB locally.
- Create a `.env` file in `backend/`:
  ```env
  MONGO_URL=mongodb://localhost:27017
  DB_NAME=thinktwice
  ```
- If you skip this, the app runs in fully offline mode (analytics/settings reset on restart).

**Start the backend:**
```bash
uvicorn server:app --reload --port 8001
```

### 2. Frontend Setup

```bash
cd frontend
npm install   # or yarn install
npm start     # or yarn start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🖥️ Usage
- Type a message in the box.
- Adjust the “Regret Threshold” slider.
- If your message is risky, a warning will appear.
- Toggle dark mode in settings.
- All processing is local and private.

---

## 🛠️ Technologies Used
- **Frontend:** React, Tailwind CSS, Heroicons
- **Backend:** FastAPI, Detoxify (PyTorch), Uvicorn
- **Optional:** MongoDB (for persistent analytics/settings)

---

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a pull request

---

## 📄 License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

---

## 📬 Contact & Links
- Project by [Your Name or Team]
- [GitHub Repo](https://github.com/yourusername/thinktwice)
- [Issue Tracker](https://github.com/yourusername/thinktwice/issues)

---

> _ThinkTwice – Helping you communicate better, one message at a time._
