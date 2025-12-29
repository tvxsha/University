from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User model for all roles: Admin, Student, Faculty, Parent"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, student, faculty, parent
    full_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=True)  # For students
    parent_student_id = db.Column(db.String(50), nullable=True)  # For parents to link to their child
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', foreign_keys='Enrollment.student_id', backref='student', lazy=True)
    taught_subjects = db.relationship('Subject', backref='faculty', lazy=True)
    grades = db.relationship('Grade', backref='student', lazy=True)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    reevaluation_requests = db.relationship('ReEvaluationRequest', backref='student', lazy=True)

class Subject(db.Model):
    """Subject/Course model"""
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    slot = db.Column(db.String(10), nullable=False)  # A1, B1, C1, etc.
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='subject', lazy=True)
    grades = db.relationship('Grade', backref='subject', lazy=True)
    attendance_records = db.relationship('Attendance', backref='subject', lazy=True)
    course_contents = db.relationship('CourseContent', backref='subject', lazy=True)

class Enrollment(db.Model):
    """Student subject enrollment"""
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure unique enrollment
    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id', name='unique_enrollment'),)
    
    faculty = db.relationship('User', foreign_keys=[faculty_id])

class Grade(db.Model):
    """Student grades and marks"""
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5), nullable=False)  # A+, A, B+, etc.
    is_final = db.Column(db.Boolean, default=False)  # Finalized after re-evaluation period
    reevaluation_allowed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'subject_id', name='unique_grade'),)

class Attendance(db.Model):
    """Student attendance records"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReEvaluationRequest(db.Model):
    """Student re-evaluation requests"""
    __tablename__ = 'reevaluation_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, denied
    admin_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CourseContent(db.Model):
    """Course content uploaded by faculty"""
    __tablename__ = 'course_content'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Could be text, URL, or file path
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    faculty = db.relationship('User', foreign_keys=[faculty_id])