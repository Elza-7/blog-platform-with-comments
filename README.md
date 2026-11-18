# Blog Platform with Comments

A full-stack blogging application built with Python Flask, SQLite, HTML, CSS and a little JavaScript.

## Features

- User registration and login
- Password hashing
- Login-protected dashboard
- Create, read, update and delete blog posts
- Comment on posts
- Authors can delete comments on their own posts; comment authors can delete their own comments
- Search posts by title, content or author
- CSRF protection on forms
- SQLite database created automatically

## Requirements

- Python 3.10 or newer
- VS Code (recommended)

## Run on Windows (PowerShell)

Open this folder in VS Code, then run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, use Command Prompt:

```bat
venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Run on macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## First use

1. Open the website.
2. Select **Register** and create an account.
3. Sign in and choose **Write a post**.
4. Publish a post.
5. Open a post and add a comment (you must be signed in).

The SQLite database is created at `instance/blog.db` on the first run.

## Project structure

```text
blog-platform/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── instance/              # created automatically; local database
├── static/
│   ├── script.js
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── post_form.html
    ├── post_detail.html
    └── error.html
```

## Before deployment

- Set a long, random `SECRET_KEY` environment variable.
- Set `debug=False`.
- Use a production WSGI server (for example, Waitress on Windows or Gunicorn on Linux).
- Configure a production database and HTTPS.
- Do not commit your `.env`, `instance/` folder, or database file.
