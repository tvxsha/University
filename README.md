# University
A comprehensive web-based university management system built with Flask and Python that streamlines academic operations for administrators, faculty, students, and parents.

**Key Features**

1)Authentication & Authorization

2)JWT-based secure authentication

3)Role-Based Access Control (RBAC)

4)Supported roles: Admin, Student, Faculty, Parent

5)Single role per user

6)Fully protected API endpoints

 **Admin Dashboard**

1)User management and role assignment

2)Subject creation and faculty allocation

3)Approve / deny student re-evaluation requests

4)Full CRUD operations on academic entities

**Student Portal**

1)Subject registration with intelligent slot clash detection

2)Credit limit enforcement (maximum 27 credits per semester)

3)Automated timetable generation

4)View grades, attendance, and course materials

5)Submit re-evaluation requests

**Faculty Dashboard**

1)Manage enrolled students

2)Add and update grades with re-evaluation workflow

3)Mark and track attendance

4)Upload and manage course content

5)Finalize grades after re-evaluation period

**Parent Portal**

1)View child’s timetable and class schedule

2)Monitor academic performance and grades

3)Track attendance records with detailed statistics

**Technical Stack**

Layer	Technology

Backend	Flask, SQLAlchemy

Authentication	JWT (JSON Web Tokens)

Database	SQLite (7 relational tables)

Frontend	HTML5, CSS3, Vanilla JavaScript

Architecture	RESTful APIs

Design	Dark theme with glassmorphic UI

**System Highlights**

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

 **Installation & Setup**
 
1️)Clone the repository

git clone https://github.com/tvxsha/University.git

cd University

2️) Create and activate virtual environment\

python -m venv venv

source venv/bin/activate    # Linux / macOS

venv\Scripts\activate       # Windows

3) Install dependencies

pip install -r requirements.txt

4)Run the Application

python app.py


The application will be available at:

http://127.0.0.1:5000/

**Database Overview**

The system uses 7 relational tables, including:

Users

Roles

Subjects

Enrollments

Attendance

Grades

Re-evaluation Requests

All relationships are managed using SQLAlchemy ORM.

**Security Considerations**

JWT tokens for authentication

Protected routes based on user roles

Secure grade modification and approval workflow

Input validation at both frontend and backend

**Contributing**

Contributions are welcome!
Feel free to open an issue or submit a pull request.
