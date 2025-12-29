from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Subject, Enrollment, Grade, Attendance, ReEvaluationRequest, CourseContent
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from config import Config
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

# ============= FRONTEND ROUTES =============

@app.route('/')
def home():
    """Serve login page"""
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    """Serve admin dashboard"""
    return render_template('admin.html')

@app.route('/student')
def student_dashboard():
    """Serve student dashboard"""
    return render_template('student.html')

@app.route('/faculty')
def faculty_dashboard():
    """Serve faculty dashboard"""
    return render_template('faculty.html')

@app.route('/parent')
def parent_dashboard():
    """Serve parent dashboard"""
    return render_template('parent.html')

# ============= DATABASE INITIALIZATION =============

# Create tables
with app.app_context():
    db.create_all()
    # Create default admin if doesn't exist
    if not User.query.filter_by(email='admin@university.com').first():
        admin = User(
            email='admin@university.com',
            password=generate_password_hash('admin123'),
            role='admin',
            full_name='System Administrator'
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: admin@university.com / admin123")

# ============= AUTHENTICATION =============

@app.route('/api/register', methods=['POST'])
@jwt_required()
def register():
    """Register new user (Admin only can assign roles). Admin-only endpoint."""
    current_user = User.query.get(int(get_jwt_identity()))
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403

    data = request.get_json() or {}
    # Basic payload validation
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'student')

    if not email or not password or not full_name:
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(
        email=email,
        password=generate_password_hash(password),
        role=role,
        full_name=full_name,
        student_id=data.get('student_id'),
        parent_student_id=data.get('parent_student_id')
    )

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error (duplicate or invalid data)'}), 400

    return jsonify({'message': 'User registered successfully', 'user_id': user.id}), 201
@app.route('/api/login', methods=['POST'])
def login():
    """Login and get JWT token"""
    data = request.get_json() or {}

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )

    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'full_name': user.full_name
        }
    }), 200

# ============= ADMIN ENDPOINTS =============

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Admin: Get all users"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'email': u.email,
        'role': u.role,
        'full_name': u.full_name,
        'student_id': u.student_id
    } for u in users]), 200

@app.route('/api/admin/assign-role', methods=['POST'])
@jwt_required()
def assign_role():
    """Admin: Assign role to user"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    user = User.query.get(data['user_id'])
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.role = data['role']
    db.session.commit()
    
    return jsonify({'message': 'Role assigned successfully'}), 200

@app.route('/api/admin/reevaluation-requests', methods=['GET'])
@jwt_required()
def get_reevaluation_requests():
    """Admin: Get all re-evaluation requests"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    requests = ReEvaluationRequest.query.all()
    return jsonify([{
        'id': r.id,
        'student_id': r.student_id,
        'subject_id': r.subject_id,
        'reason': r.reason,
        'status': r.status,
        'created_at': r.created_at.isoformat()
    } for r in requests]), 200

@app.route('/api/admin/reevaluation-requests/<int:request_id>', methods=['PUT'])
@jwt_required()
def approve_reevaluation(request_id):
    """Admin: Approve or deny re-evaluation request"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    req = ReEvaluationRequest.query.get(request_id)
    
    if not req:
        return jsonify({'error': 'Request not found'}), 404
    
    req.status = data['status']  # 'approved' or 'denied'
    req.admin_comment = data.get('admin_comment')
    
    # If approved, unlock grade for editing
    if req.status == 'approved':
        grade = Grade.query.filter_by(
            student_id=req.student_id,
            subject_id=req.subject_id
        ).first()
        if grade:
            grade.reevaluation_allowed = True
    
    db.session.commit()
    
    return jsonify({'message': 'Request processed successfully'}), 200

# ============= SUBJECT MANAGEMENT =============

@app.route('/api/subjects', methods=['POST'])
@jwt_required()
def create_subject():
    """Admin/Faculty: Create new subject"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role not in ['admin', 'faculty']:
        return jsonify({'error': 'Admin or Faculty access required'}), 403
    
    data = request.get_json()
    subject = Subject(
        name=data['name'],
        code=data['code'],
        credits=data['credits'],
        slot=data['slot'],  # A1, B1, C1, etc.
        faculty_id=data.get('faculty_id')
    )
    
    db.session.add(subject)
    db.session.commit()
    
    return jsonify({'message': 'Subject created', 'subject_id': subject.id}), 201

