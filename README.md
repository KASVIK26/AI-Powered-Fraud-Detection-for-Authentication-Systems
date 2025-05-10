# AI-Powered-Fraud-Detection-for-Authentication-Systems
A cutting-edge security solution that leverages machine learning and behavioral biometrics to detect and prevent fraudulent login attempts in real time. This system analyzes user interaction patterns—such as mouse movements, keystroke dynamics, and login behavior—to distinguish legitimate users from potential attackers.
# Key Features  
✅ Behavioral Biometrics – Tracks unique user interactions (typing speed, mouse velocity) to create a digital fingerprint.  
✅ Anomaly Detection – Uses Isolation Forest (AI/ML) to flag suspicious login attempts.  
✅ Real-Time Risk Scoring – Dynamically assesses threat levels and triggers 2FA when needed.  
✅ Redis-Powered Session Storage – Securely stores user behavior baselines for comparison.  
✅ JWT Authentication – Ensures secure, token-based user validation.  

# How It Works
### Signup Phase – Records baseline biometrics (typing/mouse patterns).  

### Login Phase – Compares live behavior against stored profiles.  

### Fraud Detection – AI model flags deviations (e.g., bot-like typing, unfamiliar mouse movements).  

### Response – Blocks suspicious logins or escalates to 2FA.  

# Tech Stack
🔹 Frontend: React, Plotly.js (for biometric visualization)  
🔹 Backend: Python (Flask), Redis (session storage)  
🔹 AI/ML: Scikit-learn (Isolation Forest for anomaly detection)  
🔹 Security: JWT, rate limiting, behavioral thresholds  
![Screenshot 2025-05-10 155817](https://github.com/user-attachments/assets/6a4bd30a-3574-486e-a279-b1e363c5e384)
