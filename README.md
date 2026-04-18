# 🚨 Scamurai

**Real-time AI-powered Scam Call Detection & Prevention System**

---

## 🎯 Overview

Scamurai is a real-time system that analyzes phone call audio to detect potential scams **during the call itself**.
It combines multiple AI signals — linguistic patterns, impersonation cues, financial intent, and voice analysis — to generate a live risk score and trigger alerts.

---

## ⚡ Key Features

* 🎙️ **Real-time call analysis** (audio → transcript → signals)
* 🧠 **Multi-signal detection**:

  * Linguistic scam patterns
  * Impersonation detection
  * Financial risk detection (OTP / money requests)
  * Voice / deepfake indicators
* 📊 **Dynamic risk scoring dashboard**
* 🚨 **Live alerts for suspicious activity**
* 📄 **Evidence logging (transcript + signals + decision)**
* 📲 **Emergency alert capability (conceptual feature)**

---

## 🧩 System Architecture

```
Audio Input
   ↓
Transcription (Whisper)
   ↓
Signal Detection Modules
   ├── Linguistic Analysis
   ├── Impersonation Detection
   ├── Money Risk Detection
   ├── Voice Analysis
   ↓
Consensus Engine
   ↓
Risk Score + Alerts
   ↓
Frontend Dashboard
```

---

## 🚀 Demo Instructions

### 1️⃣ Clone Repository

```bash
git clone <your-repo-link>
cd Scamurai
```

---

### 2️⃣ Setup Environment

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

---

### 3️⃣ Run Backend

```bash
python3 -m uvicorn app.server:app --reload
```

Backend runs on:

```
http://127.0.0.1:8000
```

---

### 4️⃣ Run Frontend

```bash
python3 -m http.server 5500
```

Open in browser:

```
http://localhost:5500
```

---

### 5️⃣ Start Demo

* Open the frontend dashboard
* Backend auto-starts call simulation
* Watch:

  * Transcript generation
  * Risk score updates
  * Alerts appearing in real-time

---

## 🧪 Demo Scenario

The demo simulates a scam call involving:

* Urgent request for money
* Impersonation behavior
* Financial manipulation

The system processes this audio and dynamically updates risk levels.

---


## 👥 Team

*git out of my way

---

## 📌 Note

This is a hackathon prototype demonstrating real-time scam detection capabilities using simulated call audio.

---