@app.route('/api/subjects', methods=['GET'])
@jwt_required()
def get_subjects():
    """Get all subjects"""
    subjects = Subject.query.all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'code': s.code,
        'credits': s.credits,
        'slot': s.slot,
        'faculty_id': s.faculty_id,
        'faculty_name': s.faculty.full_name if s.faculty else None
    } for s in subjects]), 200

# ============= STUDENT ENDPOINTS =============

@app.route('/api/student/enroll', methods=['POST'])
@jwt_required()
def enroll_subject():
    """Student: Register for subjects"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'student':
        return jsonify({'error': 'Student access required'}), 403
    
    data = request.get_json() or {}
    subject_ids = data.get('subject_ids')
    if not subject_ids or not isinstance(subject_ids, list):
        return jsonify({'error': 'subject_ids must be a non-empty list'}), 400

    # Load requested subjects
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()
    if len(subjects) != len(subject_ids):
        return jsonify({'error': 'One or more subjects not found'}), 404

    # Existing enrollments
    existing_enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    existing_subject_ids = {e.subject_id for e in existing_enrollments}
    existing_slots = {e.subject.slot for e in existing_enrollments}

    # Build list of new subjects to create (skip duplicates)
    to_create = []
    new_slots = []

    for s in subjects:
        if s.id in existing_subject_ids:
            # skip duplicate subject
            continue
        to_create.append(s)
        new_slots.append(s.slot)

    # Compute total credits after adding new subjects
    all_subject_ids = list(existing_subject_ids) + [s.id for s in to_create]
    total_credits = sum(s.credits for s in Subject.query.filter(Subject.id.in_(all_subject_ids)).all()) if all_subject_ids else 0

    if total_credits > 27:
        return jsonify({'error': 'Total credits cannot exceed 27'}), 400

    # Check for slot clashes between new subjects and existing slots
    for slot in new_slots:
        if slot in existing_slots:
            return jsonify({'error': f'Slot clash detected with existing enrollment for slot {slot}'}), 400

    # Check for duplicates among new_slots
    if len(new_slots) != len(set(new_slots)):
        return jsonify({'error': 'Slot clash detected among selected subjects'}), 400

    # Create enrollments for the non-duplicate requested subjects
    for subject in to_create:
        enrollment = Enrollment(
            student_id=current_user.id,
            subject_id=subject.id,
            faculty_id=subject.faculty_id
        )
        db.session.add(enrollment)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Database integrity error while enrolling'}), 400

    return jsonify({'message': 'Enrolled successfully'}), 201

@app.route('/api/student/subjects', methods=['GET'])
@jwt_required()
def get_student_subjects():
    """Student: Get enrolled subjects"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'student':
        return jsonify({'error': 'Student access required'}), 403
    
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    
    return jsonify([{
        'subject_id': e.subject.id,
        'name': e.subject.name,
        'code': e.subject.code,
        'credits': e.subject.credits,
        'slot': e.subject.slot,
        'faculty_name': e.faculty.full_name if e.faculty else None
    } for e in enrollments]), 200

@app.route('/api/student/timetable', methods=['GET'])
@jwt_required()
def get_timetable():
    """Student: Get personalized timetable"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'student':
        return jsonify({'error': 'Student access required'}), 403
    
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    
    timetable = {}
    for e in enrollments:
        slot = e.subject.slot
        if slot not in timetable:
            timetable[slot] = []
        timetable[slot].append({
            'subject': e.subject.name,
            'code': e.subject.code,
            'faculty': e.faculty.full_name if e.faculty else None
        })
    
    return jsonify(timetable), 200

@app.route('/api/student/grades', methods=['GET'])
@jwt_required()
def get_student_grades():
    """Student: View marks and grades"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'student':
        return jsonify({'error': 'Student access required'}), 403
    
    grades = Grade.query.filter_by(student_id=current_user.id).all()
    
    return jsonify([{
        'subject': g.subject.name,
        'marks': g.marks,
        'grade': g.grade,
        'is_final': g.is_final
    } for g in grades]), 200

