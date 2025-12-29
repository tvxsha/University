# University
A comprehensive web-based university management system built with Flask and Python that streamlines academic operations for administrators, faculty, students, and parents.
Key Features
🔐 Authentication & Authorization

JWT-based secure authentication

Role-Based Access Control (RBAC)

Supported roles: Admin, Student, Faculty, Parent

Single role per user

Fully protected API endpoints

👑 Admin Dashboard

User management and role assignment

Subject creation and faculty allocation

Approve / deny student re-evaluation requests

Full CRUD operations on academic entities

🎓 Student Portal

Subject registration with intelligent slot clash detection

Credit limit enforcement (maximum 27 credits per semester)

Automated timetable generation

View grades, attendance, and course materials

Submit re-evaluation requests

👨‍🏫 Faculty Dashboard

Manage enrolled students

Add and update grades with re-evaluation workflow

Mark and track attendance

Upload and manage course content

Finalize grades after re-evaluation period

👨‍👩‍👧 Parent Portal

View child’s timetable and class schedule

Monitor academic performance and grades

Track attendance records with detailed statistics

🛠️ Technical Stack
Layer	Technology
Backend	Flask, SQLAlchemy
Authentication	JWT (JSON Web Tokens)
Database	SQLite (7 relational tables)
Frontend	HTML5, CSS3, Vanilla JavaScript
Architecture	RESTful APIs
Design	Dark theme with glassmorphic UI
📊 System Highlights

RESTful API architecture with 30+ endpoints

Real-time validation for:

Slot clashes

Credit limits

Secure grade management and re-evaluation workflow

Responsive UI for desktop, tablet, and mobile

Complete CRUD operations for all entities

📁 Project Structure
University/
├── app.py                # Flask application entry point
├── config.py             # App configuration and secrets
├── models.py             # Database models (SQLAlchemy)
├── requirements.txt      # Python dependencies
├── templates/            # Frontend HTML files
│   ├── index.html
│   ├── admin.html
│   ├── faculty.html
│   ├── student.html
│   └── parent.html
└── static/               # CSS, JS, and assets

⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/tvxsha/University.git
cd University

2️⃣ Create and activate virtual environment
python -m venv venv
source venv/bin/activate    # Linux / macOS
venv\Scripts\activate       # Windows

3️⃣ Install dependencies
pip install -r requirements.txt

🚀 Run the Application
python app.py


The application will be available at:

http://127.0.0.1:5000/

🗃️ Database Overview

The system uses 7 relational tables, including:

Users

Roles

Subjects

Enrollments

Attendance

Grades

Re-evaluation Requests

All relationships are managed using SQLAlchemy ORM.

🔒 Security Considerations

JWT tokens for authentication

Protected routes based on user roles

Secure grade modification and approval workflow

Input validation at both frontend and backend

🤝 Contributing

Contributions are welcome!
Feel free to open an issue or submit a pull request.
