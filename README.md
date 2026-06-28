# 📋 Report Card Management System

A full-featured student report card management system built with **FastAPI**, **PostgreSQL**, and **Jinja2** templates. Designed for schools and educational institutions to manage student records, marks, feedback, analytics, and lost & found reports.

---

## 🚀 Features

| Module | Description |
|---|---|
| 🔐 Authentication | Secure login & register with JWT cookies and bcrypt password hashing |
| 👨‍🎓 Student Management | Add, view, update, and delete students with dynamic subjects |
| 📝 Marks Management | Add, update, and remove subject-wise marks per student |
| 📊 Analytics Dashboard | ML-based score prediction and class-wise performance summary |
| 💬 Feedback | Teacher and student feedback with sentiment analysis |
| 🧳 Lost & Found | Report, resolve, and delete lost/found items |
| 📄 PDF Download | Download individual student marksheet as PDF |
| 🛡️ Rate Limiting | Per-route IP-based rate limiting to prevent abuse |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI (Python) |
| Database | PostgreSQL |
| DB Driver | asyncpg + databases |
| Auth | JWT (python-jose) + bcrypt |
| Templating | Jinja2 |
| Frontend | HTML5 + CSS3 |
| ML - Prediction | Rule-based predictor (scikit-learn ready) |
| ML - Sentiment | TextBlob |
| Rate Limiting | SlowAPI |
| PDF Export | WeasyPrint |
| Server | Uvicorn |

---

## 📁 Folder Structure

```
report_card_system/
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── students.py
│   │   ├── marks.py
│   │   ├── analytics.py
│   │   ├── feedback.py
│   │   └── lost_found.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── student.py
│   │   └── feedback.py
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── hashing.py
│   │   └── jwt_handler.py
│   │
│   └── ml/
│       ├── __init__.py
│       ├── predictor.py
│       └── feedback_analyzer.py
│
└── frontend/
    ├── static/
    │   └── css/
    │       └── style.css
    │
    └── templates/
        ├── base.html
        ├── login.html
        ├── register.html
        ├── dashboard.html
        ├── student_detail.html
        ├── analytics.html
        ├── feedback.html
        ├── lost_found.html
        └── marksheet_pdf.html
```

---

## 🐘 Database Tables

| Table | Purpose |
|---|---|
| `users` | Stores admin, teacher, student accounts |
| `students` | Stores student basic info |
| `subjects` | Master list of all subjects |
| `student_subjects` | Links students to subjects with marks |
| `feedback` | Stores teacher and student feedback |
| `lost_found` | Stores lost and found item reports |
| `student_results` | VIEW — auto-computes total, average, percentage |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/report-card-system.git
cd report-card-system
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root folder:
```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/report_card_system
JWT_SECRET_KEY=your_random_secret_key
DEBUG=True
```

### 5. Setup PostgreSQL
```bash
sudo systemctl start postgresql
sudo -u postgres psql
```
Then run all the SQL queries to create tables, views, and triggers.

### 6. Run the server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 7. Open in browser
```
http://localhost:8000
```

---

## 🔐 Role-based Access

| Feature | Admin | Teacher | Student |
|---|---|---|---|
| View Dashboard | ✅ | ✅ | ✅ |
| Add Student | ✅ | ✅ | ❌ |
| Update Student | ✅ | ✅ | ❌ |
| Delete Student | ✅ | ❌ | ❌ |
| Add/Remove Marks | ✅ | ✅ | ❌ |
| View Analytics | ✅ | ✅ | ✅ |
| Submit Feedback | ✅ | ✅ | ✅ |
| Delete Feedback | ✅ | ❌ | ❌ |
| Lost & Found Report | ✅ | ✅ | ✅ |
| Mark Item as Found | ✅ | ✅ | ❌ |
| Delete Lost & Found | ✅ | ❌ | ❌ |
| Download PDF | ✅ | ✅ | ✅ |

---

## 🛡️ Security Features

- Passwords hashed with **bcrypt**
- Auth via **JWT stored in HttpOnly cookies** — not accessible by JavaScript
- **Role-based access control** on every route
- **Rate limiting** per IP address on all routes
- **SameSite cookie** policy to prevent CSRF attacks

---

## 📊 ML Features

- **Score Prediction** — predicts future percentage based on current performance
- **Sentiment Analysis** — analyzes feedback text and categorizes as praise, concern, or improvement using TextBlob
- Both ML outputs are stored in the database for future model training

---

## 🚦 Rate Limits

| Route | Limit |
|---|---|
| POST /login | 5 / minute |
| POST /register | 3 / minute |
| GET dashboard, students | 30 / minute |
| POST add/update student | 20 / minute |
| POST add/update marks | 20 / minute |
| DELETE student, marks | 10 / minute |
| GET feedback, analytics | 20 / minute |
| POST feedback | 10 / minute |
| GET/POST lost & found | 20 / minute |

---

## 📄 PDF Marksheet

Each student's marksheet can be downloaded as a PDF directly from their detail page. It includes student info, subject-wise marks, total, average, percentage, and pass/fail result.

---

## 👥 Contributors

**Sayon Biswas**
- Github: [@SayonBiswas](https://github.com/SayonBiswas)

---

## 📃 License

MIT License