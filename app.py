from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import oracledb
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database connection details
DB_USER = 'system'
DB_PASSWORD = 'abhi2006'
DB_DSN = 'DESKTOP-2JPORVJ:1521/XE'

def get_db_connection():
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN,mode=oracledb.AUTH_MODE_SYSDBA)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/select_user_type')
def select_user_type():
    return render_template('select_user_type.html')

# Doctor routes
@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors WHERE email = :email AND password = :password", 
                          {'email': email, 'password': password})
            doctor = cursor.fetchone()
            
            if doctor:
                session['doctor_id'] = doctor[0]
                session['doctor_name'] = doctor[1]
                session['user_type'] = 'doctor'
                return redirect(url_for('doctor_dashboard'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash('An error occurred: ' + str(e), 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('doctor_login.html')

@app.route('/doctor/register', methods=['GET', 'POST'])
def doctor_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        specialization = request.form['specialization']
        phone = request.form['phone']
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM doctors WHERE email = :email", {'email': email})
            if cursor.fetchone():
                flash('Email already registered', 'error')
                return redirect(url_for('doctor_register'))
            
            # Insert new doctor
            cursor.execute("""
                INSERT INTO doctors (id, name, email, password, specialization, phone) 
                VALUES (doctor_seq.NEXTVAL, :name, :email, :password, :specialization, :phone)
            """, {
                'name': name,
                'email': email,
                'password': password,
                'specialization': specialization,
                'phone': phone
            })
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('doctor_login'))
        except Exception as e:
            if conn:
                conn.rollback()
            flash('Registration failed: ' + str(e), 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('doctor_register.html')

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'user_type' not in session or session['user_type'] != 'doctor':
        return redirect(url_for('doctor_login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get doctor's appointments
        cursor.execute("""
            SELECT a.id, p.name, p.email, p.phone, a.appointment_date, a.status 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.doctor_id = :doctor_id
            ORDER BY a.appointment_date
        """, {'doctor_id': session['doctor_id']})
        appointments = cursor.fetchall()
        
        # Get doctor details
        cursor.execute("SELECT * FROM doctors WHERE id = :id", {'id': session['doctor_id']})
        doctor = cursor.fetchone()
        
        return render_template('doctor_dashboard.html', 
                             doctor=doctor, 
                             appointments=appointments,
                             date=datetime)  # Pass datetime to template
    except Exception as e:
        flash('Error fetching data: ' + str(e), 'error')
        return redirect(url_for('doctor_login'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/doctor/appointments')
def doctor_appointments():
    if 'user_type' not in session or session['user_type'] != 'doctor':
        return redirect(url_for('doctor_login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all appointments for the logged-in doctor
        cursor.execute("""
            SELECT a.id, p.name, p.email, p.phone, a.appointment_date, a.status 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.doctor_id = :doctor_id
            ORDER BY a.appointment_date
        """, {'doctor_id': session['doctor_id']})
        
        appointments = cursor.fetchall()

        return render_template('doctor_appointments.html', 
                               appointments=appointments,
                               date=datetime)
    except Exception as e:
        flash('Error fetching appointments: ' + str(e), 'error')
        return redirect(url_for('doctor_dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/doctor/profile', methods=['GET', 'POST'])
def doctor_profile():
    if 'user_type' not in session or session['user_type'] != 'doctor':
        return redirect(url_for('doctor_login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            # Update profile
            name = request.form['name']
            email = request.form['email']
            specialization = request.form['specialization']
            phone = request.form['phone']
            
            cursor.execute("""
                UPDATE doctors SET 
                name = :name,
                email = :email,
                specialization = :specialization,
                phone = :phone
                WHERE id = :id
            """, {
                'name': name,
                'email': email,
                'specialization': specialization,
                'phone': phone,
                'id': session['doctor_id']
            })
            conn.commit()
            flash('Profile updated successfully!', 'success')
            session['doctor_name'] = name  # Update session name
        
        # Get current profile
        cursor.execute("SELECT * FROM doctors WHERE id = :id", {'id': session['doctor_id']})
        doctor = cursor.fetchone()
        
        return render_template('doctor_profile.html', doctor=doctor)
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash('Error updating profile: ' + str(e), 'error')
        return redirect(url_for('doctor_dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/doctor/update_status/<int:appointment_id>', methods=['POST'])
def update_appointment_status(appointment_id):
    if 'user_type' not in session or session['user_type'] != 'doctor':
        return redirect(url_for('doctor_login'))
    
    conn = None
    cursor = None
    try:
        status = request.form['status']
        
        # Validate status value
        if status not in ['confirmed', 'cancelled', 'completed', 'pending']:
            flash('Invalid status selected', 'error')
            return redirect(url_for('doctor_appointments'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update appointment status
        cursor.execute("""
            UPDATE appointments SET 
            status = :status,
            last_updated = SYSTIMESTAMP
            WHERE id = :appointment_id AND doctor_id = :doctor_id
        """, {
            'status': status,
            'appointment_id': appointment_id,
            'doctor_id': session['doctor_id']
        })
        
        if cursor.rowcount > 0:
            conn.commit()
            flash(f'Appointment status updated to {status}', 'success')
        else:
            flash('Appointment not found or you do not have permission to update it', 'error')
            
    except Exception as e:
        if conn:
            conn.rollback()
        flash('Error updating appointment status: ' + str(e), 'error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return redirect(url_for('doctor_appointments'))

@app.route('/reschedule_appointment/<int:appointment_id>', methods=['POST'])
def reschedule_appointment(appointment_id):
    if 'user_type' not in session or session['user_type'] != 'patient':
        return redirect(url_for('patient_login'))
    
    conn = None
    cursor = None
    try:
        new_date = request.form['new_date']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify appointment belongs to patient
        cursor.execute("""
            UPDATE appointments SET 
            appointment_date = TO_DATE(:new_date, 'YYYY-MM-DD HH24:MI')
            WHERE id = :appt_id AND patient_id = :patient_id
            RETURNING id
        """, {
            'new_date': new_date.replace('T', ' '),
            'appt_id': appointment_id,
            'patient_id': session['patient_id']
        })
        
        if not cursor.fetchone():
            flash('Appointment not found or you cannot reschedule it', 'error')
        else:
            conn.commit()
            flash('Appointment rescheduled successfully', 'success')
            
    except Exception as e:
        if conn:
            conn.rollback()
        flash('Error rescheduling appointment: ' + str(e), 'error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return redirect(url_for('patient_appointments'))

@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE email = :email AND password = :password", 
                          {'email': email, 'password': password})
            patient = cursor.fetchone()
            
            if patient:
                session['patient_id'] = patient[0]
                session['patient_name'] = patient[1]
                session['user_type'] = 'patient'
                return redirect(url_for('patient_dashboard'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash('An error occurred: ' + str(e), 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('patient_login.html')

@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM patients WHERE email = :email", {'email': email})
            if cursor.fetchone():
                flash('Email already registered', 'error')
                return redirect(url_for('patient_register'))
            
            # Insert new patient
            cursor.execute("""
                INSERT INTO patients (id, name, email, password, phone) 
                VALUES (patient_seq.NEXTVAL, :name, :email, :password, :phone)
            """, {
                'name': name,
                'email': email,
                'password': password,
                'phone': phone
            })
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('patient_login'))
        except Exception as e:
            if conn:
                conn.rollback()
            flash('Registration failed: ' + str(e), 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    return render_template('patient_register.html')

@app.route('/patient/dashboard')
def patient_dashboard():
    if 'user_type' not in session or session['user_type'] != 'patient':
        return redirect(url_for('patient_login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all doctors
        cursor.execute("SELECT * FROM doctors ORDER BY specialization, name")
        doctors = cursor.fetchall()
        
        # Get patient's appointments
        cursor.execute("""
            SELECT a.id, d.name, d.specialization, a.appointment_date 
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = :patient_id
            ORDER BY a.appointment_date
        """, {'patient_id': session['patient_id']})
        appointments = cursor.fetchall()
        
        return render_template('patient_dashboard.html', 
                             doctors=doctors, 
                             appointments=appointments,
                             date=datetime)  # Pass datetime to template
    except Exception as e:
        flash('Error fetching data: ' + str(e), 'error')
        return redirect(url_for('patient_login'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/patient/appointments')
def patient_appointments():
    if 'user_type' not in session or session['user_type'] != 'patient':
        return redirect(url_for('patient_login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get upcoming appointments
        cursor.execute("""
            SELECT a.id, d.name as doctor_name, d.specialization, a.appointment_date
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = :patient_id AND a.appointment_date > SYSDATE
            ORDER BY a.appointment_date
        """, {'patient_id': session['patient_id']})
        upcoming_appointments = cursor.fetchall()
        
        # Get past appointments
        cursor.execute("""
            SELECT a.id, d.name as doctor_name, d.specialization, a.appointment_date
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.patient_id = :patient_id AND a.appointment_date <= SYSDATE
            ORDER BY a.appointment_date DESC
        """, {'patient_id': session['patient_id']})
        past_appointments = cursor.fetchall()
        
        # For this example, we'll just simulate cancelled appointments as empty
        cancelled_appointments = []
        
        return render_template('patient_appointments.html', 
                            upcoming_appointments=upcoming_appointments,
                            past_appointments=past_appointments,
                            cancelled_appointments=cancelled_appointments,
                            date=datetime)
    except Exception as e:
        flash('Error fetching appointments: ' + str(e), 'error')
        return redirect(url_for('patient_dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id):
    if 'user_type' not in session or session['user_type'] != 'patient':
        return redirect(url_for('patient_login'))
    
    if request.method == 'POST':
        appointment_date = request.form['appointment_date']
        
        conn = None
        cursor = None
        try:
            # Convert string to datetime
            appointment_datetime = datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M')
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if doctor is available at that time
            cursor.execute("""
                SELECT id FROM appointments 
                WHERE doctor_id = :doctor_id 
                AND appointment_date = TO_DATE(:appointment_date, 'YYYY-MM-DD HH24:MI')
            """, {
                'doctor_id': doctor_id,
                'appointment_date': appointment_date.replace('T', ' ')
            })
            
            if cursor.fetchone():
                flash('Doctor is not available at this time. Please choose another time.', 'error')
            else:
                # Book appointment
                cursor.execute("""
                    INSERT INTO appointments (id, doctor_id, patient_id, appointment_date, status)
                    VALUES (appointment_seq.NEXTVAL, :doctor_id, :patient_id, TO_DATE(:appointment_date, 'YYYY-MM-DD HH24:MI'), 'pending')
                """, {
                    'doctor_id': doctor_id,
                    'patient_id': session['patient_id'],
                    'appointment_date': appointment_date.replace('T', ' ')
                })
                conn.commit()
                flash('Appointment booked successfully!', 'success')
                return redirect(url_for('patient_dashboard'))
        except Exception as e:
            if conn:
                conn.rollback()
            flash('Error booking appointment: ' + str(e), 'error')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors WHERE id = :id", {'id': doctor_id})
        doctor = cursor.fetchone()
        
        if not doctor:
            flash('Doctor not found', 'error')
            return redirect(url_for('patient_dashboard'))
        
        return render_template('book_appointment.html', doctor=doctor)
    except Exception as e:
        flash('Error fetching doctor details: ' + str(e), 'error')
        return redirect(url_for('patient_dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/patient/profile', methods=['GET', 'POST'])
def patient_profile():
    if 'user_type' not in session or session['user_type'] != 'patient':
        return redirect(url_for('patient_login'))
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            # Get form type with validation
            form_type = request.form.get('form_type')
            if form_type not in ('personal', 'medical'):
                flash('Invalid form type submitted', 'error')
                return redirect(url_for('patient_profile'))
                
            if form_type == 'personal':
                # Process personal info update
                name = request.form.get('name', '').strip()
                email = request.form.get('email', '').strip()
                phone = request.form.get('phone', '').strip()
                
                # Validate required fields
                if not all([name, email, phone]):
                    flash('All personal information fields are required', 'error')
                    return redirect(url_for('patient_profile'))
                
                # Basic email validation
                if '@' not in email or '.' not in email.split('@')[-1]:
                    flash('Please enter a valid email address', 'error')
                    return redirect(url_for('patient_profile'))
                
                # Update personal info
                cursor.execute("""
                    UPDATE patients SET 
                    name = :name,
                    email = :email,
                    phone = :phone,
                    last_updated = SYSTIMESTAMP
                    WHERE id = :id
                """, {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'id': session['patient_id']
                })
                
                conn.commit()
                flash('Profile updated successfully!', 'success')
                session['patient_name'] = name  # Update session name
                
            elif form_type == 'medical':
                # Medical info (these fields can be optional)
                blood_type = request.form.get('blood_type', '').strip()
                allergies = request.form.get('allergies', '').strip()
                chronic_conditions = request.form.get('chronic_conditions', '').strip()
                medications = request.form.get('medications', '').strip()
                
                # Update medical info
                cursor.execute("""
                    UPDATE patients SET 
                    blood_type = :blood_type,
                    allergies = :allergies,
                    chronic_conditions = :chronic_conditions,
                    medications = :medications,
                    last_updated = SYSTIMESTAMP
                    WHERE id = :id
                """, {
                    'blood_type': blood_type,
                    'allergies': allergies,
                    'chronic_conditions': chronic_conditions,
                    'medications': medications,
                    'id': session['patient_id']
                })
                
                conn.commit()
                flash('Medical information updated successfully!', 'success')
        
        # Get current patient data (after update if POST or initial load if GET)
        cursor.execute("SELECT * FROM patients WHERE id = :id", {'id': session['patient_id']})
        patient_data = cursor.fetchone()
        
        if patient_data:
            # Convert to dict for easier access in template
            columns = [desc[0].lower() for desc in cursor.description]
            patient = dict(zip(columns, patient_data))
            return render_template('patient_profile.html', patient=patient)
        else:
            flash('Patient record not found', 'error')
            return redirect(url_for('patient_dashboard'))
            
    except Exception as e:
        if conn:
            conn.rollback()
        flash('Error: ' + str(e), 'error')
        return redirect(url_for('patient_dashboard'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)