<div align="center">

# 🛡️ AJAXX Data Scrubber
### Take Control of Your Digital Footprint

Automated privacy protection platform that scans, tracks & removes your personal data from online data broker sites — powered by secure APIs, automation workflows and modern web technologies.

---

![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-REST%20Framework-green?style=flat-square&logo=django)

</div>

---

## 📌 Table of Contents
- [Overview](#-project-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Screenshots](#-screenshots)
- [Folder Structure](#-folder-structure)
- [Setup Guide](#-setup--getting-started)
- [Environment Variables](#-environment-variables)
- [Running Locally](#-running-the-project)

---

## 📘 Project Overview
AJAXX Data Scrubber empowers users to protect their personal data online by automating:
✅ Data scans  
✅ Removal requests  

Designed to help users comply with privacy laws like GDPR / CCPA.

---

## 🎯 Purpose of the Application
✔ Allow users to regain control over their exposed personal data  
✔ Automate scan + removal workflows  
✔ Provide compliance history + audit logs  
✔ Securely manage data with modern authentication & encryption

---

## 🚀 Features

### 🧑‍💻 User Features
| Feature | Description |
|--------|-------------|
| Login / Signup | Firebase Auth for secure access |
| Dashboard | View scans, results & progress |
| Scan Request | N8N automated workflow trigger |
| Scan Results | Fetch scan status + logs from Airtable |
| Subscription | Stripe (Basic / Silver / Gold) |
| Settings | Control retention, delete account |
| Compliance History | PDF export of logs for legal compliance |
| Help & Support | Contact form |

### 🛠 Admin Features
| Feature | Description |
|--------|-------------|
| Admin Dashboard | Manage users + scans |
| User Management | Ban, reset, delete accounts |
| Analytics | Real-time charts usage/subscription |
| Audit Logs Export | Legal documentation |

---

## 🧰 Tech Stack

| Layer | Technology |
|------|------------|
| Backend | Django, DRF |
| Frontend | React.js / Django Templates |
| Authentication | Firebase Auth |
| Database | PostgreSQL / MySQL / SQLite |
| Payments | Stripe |
| Automation Engine | N8N |
| Storage & Data Fetch | Airtable API |
| Logging / Compliance | Custom Export Services |

---

## 🏗 System Architecture

--
## 🗂 Folder Structure
project-root/
│── backend/
│ │── apps/
│ │── core/
│ │── settings.py
│── .env.example
│── requirements.txt
│── README.md

---

## ⚙️ Setup / Getting Started

### ✅ Prerequisites
- Python 3.14.0
- pip & virtualenv  
- Git  

---

### 🔧 Install Guide

```bash
# Clone repo
git clone https://github.com/yourusername/ajaxx-data-scrubber.git
cd ajaxx-data-scrubber

# Create venv
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
🔐 Environment Variables
Rename .env.example ➝ .env and fill in:


# Django
SECRET_KEY=YOUR_DJANGO_SECRET_KEY

# Email
EMAIL=example@gmail.com
EMAIL_PASSWORD=YOUR_EMAIL_APP_PASSWORD

# Database
DB_NAME=YOUR_DB_NAME
DB_USER=YOUR_DB_USER
DB_PASSWORD=YOUR_DB_PASSWORD

# Stripe
stripe_secret_key=YOUR_STRIPE_SECRET_KEY
stripe_publishable_key=YOUR_STRIPE_PUBLISHABLE_KEY
stripe_webhook_secret=YOUR_STRIPE_WEBHOOK_SECRET
▶ Running the Project

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
🔗 URL: http://127.0.0.1:8000/


🤝 Contributing

git checkout -b feature-name
git commit -m "Added new feature"
git push origin feature-name


