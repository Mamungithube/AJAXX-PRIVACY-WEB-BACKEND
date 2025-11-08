# AJAXX Data Scrubber

**AJAXX Data Scrubber** is a privacy-focused web application that empowers users to take control of their digital footprint by scanning, tracking, and requesting the removal of their personal data from online data brokers. The app uses automated workflows and secure APIs to streamline the process of managing privacy and complying with data regulations.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Purpose](#purpose-of-the-application)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview
AJAXX Data Scrubber is designed to give users a simple and secure way to manage their personal data online. It automates data scans, tracks scan results, and allows users to request removal of personal information from third-party data brokers.

---

## Purpose of the Application
The primary purpose of AJAXX Data Scrubber is to provide users with an easy and secure way to protect their personal information online. By automating the process of data scanning and removal, the app helps users regain control over their online presence and comply with digital privacy laws.

---

## Features

### User-Facing Pages
- **Login / Signup:** Firebase authentication for secure login and signup.  
- **Dashboard:** View scan status, results, and a summary of account activity.  
- **Scan Request:** Trigger data scans through a webhook integration (powered by N8N).  
- **Scan Results Page:** Displays the status and results of ongoing and completed scans from Airtable.  
- **Subscription Page:** Allows users to subscribe to Basic, Silver, or Gold plans via Stripe.  
- **Settings Page:** Update user preferences, manage data retention, or delete the account.  
- **Compliance History:** Download or request PDF logs of compliance history.  
- **Support/Contact:** Built-in help form for user inquiries.

### Admin Pages
- **Admin Dashboard:** View and manage all user accounts and scans, trigger exports, and control app settings.  
- **User Management:** Ban, reset, or delete user accounts.  
- **Analytics View:** Monitor scan usage, user activity, and subscription tiers with real-time charts.  
- **Audit Log Export:** Legal export options for compliance documentation.  

---

## Tech Stack
- **Backend:** Django, Django REST Framework (DRF)  
- **Authentication:** Firebase Authentication  
- **Database:** PostgreSQL
- **Payment Gateway:** Stripe  

---

## Installation

```bash
# Clone the repository
git clone [(https://github.com/Mamungithube/AJAXX-PRIVACY-WEB-BACKEND/)}

# Navigate to project folder
cd ajaxx-data-scrubber

# Create virtual environment
python -m venv env
source venv/bin/activate  # Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt


