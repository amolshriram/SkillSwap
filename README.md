# Skill Swap Platform (Peer-to-Peer Skill Exchange)

A full-stack web application where users **swap skills without money**. Built with **Django (Python)**, **SQLite**, **HTML/CSS**, and **JavaScript**.

## Features

- User registration, login, logout
- User profile (name, email) + manage skills
- Skills with proficiency levels: **Beginner / Intermediate / Advanced**
- Skill listings (browse/search users by offered skills)
- Skill swap requests: **Pending / Accepted / Rejected**
- Dashboard showing profile + incoming/outgoing requests
- Admin module via Django Admin

## Tech Stack

- Frontend: HTML5, CSS3, JavaScript
- Backend: Python (Django)
- Database: SQLite (default)

## Setup (Windows)

1. Install **Python 3.11+** from `https://www.python.org/downloads/`  
   During install, check **“Add Python to PATH”**.
2. In this project folder, create a virtual environment:

```bash
python -m venv .venv
.venv\\Scripts\\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run migrations and create admin user:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. Run the server:

```bash
python manage.py runserver
```

Open the app at `http://127.0.0.1:8000/`  
Open admin at `http://127.0.0.1:8000/admin/`

## Main Modules (Mapped to Your Report)

- **User Authentication Module**: Register/Login/Logout
- **User Profile Module**: Profile + manage skills + levels
- **Skill Listing Module**: Browse/search all users and skills
- **Skill Swap Request Module**: Send/Accept/Reject requests with status tracking
- **Dashboard Module**: Personalized home with skills + requests
- **Admin Module**: Manage users, skills, and requests