@app.route('/api/student/reevaluation', methods=['POST'])
@jwt_required()
def submit_reevaluation():
    """Student: Submit re-evaluation request"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'student':
        return jsonify({'error': 'Student access required'}), 403
    
    data = request.get_json()
    
    request_obj = ReEvaluationRequest(
        student_id=current_user.id,
        subject_id=data['subject_id'],
        reason=data['reason']
    )
    
    db.session.add(request_obj)
    db.session.commit()
    
    return jsonify({'message': 'Re-evaluation request submitted'}), 201

@app.route('/api/student/attendance', methods=['GET'])
@jwt_required()
def get_student_attendance():
    """Student: View attendance records"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'student':
        return jsonify({'error': 'Student access required'}), 403
    
    attendance = Attendance.query.filter_by(student_id=current_user.id).all()
    
    return jsonify([{
        'subject': a.subject.name,
        'date': a.date.isoformat(),
        'status': a.status
    } for a in attendance]), 200

@app.route('/api/student/course-content/<int:subject_id>', methods=['GET'])
@jwt_required()
def get_course_content(subject_id):
    """Student: View course content for enrolled subject"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'student':
        return jsonify({'error': 'Student access required'}), 403
    
    # Check if student is enrolled
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        subject_id=subject_id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this subject'}), 403
    
    content = CourseContent.query.filter_by(subject_id=subject_id).all()
    
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'content': c.content,
        'uploaded_at': c.uploaded_at.isoformat()
    } for c in content]), 200

# ============= FACULTY ENDPOINTS =============

@app.route('/api/faculty/students', methods=['GET'])
@jwt_required()
def get_faculty_students():
    """Faculty: View students in their subjects"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'faculty':
        return jsonify({'error': 'Faculty access required'}), 403
    
    enrollments = Enrollment.query.filter_by(faculty_id=current_user.id).all()
    
    students = {}
    for e in enrollments:
        subject_name = e.subject.name
        if subject_name not in students:
            students[subject_name] = []
        students[subject_name].append({
            'student_id': e.student.id,
            'name': e.student.full_name,
            'email': e.student.email
        })
    
    return jsonify(students), 200

@app.route('/api/faculty/grades', methods=['POST'])
@jwt_required()
def add_grade():
    """Faculty: Add marks for students"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'faculty':
        return jsonify({'error': 'Faculty access required'}), 403
    
    data = request.get_json()
    
    # Check if faculty teaches this subject
    enrollment = Enrollment.query.filter_by(
        student_id=data['student_id'],
        subject_id=data['subject_id'],
        faculty_id=current_user.id
    ).first()
    
    if not enrollment:
        return jsonify({'error': 'Unauthorized'}), 403
    
    grade = Grade.query.filter_by(
        student_id=data['student_id'],
        subject_id=data['subject_id']
    ).first()
    
    if grade:
        # Can only edit if re-evaluation is allowed
        if not grade.reevaluation_allowed and grade.is_final:
            return jsonify({'error': 'Grade is final, re-evaluation not approved'}), 403
        grade.marks = data['marks']
        grade.grade = calculate_grade(data['marks'])
    else:
        grade = Grade(
            student_id=data['student_id'],
            subject_id=data['subject_id'],
            marks=data['marks'],
            grade=calculate_grade(data['marks'])
        )
        db.session.add(grade)
    
    db.session.commit()
    
    return jsonify({'message': 'Grade added successfully'}), 201

@app.route('/api/faculty/finalize-grades', methods=['POST'])
@jwt_required()
def finalize_grades():
    """Faculty: Finalize grades after re-evaluation period"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'faculty':
        return jsonify({'error': 'Faculty access required'}), 403
    
    data = request.get_json()
    subject_id = data['subject_id']
    
    grades = Grade.query.filter_by(subject_id=subject_id).all()
    
    for grade in grades:
        grade.is_final = True
        grade.reevaluation_allowed = False
    
    db.session.commit()
    
    return jsonify({'message': 'Grades finalized'}), 200

