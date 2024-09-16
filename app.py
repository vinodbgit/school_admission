from flask import *
from functools import wraps
from flask_mysqldb import MySQL
import secrets
from flask_bcrypt import Bcrypt
import re
import os
import datetime
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import matplotlib.ticker as mtick


app=Flask(__name__)
app.config['SECRET_KEY']=secrets.token_hex(16)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sms'
# Ensure to configure the mail settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'premkumarbanakar@gmail.com'
app.config['MAIL_PASSWORD'] = 'yjqx zgcl fnez wbnx'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# Configuration for pdfkit
pdfkit_config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
options = {
    'quiet': '',
    'disable-smart-shrinking': '',
    'no-stop-slow-scripts': '',
    'debug-javascript': '',
    'enable-local-file-access': ''
}


# Custom 404 error handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# to restrict access to certain routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('You need to log in first.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize MySQL
mysql = MySQL(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

# Directory for saving uploaded files
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Route to admin register
@app.route('/admin_register', methods=['GET', 'POST'])
@login_required
def admin_register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        gender = request.form['gender']
        mobile = request.form['mobile']
        role = request.form['role']

        # Server-side validation
        if not (first_name and last_name and email and password and confirm_password and gender and mobile and role):
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin_register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin_register'))

        # Ensure mobile number is numeric and of correct length
        if not (mobile.isdigit() and len(mobile) == 10):
            flash('Mobile number must be a 10-digit numeric value.', 'danger')
            return redirect(url_for('admin_register'))

        # Ensure role is 'admin'
        if role.lower() != 'admin':
            flash('Invalid role specified.', 'danger')
            return redirect(url_for('admin_register'))
        
        # Check if email already exists
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admin_table WHERE email = %s", (email,))
        existing_admin = cursor.fetchone()
        cursor.close()

        if existing_admin:
            flash('Email already exists. Please use a different email.', 'danger')
            return redirect(url_for('admin_register'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert into database
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO admin_table (first_name, last_name, email, password, gender, mobile, role) VALUES (%s, %s, %s, %s, %s, %s, %s)", (first_name, last_name, email, hashed_password, gender, mobile, role))
        mysql.connection.commit()
        cursor.close()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin_register.html')

# Route to Admin Login Page
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Server-side validation
        email_regex = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
        if not email_regex.match(email):
            flash('Invalid email address.', 'danger')
            return render_template('admin_login.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('admin_login.html')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admin_table WHERE email=%s", (email,))
        admin = cursor.fetchone()
        cursor.close()

        if admin and bcrypt.check_password_hash(admin[4], password): 
            session['logged_in'] = True
            session['admin_id'] = admin[0]
            session['admin_email'] = admin[3]
            session['admin_role'] = 'Admin'
            flash('You are successlly logged in, Welcome To Admin Dashboard!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!','danger')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

# Route to Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'logged_in' in session:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM admin_table')
        admin = cursor.fetchone()
        role=admin[7]
        email=admin[3]
        cursor.close()
        return render_template('admin_dashboard.html',email=email,role=role)
    else:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('admin_login'))
 
# Route to student dashboard
@app.route('/student_dashboard', methods=['GET', 'POST'])
def student_dashboard():
    # if 'logged_in' in session:
        cursor = mysql.connection.cursor()
    
        # Handle form submission and filtering
        if request.method == 'POST':
            class_filter = request.form.get('class', None)
            caste_filter = request.form.get('caste', None)
            
            # Construct the SQL query with filters
            query = 'SELECT * FROM student WHERE 1=1'
            params = []
            
            if class_filter:
                query += ' AND enrolling_class = %s'
                params.append(class_filter)
            
            if caste_filter:
                query += ' AND caste = %s'
                params.append(caste_filter)
            
            cursor.execute(query, params)
        else:
            cursor.execute('SELECT * FROM student ORDER BY admission_id DESC')
        
        students = cursor.fetchall()
        cursor.close()
        
        # Retrieve admin info
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM admin_table')
        admin = cursor.fetchone()
        cursor.close()
        
        role = admin[7]
        email = admin[3]
        
        return render_template('student_dashboard.html', email=email, role=role, students=students)

    # else:
    #     flash('You need to log in first.', 'danger')
    #     return redirect(url_for('admin_login'))

# Route to view student admission details
@app.route('/view_student/<int:student_id>')
def view_student(student_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM student WHERE admission_id = %s", (student_id,))
    student = cursor.fetchone()
    # Convert student[61] to a string if it's in bytes
    student_photo = student[61].decode('utf-8') if isinstance(student[61], bytes) else student[61]
    cursor.close()
    if student is None:
        return "Student not found", 404
    return render_template('view_student.html', student=student, student_photo=student_photo)

#Route to send the images om the upload folder
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)


# Route to add admission fees
@app.route('/add_admission_fees', methods=['POST'])
def add_admission_fees():
    if request.method == 'POST': 
        try:
            class_name = request.form['class_name']
            admission_fees = float(request.form['admission_fees'])
            tuition_fees = float(request.form['tuition_fees'])
            computer_fees = float(request.form['computer_fees'])
            annual_day_fees = float(request.form['annual_day_fees'])

            cursor=mysql.connection.cursor()
            cursor.execute('SELECT class_name from admission_fees WHERE class_name=%s',(class_name,))
            existing_class_name=cursor.fetchone()
            cursor.close()

            class_name_int=None
            if existing_class_name:
                class_name_str = existing_class_name[0]
                try:
                    class_name_int = int(class_name_str)
                    print(class_name_int)
                except ValueError:
                    print("The class name cannot be converted to an integer.")
        
            if class_name_int:
                flash(f" Fees for Class {class_name_int} is already exist.", "danger")
                return render_template('fees_structure.html')

            if not class_name or admission_fees < 0 or tuition_fees < 0 or computer_fees < 0 or annual_day_fees < 0:
                flash('Please enter valid data for all fields.', 'danger')
                return render_template('fees_structure.html')
            total_amount = admission_fees + tuition_fees + computer_fees + annual_day_fees

            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO admission_fees (class_name, admission_fees, tuition_fees, computer_fees, annual_day_fees, total_amount) VALUES (%s, %s, %s, %s, %s, %s)", 
                (class_name, admission_fees, tuition_fees, computer_fees, annual_day_fees, total_amount)
            )
            mysql.connection.commit()
            cursor.close()
            flash('New Class admission fees added successfully!', 'success')

        except ValueError:
            flash('Invalid input. Please enter numeric values for fees.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')

    return render_template('fees_structure.html')


# Route to add bus fees
@app.route('/add_bus_fees', methods=['POST'])
def add_bus_fees():
    if request.method == 'POST':
        village_name = request.form['village_name']
        first_term = float(request.form['first_term'])
        second_term = float(request.form['second_term'])
        total_amount = first_term + second_term

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO bus_fees (village_name, first_term, second_term, total_amount) VALUES (%s, %s, %s, %s)", 
            (village_name, first_term, second_term, total_amount)
        )
        mysql.connection.commit()
        cursor.close()
    flash('Bus fees added successfully!', 'success')
    return render_template('fees_structure.html')

# Route to fees structure
@app.route('/fees_structure')
def fees_structure():
    if 'logged_in' in session:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM admin_table')
        admin = cursor.fetchone()
        role=admin[7]
        email=admin[3]
        cursor.close()

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admission_fees")
        admission_fees = cursor.fetchall()

        cursor.execute("SELECT * FROM bus_fees")
        bus_fees = cursor.fetchall()
        
        cursor.close()
        return render_template('fees_structure.html',email=email, role=role, admission_fees=admission_fees, bus_fees=bus_fees)
    else:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('admin_login'))

