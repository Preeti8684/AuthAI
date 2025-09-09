# 🛡️ AuthAI — Face-Based Authentication System

**Secure login with Face Recognition**  
> A project demonstrating Login, Logout, Sign Up, Dashboard, Face Scan, Face Recognition, Duplicate checks (same name or same face), Replace Photo, and Delete Photo features.

---

## ✨ Features

- 🔑 **Login & Logout**  
- 📝 **Sign Up with Post-Signup Face Scan**  
- 👤 **Duplicate Checks**  
  - If the **face** already exists under another name → error shown.  
  - If the **username** already exists → error shown.  
- 🧑‍💻 **Dashboard** with quick navigation.  
- 📷 **Face Scan** for new users.  
- 🔄 **Replace/Delete Photo** any time.  
- 🖼️ Stored images remain in the `images/` folder until manually deleted.  
- ⚡ **Security-first** design suitable for banking-grade apps.  

---

## 🎬 Screenshots & Flow

> 📌 Replace `docs/media/...` with your actual screenshot paths.  
> Best practice → keep screenshots inside your repo under `docs/media/`.

### 1) Landing Page (Get Started)
![Landing](docs/media/landing.png)

---

### 2) Sign Up + Face Scan
| Sign Up | Face Scan | Duplicate Face Error | Duplicate Name Error |
|---------|-----------|-----------------------|----------------------|
| ![SignUp](docs/media/signup.png) | ![Scan](docs/media/face-scan.png) | ![DupFace](docs/media/dup-face.png) | ![DupName](docs/media/dup-name.png) |

---

### 3) Login + Face Recognize
| Login | Face Recognize |
|-------|----------------|
| ![Login](docs/media/login.png) | ![Recognize](docs/media/face-recognize.png) |

---

### 4) Dashboard
![Dashboard](docs/media/dashboard.png)

---

### 5) Replace & Delete Photo
| Replace | Delete |
|---------|--------|
| ![Replace](docs/media/replace.png) | ![Delete](docs/media/delete.png) |

---

### 6) Logout
![Logout](docs/media/logout.png)

---

## 🧱 Tech Stack

- **Frontend**: HTML, CSS, JavaScript  
- **Backend**: Flask (Python)  
- **Database**: MongoDB  
- **Face Recognition**: OpenCV / Deep Learning  
- **Storage**: Images saved in `images/` folder  

---

## 📂 Project Structure