@app.route('/api/faculty/course-content', methods=['POST'])
@jwt_required()
def upload_course_content():
    """Faculty: Upload course content"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'faculty':
        return jsonify({'error': 'Faculty access required'}), 403
    
    data = request.get_json()
    
    content = CourseContent(
        subject_id=data['subject_id'],
        faculty_id=current_user.id,
        title=data['title'],
        content=data['content']
    )
    
    db.session.add(content)
    db.session.commit()
    
    return jsonify({'message': 'Content uploaded', 'content_id': content.id}), 201

@app.route('/api/faculty/course-content/<int:content_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_course_content(content_id):
    """Faculty: Update or delete course content"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'faculty':
        return jsonify({'error': 'Faculty access required'}), 403
    
    content = CourseContent.query.get(content_id)
    
    if not content or content.faculty_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'PUT':
        data = request.get_json()
        content.title = data.get('title', content.title)
        content.content = data.get('content', content.content)
        db.session.commit()
        return jsonify({'message': 'Content updated'}), 200
    
    elif request.method == 'DELETE':
        db.session.delete(content)
        db.session.commit()
        return jsonify({'message': 'Content deleted'}), 200

@app.route('/api/faculty/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    """Faculty: Mark attendance for students"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'faculty':
        return jsonify({'error': 'Faculty access required'}), 403
    
    data = request.get_json()
    
    attendance = Attendance(
        student_id=data['student_id'],
        subject_id=data['subject_id'],
        date=datetime.fromisoformat(data['date']),
        status=data['status']  # 'present' or 'absent'
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({'message': 'Attendance marked'}), 201

# ============= PARENT ENDPOINTS =============

@app.route('/api/parent/child-timetable', methods=['GET'])
@jwt_required()
def get_child_timetable():
    """Parent: View child's timetable"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'parent':
        return jsonify({'error': 'Parent access required'}), 403
    
    student = User.query.filter_by(student_id=current_user.parent_student_id).first()
    if not student:
        return jsonify({'error': 'Child not found'}), 404
    
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    
    timetable = {}
    for e in enrollments:
        slot = e.subject.slot
        if slot not in timetable:
            timetable[slot] = []
        timetable[slot].append({
            'subject': e.subject.name,
            'code': e.subject.code,
            'faculty': e.faculty.full_name if e.faculty else None
        })
    
    return jsonify(timetable), 200

@app.route('/api/parent/child-grades', methods=['GET'])
@jwt_required()
def get_child_grades():
    """Parent: View child's marks and grades"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'parent':
        return jsonify({'error': 'Parent access required'}), 403
    
    student = User.query.filter_by(student_id=current_user.parent_student_id).first()
    if not student:
        return jsonify({'error': 'Child not found'}), 404
    
    grades = Grade.query.filter_by(student_id=student.id).all()
    
    return jsonify([{
        'subject': g.subject.name,
        'marks': g.marks,
        'grade': g.grade,
        'is_final': g.is_final
    } for g in grades]), 200

@app.route('/api/parent/child-attendance', methods=['GET'])
@jwt_required()
def get_child_attendance():
    """Parent: View child's attendance"""
    current_user = User.query.get(int(get_jwt_identity()))
    if current_user.role != 'parent':
        return jsonify({'error': 'Parent access required'}), 403
    
    student = User.query.filter_by(student_id=current_user.parent_student_id).first()
    if not student:
        return jsonify({'error': 'Child not found'}), 404
    
    attendance = Attendance.query.filter_by(student_id=student.id).all()
    
    return jsonify([{
        'subject': a.subject.name,
        'date': a.date.isoformat(),
        'status': a.status
    } for a in attendance]), 200

# ============= UTILITY FUNCTIONS =============

def calculate_grade(marks):
    """Calculate letter grade from marks"""
    if marks >= 90: return 'A+'
    elif marks >= 80: return 'A'
    elif marks >= 70: return 'B+'
    elif marks >= 60: return 'B'
    elif marks >= 50: return 'C'
    elif marks >= 40: return 'D'
    else: return 'F'

# ============= RUN APPLICATION =============

if __name__ == '__main__':
    app.run(debug=True)