# Route to update the admission fees
@app.route('/update_admission_fees', methods=['POST'])
def update_admission_fees():
    if 'logged_in' in session:
        try:
            admission_fees_id = float(request.form['admission_fees_id'])
            admission_fees = float(request.form['admission_fees'])
            tuition_fees = float(request.form['tuition_fees'])
            computer_fees = float(request.form['computer_fees'])
            annual_day_fees = float(request.form['annual_day_fees'])

            if  admission_fees < 0 or tuition_fees < 0 or computer_fees < 0 or annual_day_fees < 0:
                flash('Please enter valid data for all fields.', 'danger')
                return render_template('fees_structure.html')
            total_amount = admission_fees + tuition_fees + computer_fees + annual_day_fees
            
            cursor = mysql.connection.cursor()
            cursor.execute("""
                UPDATE admission_fees 
                SET admission_fees=%s, tuition_fees=%s, computer_fees=%s, annual_day_fees=%s, total_amount=%s
                WHERE admission_fees_id=%s
            """, (admission_fees, tuition_fees, computer_fees, annual_day_fees, total_amount, admission_fees_id))
            mysql.connection.commit()
            cursor.close()
            
            flash('Admission fees updated successfully!','success')
            return redirect(url_for('fees_structure'))
        
        except ValueError:
            flash('Invalid input. Please enter numeric values for fees.', 'danger')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
        
    else:
        flash('You need to be logged in to update admission fees.','danger')
        return redirect(url_for('admin_login'))

# route to update bus fees
@app.route('/update_bus_fees', methods=['POST'])
def update_bus_fees():
    if request.method == 'POST':
        bus_fees_id = request.form['bus_fees_id']
        first_term = request.form['first_term']
        second_term = request.form['second_term']
        total_amount = float(first_term) + float(second_term)
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE bus_fees 
            SET first_term=%s, second_term=%s, total_amount=%s 
            WHERE bus_fees_id=%s
        """, (first_term, second_term, total_amount, bus_fees_id))
        mysql.connection.commit()
        cursor.close()
        
        flash('Bus fees updated successfully!')
        return redirect(url_for('fees_structure'))

# Route to admission form
@app.route('/new_admission', methods=['GET', 'POST'])
def new_admission():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM admin_table')
    admin = cursor.fetchone()
    role=admin[7]
    email=admin[3]
    cursor.close()

    if request.method == 'GET':
        admission_id = request.args.get('admission_id')
        if admission_id:
            cursor=mysql.connection.cursor()
            cursor.execute("SELECT * FROM student WHERE admission_id = %s", (admission_id,))
            student = cursor.fetchone()
            cursor.close()
            return render_template('new_admission.html',email=email,role=role, student=student, edit_mode=True)
        else:
            return render_template('new_admission.html', email=email, role=role, edit_mode=False)

    if request.method == 'POST':
        admission_id = request.form.get('admission_id')  # Get the student ID from the form (if present)    
        # Get form data
        form_data = request.form.to_dict()
        files_data = request.files.to_dict()

        print(request.form)
        print(request.files)


        try:
            academic_year = request.form['academic_year']
            first_name = request.form['first_name'].upper()
            middle_name = request.form['middle_name'].upper()
            last_name = request.form['last_name'].upper()
            parent_email = request.form['parent_email']
            parent_phone_no = request.form['parent_phone_no']
            gender = request.form['gender']
            dob = request.form['dob']
            place_of_birth = request.form['place_of_birth']
            city = request.form['city'].upper()
            pin_code = request.form['pin_code']
            taluka = request.form['taluka'].upper()
            district = request.form['district'].upper()
            state = request.form['state'].upper()
            father_name = request.form['father_name'].upper()
            father_living_status = request.form['father_living_status']
            mother_name = request.form['mother_name'].upper()
            mother_living_status = request.form['mother_living_status']
            father_education_level = request.form['father_education_level']
            mother_education_level = request.form['mother_education_level']
            father_occupation = request.form['father_occupation']
            mother_occupation = request.form['mother_occupation']
            parent_annual_income = request.form['parent_annual_income']
            number_of_dependents = request.form['number_of_dependents']
            pupil_staying_with = request.form['pupil_staying_with']
            guardian_name = request.form['guardian_name'].upper()
            guardian_address = request.form['guardian_address']
            nationality = request.form['nationality'].upper()
            religion = request.form['religion'].upper()
            caste = request.form['caste']
            mother_tongue = request.form['mother_tongue'].upper()
            any_other_languages_spoken = request.form['any_other_languages_spoken'].upper()
            number_of_brothers = request.form['number_of_brothers']
            elder_brothers = request.form['elder_brothers']
            younger_brothers = request.form['younger_brothers']
            number_of_sisters = request.form['number_of_sisters']
            elder_sisters = request.form['elder_sisters']
            younger_sisters = request.form['younger_sisters']
            permanent_address = request.form['permanent_address']
            permanent_city = request.form['permanent_city']
            permanent_pin_code = request.form['permanent_pin_code']
            permanent_taluka = request.form['permanent_taluka']
            permanent_district = request.form['permanent_district']
            permanent_state = request.form['permanent_state']
            present_address = request.form['present_address']
            present_city = request.form['present_city'].upper()
            present_pin_code = request.form['present_pin_code']
            present_taluka = request.form['present_taluka'].upper()
            present_district = request.form['present_district'].upper()
            present_state = request.form['present_state'].upper()
            studied_in_previous_school = request.form['studied_in_previous_school'].upper()
            previous_studied_class = request.form['previous_studied_class']
            date_of_transfer_certificate = request.form['date_of_transfer_certificate']
            enrolling_class = request.form['enrolling_class']
            date_of_enrollment = request.form['date_of_enrollment']

            # File uploads
            birth_certificate = request.files['birth_certificate']
            aadhaar_card = request.files['aadhaar_card']
            father_mother_aadhaar_card = request.files['father_mother_aadhaar_card']
            income_certificate = request.files['income_certificate']
            ration_card = request.files['ration_card']
            passport_size_photo = request.files['passport_size_photo']
            passbook = request.files['passbook']
            transfer_certificate = request.files['transfer_certificate']
            previous_class_marks_card = request.files['previous_class_marks_card']

            # Validate data
            email_regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
            phone_regex = r'^\d{10}$'
            date_regex = r'^\d{4}-\d{2}-\d{2}$'

            # Backend validation 
            if not academic_year or not re.match(r'^\d{4}-\d{4}$', academic_year):
                flash('Invalid Academic Year format. Use YYYY-YYYY.', 'error')
                return redirect(url_for('new_admission'))
            
            if not first_name or not re.match(r'^[A-Za-z]+$', first_name):
                flash('First Name must contain only letters.', 'error')
                return redirect(url_for('new_admission'))
            
            if not middle_name or not re.match(r'^[A-Za-z]+$', middle_name):
                flash('Middle Name must contain only letters.', 'error')
                return redirect(url_for('new_admission'))
            
            if not last_name or not re.match(r'^[A-Za-z]+$', last_name):
                flash('Last Name must contain only letters.', 'error')
                return redirect(url_for('new_admission'))

            if not parent_email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', parent_email):
                flash('Invalid email format.', 'error')
                return redirect(url_for('new_admission'))

            if not parent_phone_no or not re.match(r'^\d{10}$', parent_phone_no):
                flash('Phone Number must be exactly 10 digits.', 'error')
                return redirect(url_for('new_admission'))
            
            if not gender:
                flash('Please select a gender.', 'error')
                return redirect(url_for('new_admission'))
            
            if not dob:
                flash('Please enter your Date of Birth.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not city:
                flash('Please enter your city.', 'danger')
                return redirect(url_for('new_admission'))
            
            if len(city) < 2:
                flash('City name must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not pin_code:
                flash('Please enter your pin code.', 'danger')
                return redirect(url_for('new_admission'))
        
            if not pin_code.isdigit() or len(pin_code) != 6:
                flash('Pin Code must be exactly 6 digits.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not taluka:
                flash('Please enter the taluka.', 'danger')
                return redirect(url_for('new_admission'))
        
            if len(taluka) < 2:
                flash('Taluka must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            
            today = datetime.date.today()
            dob_date = datetime.date.fromisoformat(dob)
            if dob_date > today:
                flash('Date of Birth cannot be in the future.', 'danger')

            if not re.match(date_regex, form_data['dob']):
                flash('Invalid date of birth format', 'danger')
                return render_template('new_admission.html', form_data=form_data)
            
            if not place_of_birth:
                flash('Please enter your Place of Birth.', 'danger')
                return redirect(url_for('new_admission'))
            
            if len(place_of_birth) < 2:
                flash('Place of Birth must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not district:
                flash('Please enter the district.', 'danger')
                return redirect(url_for('new_admission'))
        
            if len(district) < 2:
                flash('District must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not state:
                flash('Please enter the state.', 'danger')
                return redirect(url_for('new_admission'))
        
            if len(state) < 2:
                flash('State must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not father_name:
                flash('Please enter the Father\'s Name.', 'danger')
                return redirect(url_for('new_admission'))
        
            if len(father_name) < 2:
                flash('Father\'s Name must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not father_living_status:
                flash('Please select Father\'s Living Status.', 'danger')
                return redirect(url_for('new_admission'))

            
            if not mother_name:
                flash('Please enter Mother\'s Name.', 'danger')
                return redirect(url_for('new_admission'))
            
            if len(mother_name) < 2:
                flash('Mother\'s Name must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not mother_living_status:
                flash('Please select Mother\'s Living Status.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not father_education_level:
                flash('Please select Father\'s Education Level.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not mother_education_level:
                flash('Please select Mother\'s Education Level.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not father_occupation:
                flash('Please enter Father\'s Occupation.', 'danger')
                return redirect(url_for('new_admission'))
            
            if len(father_occupation) < 2:
                flash('Father\'s Occupation must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not mother_occupation:
                flash('Please enter Mother\'s Occupation.', 'danger')
                return redirect(url_for('new_admission'))

            if len(mother_occupation) < 2:
                flash('Mother\'s Occupation must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not parent_annual_income:
                flash('Please enter the parent annual income.', 'danger')
                return redirect(url_for('new_admission'))
            
            if parent_annual_income:
                try:
                    parent_annual_income = float(parent_annual_income)
                    if parent_annual_income <= 0:
                        flash('Parent\'s Annual Income must be a positive number.', 'danger')
                        return redirect(url_for('new_admission'))
                except ValueError:
                    flash('Invalid input for Parent\'s Annual Income. Please enter a valid income.', 'danger')
                    return redirect(url_for('new_admission'))
            
            if not number_of_dependents:
                flash('Please enter the number of dependents.', 'danger')
                return redirect(url_for('new_admission'))
        
            if not number_of_dependents.isdigit():
                flash('Number of dependents must be a valid integer.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not pupil_staying_with:
                flash('Please select an option for Pupil Staying With.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not guardian_name:
                flash('Please enter Guardian Name.', 'danger')
                return redirect(url_for('new_admission'))
        
            if len(guardian_name) < 2:
                flash('Guardian Name must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not guardian_address:
                flash('Please enter Guardian Address.', 'danger')
                return redirect(url_for('new_admission'))
        
            if len(guardian_address) < 10:
                flash('Guardian Address must be at least 10 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not nationality:
                flash('Please select a nationality.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not religion:
                flash('Please select a religion.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not caste:
                flash('Please select your caste.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not mother_tongue:
                flash('Please enter your mother tongue.', 'danger')
                return redirect(url_for('new_admission'))
        
            if len(mother_tongue) < 2:
                flash('Mother Tongue must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if len(any_other_languages_spoken) > 0 and len(any_other_languages_spoken) < 2:
                flash('Languages spoken must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if number_of_brothers == '':
                flash('Please enter the number of brothers.', 'danger')
                return redirect(url_for('new_admission'))
            
            if number_of_brothers:
                try:
                    if int(number_of_brothers) < 0:
                        flash('Number of brothers must be a non-negative integer.', 'danger')
                        return redirect(url_for('new_admission'))
                except ValueError:
                    flash('Number of brothers must be a valid integer.', 'danger')
                    return redirect(url_for('new_admission'))
            
            if elder_brothers:
                if not elder_brothers.isdigit() or int(elder_brothers) < 0:
                    flash('Number of elder brothers must be a non-negative integer.', 'danger')
                    return redirect(url_for('new_admission'))
            else:
                elder_brothers = 0 
            

            if younger_brothers:
                if not younger_brothers.isdigit() or int(younger_brothers) < 0:
                    flash('Number of younger brothers must be a non-negative integer.', 'danger')
                    return redirect(url_for('new_admission'))
            else:
                younger_brothers = 0
            
            if number_of_sisters == '':
                flash('Please enter the number of sisters.', 'danger')
                return redirect(url_for('new_admission'))

            if number_of_sisters:
                try:
                    if int(number_of_sisters) < 0:
                        flash('Number of sisters must be a non-negative integer.', 'danger')
                        return redirect(url_for('new_admission'))
                except ValueError:
                    flash('Number of sisters must be a valid integer.', 'danger')
                    return redirect(url_for('new_admission'))
            
            if elder_sisters:
                if not elder_sisters.isdigit() or int(elder_sisters) < 0:
                    flash('Number of elder sisters must be a non-negative integer.', 'danger')
                    return redirect(url_for('new_admission'))

            if younger_sisters:
                if not younger_sisters.isdigit() or int(younger_sisters) < 0:
                    flash('Number of younger sisters must be a non-negative integer.', 'danger')
                    return redirect(url_for('new_admission'))
            
            if not permanent_address:
                flash('Please enter Permanent Address.', 'danger')
                return redirect(url_for('new_admission'))

            if len(permanent_address) < 5:
                flash('Permanent Address must be at least 5 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            if not permanent_city:
                flash('Please enter City.', 'danger')
                return redirect(url_for('new_admission'))

            if len(permanent_city) < 2:
                flash('City must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            

            if not permanent_pin_code:
                flash('Please enter Pin Code.', 'danger')
                return redirect(url_for('new_admission'))

            if not permanent_pin_code.isdigit() or len(permanent_pin_code) != 6:
                flash('Pin Code must be a 6-digit number.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not permanent_taluka:
                flash('Please enter Taluka.', 'danger')
                return redirect(url_for('new_admission'))

            if len(permanent_taluka) < 2:
                flash('Taluka must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            if not permanent_district:
                flash('Please enter District.', 'danger')
                return redirect(url_for('new_admission'))

            if len(permanent_district) < 2:
                flash('District must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            if not permanent_state:
                flash('Please enter State.', 'danger')
                return redirect(url_for('new_admission'))

            if len(permanent_state) < 2:
                flash('State must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not present_address:
                flash('Please enter Present Address.', 'danger')
                return redirect(url_for('new_admission'))

            if len(present_address) < 5:
                flash('Present Address must be at least 5 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not present_city:
                flash('Please enter City.', 'danger')
                return redirect(url_for('new_admission'))

            if len(present_city) < 2:
                flash('City must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            if not present_pin_code:
                flash('Please enter Pin Code.', 'danger')
                return redirect(url_for('new_admission'))

            if not present_pin_code.isdigit() or len(present_pin_code) != 6:
                flash('Pin Code must be a 6-digit number.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not present_taluka:
                flash('Please enter Taluka.', 'danger')
                return redirect(url_for('new_admission'))

            if len(present_taluka) < 2:
                flash('Taluka must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            if not present_district:
                flash('Please enter District.', 'danger')
                return redirect(url_for('new_admission'))

            if len(present_district) < 2:
                flash('District must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            if not present_state:
                flash('Please enter State.', 'danger')
                return redirect(url_for('new_admission'))

            if len(present_state) < 2:
                flash('State must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))
            
            if not studied_in_previous_school:
                flash('Please enter the name of the previous school.', 'danger')
                return redirect(url_for('new_admission'))

            if len(studied_in_previous_school) < 2:
                flash('Previous school name must be at least 2 characters long.', 'danger')
                return redirect(url_for('new_admission'))

            if not previous_studied_class:
                flash('Please select the previous studied class.', 'danger')
                return redirect(url_for('new_admission'))

            if previous_studied_class not in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                flash('Previous studied class must be a valid number between 1 and 9.', 'danger')
                return redirect(url_for('new_admission'))

            if not enrolling_class:
                flash('Please select the enrolling class.', 'danger')
                return redirect(url_for('new_admission'))

            if enrolling_class not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                flash('Enrolling class must be a valid number between 1 and 10.', 'danger')
                return redirect(url_for('new_admission'))

            if not date_of_transfer_certificate:
                flash('Please enter the date of the transfer certificate.', 'danger')
                return redirect(url_for('new_admission'))

            if not date_of_enrollment:
                flash('Please enter the date of enrollment.', 'danger')
                return redirect(url_for('new_admission'))

    
            # Save files
            def save_file(file):
                if file and (file.filename.endswith('.pdf') or file.filename.endswith('.jpg') or file.filename.endswith('.jpeg')):
                    filename = file.filename
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    return filename
                return None

            # Save files and store their names in form_data
            form_data['birth_certificate'] = save_file(files_data.get('birth_certificate'))
            form_data['aadhaar_card'] = save_file(files_data.get('aadhaar_card'))
            form_data['father_mother_aadhaar_card'] = save_file(files_data.get('father_mother_aadhaar_card'))
            form_data['income_certificate'] = save_file(files_data.get('income_certificate'))
            form_data['ration_card'] = save_file(files_data.get('ration_card'))
            form_data['passport_size_photo'] = save_file(files_data.get('passport_size_photo'))
            form_data['passbook'] = save_file(files_data.get('passbook'))
            form_data['transfer_certificate'] = save_file(files_data.get('transfer_certificate'))
            form_data['previous_class_marks_card'] = save_file(files_data.get('previous_class_marks_card'))


            # Insert new or update existing admission record
            cursor = mysql.connection.cursor()

            # Check if we are updating an existing student
            if admission_id:
                # Update the student record
                query = """
                    UPDATE student SET
                        academic_year=%s, first_name=%s, middle_name=%s, last_name=%s, parent_email=%s, parent_phone_no=%s, gender=%s, dob=%s, place_of_birth=%s,
                        city=%s, pin_code=%s, taluka=%s, district=%s, state=%s, father_name=%s, father_living_status=%s, mother_name=%s, mother_living_status=%s,
                        father_education_level=%s, mother_education_level=%s, father_occupation=%s, mother_occupation=%s, parent_annual_income=%s,
                        number_of_dependents=%s, pupil_staying_with=%s, guardian_name=%s, guardian_address=%s, nationality=%s, religion=%s, caste=%s, 
                        mother_tongue=%s, any_other_languages_spoken=%s, number_of_brothers=%s, elder_brothers=%s, younger_brothers=%s, number_of_sisters=%s,
                        elder_sisters=%s, younger_sisters=%s, permanent_address=%s, permanent_city=%s, permanent_pin_code=%s, permanent_taluka=%s,
                        permanent_district=%s, permanent_state=%s, present_address=%s, present_city=%s, present_pin_code=%s, present_taluka=%s,
                        present_district=%s, present_state=%s, studied_in_previous_school=%s, previous_studied_class=%s, date_of_transfer_certificate=%s,
                        enrolling_class=%s, date_of_enrollment=%s
                    WHERE admission_id=%s
                """
                values = (
                form_data['academic_year'], form_data['first_name'], form_data['middle_name'], form_data['last_name'], form_data['parent_email'],
                form_data['parent_phone_no'], form_data['gender'], form_data['dob'], form_data['place_of_birth'], form_data['city'],
                form_data['pin_code'], form_data['taluka'], form_data['district'], form_data['state'], form_data['father_name'],
                form_data['father_living_status'], form_data['mother_name'], form_data['mother_living_status'], form_data['father_education_level'],
                form_data['mother_education_level'], form_data['father_occupation'], form_data['mother_occupation'], form_data['parent_annual_income'],
                form_data['number_of_dependents'], form_data['pupil_staying_with'], form_data['guardian_name'], form_data['guardian_address'],
                form_data['nationality'], form_data['religion'], form_data['caste'], form_data['mother_tongue'], form_data['any_other_languages_spoken'],
                form_data['number_of_brothers'], form_data['elder_brothers'], form_data['younger_brothers'], form_data['number_of_sisters'],
                form_data['elder_sisters'], form_data['younger_sisters'], form_data['permanent_address'], form_data['permanent_city'],
                form_data['permanent_pin_code'], form_data['permanent_taluka'], form_data['permanent_district'], form_data['permanent_state'],
                form_data['present_address'], form_data['present_city'], form_data['present_pin_code'], form_data['present_taluka'],
                form_data['present_district'], form_data['present_state'], form_data['studied_in_previous_school'], form_data['previous_studied_class'],
                form_data['date_of_transfer_certificate'], form_data['enrolling_class'], form_data['date_of_enrollment'],
                admission_id
            )
                cursor.execute(query, values)
                mysql.connection.commit()
                cursor.close()
                flash('Student information updated successfully', 'success')
            
            else:
                query="""INSERT INTO student (
                        academic_year, first_name, middle_name, last_name, parent_email, parent_phone_no, gender, dob,
                        place_of_birth, city, pin_code, taluka, district, state, father_name, father_living_status, mother_name,
                        mother_living_status, father_education_level, mother_education_level, father_occupation, mother_occupation,
                        parent_annual_income, number_of_dependents, pupil_staying_with, guardian_name, guardian_address, nationality,
                        religion, caste, mother_tongue, any_other_languages_spoken, number_of_brothers, elder_brothers, younger_brothers,
                        number_of_sisters, elder_sisters, younger_sisters, permanent_address, permanent_city, permanent_pin_code,
                        permanent_taluka, permanent_district, permanent_state, present_address, present_city, present_pin_code,
                        present_taluka, present_district, present_state, studied_in_previous_school, previous_studied_class,
                        date_of_transfer_certificate, enrolling_class, date_of_enrollment, birth_certificate, aadhaar_card,
                        father_mother_aadhaar_card, income_certificate, ration_card, passport_size_photo, passbook,
                        transfer_certificate, previous_class_marks_card
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                values = (
                    form_data['academic_year'], form_data['first_name'], form_data['middle_name'], form_data['last_name'], form_data['parent_email'],
                    form_data['parent_phone_no'], form_data['gender'], form_data['dob'], form_data['place_of_birth'], form_data['city'],
                    form_data['pin_code'], form_data['taluka'], form_data['district'], form_data['state'], form_data['father_name'],
                    form_data['father_living_status'], form_data['mother_name'], form_data['mother_living_status'], form_data['father_education_level'],
                    form_data['mother_education_level'], form_data['father_occupation'], form_data['mother_occupation'], form_data['parent_annual_income'],
                    form_data['number_of_dependents'], form_data['pupil_staying_with'], form_data['guardian_name'], form_data['guardian_address'],
                    form_data['nationality'], form_data['religion'], form_data['caste'], form_data['mother_tongue'], form_data['any_other_languages_spoken'],
                    form_data['number_of_brothers'], form_data['elder_brothers'], form_data['younger_brothers'], form_data['number_of_sisters'],
                    form_data['elder_sisters'], form_data['younger_sisters'], form_data['permanent_address'], form_data['permanent_city'],
                    form_data['permanent_pin_code'], form_data['permanent_taluka'], form_data['permanent_district'], form_data['permanent_state'],
                    form_data['present_address'], form_data['present_city'], form_data['present_pin_code'], form_data['present_taluka'],
                    form_data['present_district'], form_data['present_state'], form_data['studied_in_previous_school'], form_data['previous_studied_class'],
                    form_data['date_of_transfer_certificate'], form_data['enrolling_class'], form_data['date_of_enrollment'],
                    form_data.get('birth_certificate'), form_data.get('aadhaar_card'), form_data.get('father_mother_aadhaar_card'),
                    form_data.get('income_certificate'), form_data.get('ration_card'), form_data.get('passport_size_photo'), form_data.get('passbook'),
                    form_data.get('transfer_certificate'), form_data.get('previous_class_marks_card')
                )

                cursor.execute(query, values)
                mysql.connection.commit()
                cursor.close()
                flash('Student admission successful', 'success')
            return redirect(url_for('student_dashboard'))
        
        except ValueError:
            flash('Invalid date format. Please use yyyy-mm-dd.', 'danger')
            return render_template('new_admission.html', form_data=form_data)
        except KeyError as e:
            flash(f'Missing field: {str(e)}', 'danger')
            return render_template('new_admission.html', form_data=form_data)
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return render_template('new_admission.html', form_data=form_data)
    
        
    return render_template('new_admission.html', email=email, role=role)


#route to pay fees
@app.route('/pay_fees')
def pay_fees():
    student_id = request.args.get('student_id')
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM student WHERE admission_id = %s", (student_id,))
    student_data = cursor.fetchone()
    cursor.close()

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM admission_fees WHERE class_name = %s', (student_data[54],))
    fees = cursor.fetchone()

    second_term_pay = False
    if request.method == 'POST':
        # Check if the user wants to pay the second term amount
        second_term_pay = request.form.get('second_term_pay') == 'yes'

    cursor.close()
    
    return render_template('pay_fees.html', student=student_data, fees=fees, second_term_pay=second_term_pay)


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# route to submit the payment receipt
@app.route('/submit_payment', methods=['POST'])
def submit_payment():
    student_id = request.form.get('student_id')
    # second_term_pay = request.form.get('second_term_pay') == 'yes'

    # Fetch student details from the database using student_id
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM student WHERE admission_id = %s", (student_id,))
    student_data = cursor.fetchone()
    cursor.close()

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM admission_fees WHERE class_name = %s', (student_data[54],))
    fees = cursor.fetchone()
    cursor.close()

    # Render the HTML with the student details and payment info
    rendered = render_template('pay_fees.html', student=student_data, fees=fees)

    # Convert the HTML to PDF
    pdf = pdfkit.from_string(rendered, False, configuration=pdfkit_config, options=options)

    # Send the PDF via email
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM admin_table')
    admin = cursor.fetchone()
    email=admin[3]
    cursor.close()
    admin_email = email
    parent_email = student_data[5]
    send_email(admin_email, parent_email, pdf, student_data)

    # Update payment status to 'Paid'
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE student SET payment_status = 'Paid' WHERE admission_id = %s", (student_id,))
    mysql.connection.commit()
    cursor.close()

    flash('Payment receipt sent to the parent\'s email successfully!', 'success')
    return redirect(url_for('student_dashboard', student_id=student_id))

def send_email(admin_email, parent_email, pdf, student_data):
    msg = MIMEMultipart()
    msg['From'] = admin_email
    msg['To'] = parent_email
    msg['Subject'] = "Congratulations! Your Child's Admission is Confirmed"

    body = f"""
    Dear {student_data[2]} {student_data[3]} {student_data[4]},

    We are thrilled to inform you that your child, {student_data[2]}, has been successfully admitted to  class {student_data[54]} at BASAVA EDUCATION FOUNDATION! Welcome to our school community!

    Attached to this email is the payment receipt for your records. Please review the details and let us know if you have any questions or need further assistance.


    Warm regards,

    Principal 
    BASAVA EDUCATION FOUNDATION 
    Rabkavi, Bagalkot, SH-53, Jamkhandi Miraj Road, Jamkhandi, Karnataka 587314
    Phone: 099458 82400
    """
    msg.attach(MIMEText(body, 'plain'))

    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename=payment_receipt_{student_data[0]}.pdf')
    msg.attach(attachment)

    server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
    server.starttls()
    server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    text = msg.as_string()
    server.sendmail(admin_email, parent_email, text)
    server.quit()


#Route to download the student list
@app.route('/download_student_list')
def download_student_list():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT admission_id, first_name, last_name, enrolling_class, caste, payment_status FROM student") 
    students = cursor.fetchall()
    cursor.close()

    # Specify the column names
    column_names = ['Admission No', 'First Name', 'Last Name', 'Class', 'Caste', 'Fees']
    
    # Create a DataFrame with the specified columns
    df = pd.DataFrame(students, columns=column_names)
    
    # Create an in-memory output file for the DataFrame
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Student List')
    output.seek(0)

    # Send the file to the user
    return send_file(output, download_name='student_list.xlsx', as_attachment=True)


# Route to contact Form
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    errors = {}
    parent_name = email = phone_number = child_name = grade_level = subject = message = None
    if request.method == 'POST':
        parent_name = request.form['parent_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        child_name = request.form['child_name']
        grade_level = request.form['grade_level']
        subject = request.form['subject']
        message = request.form['message']
        
        # Validate contact Form Fields
        if not parent_name:
            errors['parent_name'] = 'Parent name is required.'
        elif not re.match(r'^[A-Za-z\s]{1,50}$', parent_name):
            errors['parent_name'] = 'Parent name should only contain letters and spaces (up to 50 characters).'

        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'Email must be valid.'

        if not phone_number:
            errors['phone_number'] = 'Phone number is required.'
        elif not phone_number.isdigit() or len(phone_number) != 10:
            errors['phone_number'] = 'Phone number must be exactly 10 digits and contain only numbers.'

        if not child_name:
            errors['child_name'] = 'Child name is required.'
        
        if not grade_level:
            errors['grade_level'] = 'Grade level is required.'
        
        if not subject:
            errors['subject'] = 'Subject is required.'
        elif len(subject) > 100:
            errors['subject'] = 'Subject should be up to 100 characters long.'
        
        if not message:
            errors['message'] = 'Message is required.'

        if errors:
            return render_template('contact.html', errors=errors, 
                                   parent_name=parent_name, email=email, 
                                   phone_number=phone_number, child_name=child_name, 
                                   grade_level=grade_level, subject=subject, 
                                   message=message)
        
        # Insert data into the database
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO contact_requests (parent_name, email, phone_number, child_name, grade_level, subject, message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (parent_name, email, phone_number, child_name, grade_level, subject, message))
        mysql.connection.commit()
        cursor.close()

        flash('''Thank you! Your inquiry has been submitted successfully and we will get back to you soon. We're excited to assist you and appreciate your interest!''', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html', errors=errors)

# Route to acontact requests
@app.route('/contact_requests')
def contact_requests():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM admin_table')
    admin = cursor.fetchone()
    role=admin[7]
    email=admin[3]
    cursor.close()
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM contact_requests ORDER BY id DESC')
    requests = cursor.fetchall()
    cursor.close()
    return render_template('contact_requests.html',email=email,role=role, requests=requests)

# Route to reply contact request
@app.route('/reply_contact_request/<int:request_id>', methods=['POST'])
def reply_contact_request(request_id):
    file = request.files.get('reply_file')
    
    if not file or file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    cursor = mysql.connection.cursor()
    
    try:
        cursor.execute('SELECT email FROM contact_requests WHERE id = %s', (request_id,))
        parent_result = cursor.fetchone()
        parent_email = parent_result[0] if parent_result else None
        
        cursor.execute('SELECT parent_name FROM contact_requests WHERE id = %s', (request_id,))
        parent_names = cursor.fetchone()
        parent_name = parent_names[0]

        cursor.execute('SELECT email FROM admin_table LIMIT 1')
        admin_result = cursor.fetchone()
        admin_email = admin_result[0] if admin_result else None
        
        if parent_email and admin_email:
            msg = Message('Information Regarding Your Admission Inquiry', sender=admin_email, recipients=[parent_email])
            msg.body = f"""
                Dear {parent_name},

                Thank you for your interest in our school. Please find the attached document with the requested information.

                If you have any further questions, feel free to reach out to us.

                Warm regards,

                Principal
                BASAVA EDUCATION FOUNDATION 
                Rabkavi, Bagalkot, SH-53, Jamkhandi Miraj Road, Jamkhandi, Karnataka 587314
                Phone: 099458 82400
                """

            with app.open_resource(file_path) as fp:
                msg.attach(filename, 'application/octet-stream', fp.read())
            
            mail.send(msg)
            flash('Reply sent successfully!','success')

            # Update the database to mark the request as replied
            cursor.execute('UPDATE contact_requests SET replied = TRUE WHERE id = %s', (request_id,))
            mysql.connection.commit()
        else:
            flash('Error retrieving email addresses.','danger')
    
    finally:
        cursor.close()
    
    os.remove(file_path) 
    return redirect(url_for('contact_requests'))


@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
def delete_contact(contact_id):
    # Delete the contact from the database
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM contact_requests WHERE id = %s', (contact_id,))
    mysql.connection.commit()
    cursor.close()
    
    flash('Contact request deleted successfully!', 'success')
    return redirect(url_for('contact_requests'))


def fetch_student_data():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT enrolling_class, gender, religion, caste FROM student')
    data = cursor.fetchall()
    cursor.close()

    # Convert data to DataFrame
    df = pd.DataFrame(data, columns=['enrolling_class', 'gender', 'religion', 'caste'])
    return df

# Route to reports
@app.route('/reports', methods=['POST','GET'])
def reports():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM admin_table')
    admin = cursor.fetchone()
    role=admin[7]
    email=admin[3]
    cursor.close()
    df = fetch_student_data()

    # Plot 1: Enrollment Distribution by Class
    plt.figure(figsize=(10, 6))
    sns.countplot(x='enrolling_class', data=df, palette='viridis')
    plt.title('Enrollment Distribution by Class')
    plt.xlabel('Class')
    plt.ylabel('Number of Students')
    plt.gca().yaxis.set_major_locator(mtick.MaxNLocator(integer=True))
    img1 = BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plot_url1 = base64.b64encode(img1.getvalue()).decode('utf8')
    plt.clf() 

    # Plot 2: Gender Distribution
    plt.figure(figsize=(10, 6))
    sns.countplot(x='gender', data=df, palette='muted')
    plt.title('Gender Distribution')
    plt.xlabel('Gender')
    plt.ylabel('Number of Students')
    img2 = BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plot_url2 = base64.b64encode(img2.getvalue()).decode('utf8')
    plt.clf()

    # Plot 3: Caste Distribution
    plt.figure(figsize=(10, 6))
    sns.countplot(x='caste', data=df, palette='coolwarm')
    plt.title('Caste Distribution')
    plt.xlabel('Caste')
    plt.ylabel('Number of Students')
    img3 = BytesIO()
    plt.savefig(img3, format='png')
    img3.seek(0)
    plot_url3 = base64.b64encode(img3.getvalue()).decode('utf8')
    plt.clf()

    return render_template('reports.html', role=role, email=email, plot_url1=plot_url1, plot_url2=plot_url2, plot_url3=plot_url3)


# Route to about
@app.route('/about')
def about():
    return render_template('about.html')

# Route to gallery
@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

# Route to logout
@app.route('/logout')
@login_required 
def logout():
    session.pop('logged_in', None)
    session.pop('admin_id', None)
    session.pop('email', None)
    session.pop('role', None)
    return redirect(url_for('admin_login'))


if __name__=='__main__':
    app.run(debug=True)