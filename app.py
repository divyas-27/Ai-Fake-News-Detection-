from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
from functools import wraps
import os
from dotenv import load_dotenv
import re
import requests
import hashlib
import json 
import smtplib
from email.message import EmailMessage
from secrets import randbelow
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import (create_tables, ensure_admin_user, register_user, authenticate_user, authenticate_admin_user, get_user_by_email, get_admin_users,
                     record_login_history, get_login_history, get_prediction_activity, get_total_users, get_total_logins,
                     get_prediction_counts, delete_user_account, create_password_reset_token,
                     get_user_policy_status, update_user_policy_acceptance,
                     verify_password_reset_token, mark_password_reset_token_used, update_password,
                     save_prediction, save_history_record, get_user_predictions, get_history_records, delete_prediction,
                     delete_history_record, get_global_statistics, get_prediction_trend, get_confidence_distribution,
                     get_user_statistics, get_user_analytics_summary, get_top_fake_patterns, get_heatmap_data,
                     get_total_predictions, get_fake_percentage, save_feedback,
                     create_password_reset_otp, get_password_reset_otp, mark_otp_verified, delete_expired_otps)
from model import predict_news, pac_model, tfidf_vectorizer
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# SQLAlchemy configuration for history support
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+mysqlconnector://{quote_plus(os.environ.get('DB_USER', 'root'))}:{quote_plus(os.environ.get('DB_PASSWORD', 'Divyas@123'))}@{quote_plus(os.environ.get('DB_HOST', 'localhost'))}/{quote_plus(os.environ.get('DB_NAME', 'fake_news_detection'))}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_url(url):
    if not url:
        return None

    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'https://' + url

        response = requests.get(url, timeout=12, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        html = response.text

        try:
            from newspaper import Article
            article = Article(url)
            article.download(input_html=html)
            article.parse()
            text = article.text or ''
        except Exception:
            text = ''

        if not text or len(text) < 100:
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'svg', 'button']):
                tag.decompose()

            article_body = soup.find('article') or soup.find('main') or soup.find('section') or soup.find('div', {'class': lambda x: x and 'article' in x.lower()})
            paragraphs = []
            if article_body:
                paragraphs = [p.get_text(' ', strip=True) for p in article_body.find_all('p') if p.get_text(strip=True)]
            if not paragraphs:
                paragraphs = [p.get_text(' ', strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]

            text = '\n\n'.join(paragraphs)

        if not text:
            return None

        return text.strip()
    except Exception:
        return None


def hash_password(password):
    """Hash password securely using Werkzeug."""
    return generate_password_hash(password)

def generate_otp():
    """Generate a random 6-digit OTP."""
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def is_valid_email(email):
    """Validate an email format using a more comprehensive regex pattern."""
    # Pattern matches standard email formats: username@domain.extension
    # Allows common special characters in the local part (before @)
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def is_strong_password(password):
    """Enforce strong password rules."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Please log in as admin to access the admin dashboard.', 'error')
            return redirect(url_for('admin_login'))
        return view_func(*args, **kwargs)
    return wrapped_view

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            user = authenticate_user(username, password)
            if user:
                session.clear()
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['is_admin'] = False
                record_login_history(user[0], user[1])

                policy_status = get_user_policy_status(user[0])
                if policy_status.get('policies_accepted'):
                    session['privacy_policy_pending'] = False
                    return redirect(url_for('dashboard'))

                session['privacy_policy_pending'] = True
                return redirect(url_for('accept_policies'))
            else:
                flash('Invalid username or password', 'error')
        except Exception as e:
            print(f"Login error: {e}")
            flash('Database connection error. Please try again later.', 'error')

    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        ensure_admin_user()
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_user = authenticate_admin_user(username, password)

        if admin_user:
            session.clear()
            session['user_id'] = admin_user[0]
            session['username'] = admin_user[1]
            session['is_admin'] = True
            record_login_history(admin_user[0], admin_user[1])
            flash('Admin login successful.', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid admin credentials.', 'error')

    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip().lower()
        password = hash_password(request.form['password'])

        # Validate username - no spaces allowed
        if not username:
            flash('Please enter a username.', 'error')
            return redirect(url_for('register'))
        
        if ' ' in username:
            flash('Username cannot contain spaces.', 'error')
            return redirect(url_for('register'))

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('register'))

        try:
            if register_user(username, email, password):
                session.clear()
                flash('Registration successful! Please log in to continue.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Username or email may already exist.', 'error')
        except Exception as e:
            print(f"Registration error: {e}")
            flash('Database connection error. Please ensure MySQL is running.', 'error')

    return render_template('register.html')

@app.route('/privacy-policy')
def privacy_policy():
    """Redirect privacy policy requests to the policy acceptance page for first-time logins."""
    if 'user_id' in session:
        return redirect(url_for('accept_policies'))
    return redirect(url_for('login'))


@app.route('/privacy-policy/accept', methods=['POST'])
def accept_privacy_policy():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        if update_user_policy_acceptance(session['user_id']):
            session['privacy_policy_pending'] = False
            session['policies_accepted'] = True
            session.modified = True
            flash('Privacy policy accepted successfully.', 'success')
            return redirect(url_for('dashboard'))
    except Exception as exc:
        print(f'Policy acceptance error: {exc}')

    flash('Unable to save policy acceptance. Please try again.', 'error')
    return redirect(url_for('accept_policies'))

@app.route('/terms-conditions')
def terms_conditions():
    """Redirect to accept policies page (all content is on one page)."""
    if 'user_id' in session or 'pending_user' in session:
        return redirect(url_for('accept_policies'))
    return redirect(url_for('login'))

@app.route('/accept-policies', methods=['GET', 'POST'])
def accept_policies():
    """Handle policy acceptance after a user's first login."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    policy_status = get_user_policy_status(session['user_id'])
    if policy_status.get('policies_accepted'):
        session['privacy_policy_pending'] = False
        session['policies_accepted'] = True
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        privacy_accept = request.form.get('privacy_accept')
        terms_accept = request.form.get('terms_accept')
        data_accept = request.form.get('data_accept')

        if privacy_accept and terms_accept and data_accept:
            try:
                if update_user_policy_acceptance(session['user_id']):
                    session['privacy_policy_pending'] = False
                    session['policies_accepted'] = True
                    session.modified = True
                    flash('✓ Policies accepted successfully. You can now continue to the dashboard.', 'success')
                    return redirect(url_for('dashboard'))

                flash('Unable to save policy acceptance. Please try again.', 'error')
            except Exception as exc:
                print(f'Policy acceptance error: {exc}')
                flash('Unable to save policy acceptance. Please try again.', 'error')
        else:
            flash('Please accept all policies to continue.', 'error')

    return render_template('accept_policies.html')

def send_reset_email(recipient_email, token):
    """Send password reset email with OTP."""
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_username = os.environ.get('SMTP_USERNAME')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    email_from = os.environ.get('EMAIL_FROM', smtp_username)

    # If SMTP is not configured, log to console (for development/testing)
    if not smtp_server or not smtp_username or not smtp_password:
        print("=" * 60)
        print("EMAIL SERVICE NOT CONFIGURED - OTP FOR DEVELOPMENT")
        print("=" * 60)
        print(f"Recipient: {recipient_email}")
        print(f"OTP Code: {token}")
        print(f"Valid for: 10 minutes")
        print("=" * 60)
        print("\nTo enable email sending:")
        print("Set environment variables:")
        print("  SMTP_SERVER=smtp.gmail.com (or your SMTP server)")
        print("  SMTP_PORT=587")
        print("  SMTP_USERNAME=your-email@gmail.com")
        print("  SMTP_PASSWORD=your-app-password")
        print("  EMAIL_FROM=your-email@gmail.com (optional)")
        print("=" * 60)
        return True  # Return True to allow verification flow with console OTP

    message = EmailMessage()
    message['Subject'] = 'AI Fake News Detection - Password Reset Code'
    message['From'] = email_from
    message['To'] = recipient_email
    message.set_content(
        f"Hello,\n\nWe received a request to reset your password for AI Fake News Detection.\n\n"
        f"Your verification code is: {token}\n\n"
        f"Please enter this code on the verification page to reset your password.\n\n"
        f"This code will expire in 10 minutes.\n\n"
        f"If you did not request a password reset, you can ignore this email.\n\n"
        f"Best regards,\n"
        f"AI Fake News Detection Team"
    )

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_username, smtp_password)
            smtp.send_message(message)
            print(f"✓ Password reset email sent successfully to {recipient_email}")
            return True
    except Exception as e:
        print(f"✗ Error sending reset email: {e}")
        # Still return True to allow console-based testing
        print(f"Console OTP for testing: {token}")
        return True

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your email address.', 'error')
            return redirect(url_for('reset_password'))

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('reset_password'))

        user = get_user_by_email(email)
        if not user:
            flash('No account found for that email address.', 'error')
            return redirect(url_for('reset_password'))

        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        if create_password_reset_otp(email, otp, expires_at):
            if not send_reset_email(email, otp):
                flash('Error generating verification code. Please try again.', 'error')
                return redirect(url_for('reset_password'))
        else:
            flash('Unable to generate a verification code right now. Please try again later.', 'error')
            return redirect(url_for('reset_password'))

        session['reset_email'] = email
        flash('✓ Verification code has been sent! Check your email or the console for the code.', 'success')
        return redirect(url_for('verify_otp'))

    return render_template('reset_password.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        otp = request.form.get('otp', '').strip()

        if not email:
            flash('Please enter your email address.', 'error')
            return redirect(url_for('verify_otp'))

        if not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('verify_otp'))

        if not otp:
            flash('Please enter the OTP code sent to your email.', 'error')
            return redirect(url_for('verify_otp'))

        if len(otp) != 6 or not otp.isdigit():
            flash('OTP must be a 6-digit number.', 'error')
            return redirect(url_for('verify_otp'))

        otp_data = get_password_reset_otp(email, otp)
        if otp_data.get('status') == 'valid':
            if mark_otp_verified(otp_data['id']):
                session['verified_email'] = email
                flash('OTP verified successfully. Please create a new password.', 'success')
                return redirect(url_for('reset_password_verified'))
            flash('Error verifying OTP. Please try again.', 'error')
            return redirect(url_for('verify_otp'))

        if otp_data.get('status') == 'expired':
            flash('The OTP has expired. Please request a new verification code.', 'error')
        elif otp_data.get('status') == 'used':
            flash('This OTP has already been used. Please request a new verification code.', 'error')
        else:
            flash('Incorrect OTP. Please check the code and try again.', 'error')
        return redirect(url_for('verify_otp'))

    email = session.get('reset_email', '')
    return render_template('verify_otp.html', email=email)

@app.route('/reset-password-new', methods=['GET', 'POST'])
def reset_password_verified():
    # Check if user has verified OTP
    email = session.get('verified_email')
    if not email:
        flash('Please verify your email first.', 'error')
        return redirect(url_for('reset_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            flash('Please enter and confirm your new password.', 'error')
            return redirect(url_for('reset_password_verified'))

        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('reset_password_verified'))

        if not is_strong_password(new_password):
            flash('Password must be at least 8 characters long and include uppercase, lowercase, a number, and a special character.', 'error')
            return redirect(url_for('reset_password_verified'))

        hashed_password = hash_password(new_password)
        if update_password(email, hashed_password):
            session.pop('verified_email', None)
            session.pop('reset_email', None)
            flash('Your password has been reset successfully. Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Unable to reset your password. Please try again.', 'error')
            return redirect(url_for('reset_password_verified'))

    return render_template('reset_password_with_otp.html', email=email)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    predictions = get_user_predictions(session['user_id'])
    total_predictions = len(predictions)
    fake_count = sum(1 for prediction in predictions if prediction[2] == 'Fake')
    real_count = sum(1 for prediction in predictions if prediction[2] == 'Real')
    last_prediction = predictions[0][4] if predictions else None

    return render_template(
        'dashboard.html',
        predictions=predictions,
        total_predictions=total_predictions,
        fake_count=fake_count,
        real_count=real_count,
        last_prediction=last_prediction
    )


@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search', '').strip()
    records = get_history_records(session['user_id'], search_query=search if search else None)

    return render_template('history.html', records=records, search=search)


@app.route('/history/delete/<int:record_id>', methods=['POST'])
def delete_history_route(record_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    success = delete_history_record(record_id, session['user_id'])
    if success:
        flash('History record deleted successfully.', 'success')
    else:
        flash('Unable to delete history record.', 'error')

    return redirect(url_for('history'))

@app.route('/delete_prediction/<int:prediction_id>', methods=['POST'])
def delete_prediction_route(prediction_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    success = delete_prediction(prediction_id, session['user_id'])

    if success:
        flash('Prediction deleted successfully.', 'success')
    else:
        flash('Failed to delete prediction or prediction not found.', 'error')

    return redirect(url_for('dashboard'))

@app.route('/test')
def test():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    sample_texts = [
        {
            'title': 'Fake news example',
            'text': 'Fake news article says a celebrity discovered a real unicorn. Hoax report claims the ocean turned green overnight. Scientists secretly cloned the president using alien technology. Urgent warning: eating chocolate every day will make you immortal. Shocking text reveals hidden messages embedded in everyday traffic lights.'
        },
        {
            'title': 'Real news example',
            'text': 'Government announces a new tax policy for the next year. City council approves a new park for families. Local hospital opens a new pediatric wing with state-of-the-art equipment. University researchers publish a study showing environmental benefits of clean energy. Tech company launches affordable internet access programs for rural communities.'
        }
    ]
    return render_template('test.html', samples=sample_texts)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        news_text = ""

        # Check if text was entered directly
        if 'news_text' in request.form and request.form['news_text'].strip():
            news_text = request.form['news_text']
        # Check if file was uploaded
        elif 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Read the file content
                with open(filepath, 'r', encoding='utf-8') as f:
                    news_text = f.read()

                # Remove the uploaded file after processing
                os.remove(filepath)
            else:
                flash('Invalid file type. Please upload a .txt file.', 'error')
                return redirect(url_for('predict'))

        if news_text:
            # Make prediction
            prediction, confidence, reasons = predict_news(news_text, pac_model, tfidf_vectorizer)

            # Persist prediction and append to user history in the database
            save_prediction(session['user_id'], news_text[:500], prediction, confidence)
            save_history_record(session['user_id'], news_text[:500], prediction, confidence, source_type='text')

            return render_template('result.html', prediction=prediction, confidence=round(confidence * 100, 2), news_text=news_text[:200] + '...' if len(news_text) > 200 else news_text, reasons=reasons)
        else:
            flash('Please enter news text or upload a file.', 'error')

    return render_template('predict.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/analytics')
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    analytics_summary = get_user_analytics_summary(session['user_id'])
    user_stats = get_user_statistics(session['user_id'])

    return render_template('analytics.html',
                         total_predictions=analytics_summary['total_predictions'],
                         fake_percentage=analytics_summary['fake_percentage'],
                         user_stats=user_stats,
                         analytics_summary=analytics_summary)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_stats = get_user_statistics(session['user_id'])
    total_predictions = len(get_user_predictions(session['user_id']))
    fake_count = sum(1 for prediction in get_user_predictions(session['user_id']) if prediction[2] == 'Fake')
    real_count = total_predictions - fake_count

    return render_template('profile.html', user_stats=user_stats, total_predictions=total_predictions, fake_count=fake_count, real_count=real_count)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if subject and message:
            save_feedback(session['user_id'], subject, message)
            flash('Thank you! Your feedback has been submitted.', 'success')
            return redirect(url_for('feedback'))
        else:
            flash('Please provide both a subject and a feedback message.', 'error')

    return render_template('feedback.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    total_predictions = get_total_predictions()
    fake_percentage = get_fake_percentage()
    global_stats = get_global_statistics()
    prediction_counts = get_prediction_counts()
    total_users = get_total_users()
    total_logins = get_total_logins()
    
    return render_template('admin_dashboard.html',
                         total_predictions=total_predictions,
                         fake_percentage=fake_percentage,
                         global_stats=global_stats,
                         total_users=total_users,
                         total_logins=total_logins,
                         prediction_counts=prediction_counts)

@app.route('/api/admin/users')
@admin_required
def api_admin_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    users = get_admin_users()
    user_payload = []
    for user in users:
        user_id, username, email, role, created_at, prediction_count, last_activity = user
        user_payload.append({
            'id': user_id,
            'username': username,
            'email': email,
            'role': role,
            'createdAt': created_at.strftime('%Y-%m-%d %H:%M') if created_at else '-',
            'joinDate': created_at.strftime('%Y-%m-%d') if created_at else '-',
            'lastActivity': last_activity.strftime('%Y-%m-%d %H:%M') if last_activity else '-',
            'predictions': prediction_count or 0,
            'status': 'active' if (prediction_count or 0) > 0 else 'inactive'
        })

    return jsonify(user_payload)

@app.route('/api/admin/login-history')
@admin_required
def api_login_history():
    history = get_login_history()
    history_payload = []
    for entry in history:
        history_payload.append({
            'id': entry[0],
            'user_id': entry[1],
            'username': entry[2] or 'Unknown',
            'login_time': entry[3].strftime('%Y-%m-%d %H:%M:%S') if entry[3] else '-'
        })
    return jsonify(history_payload)

@app.route('/api/admin/predictions')
@admin_required
def api_prediction_activity():
    records = get_prediction_activity()
    payload = []
    for record in records:
        payload.append({
            'id': record[0],
            'username': record[1] or 'Unknown',
            'news_text': record[2] or (record[4] or '-'),
            'source_type': record[3] or 'text',
            'source_url': record[4] or '-',
            'prediction': record[5] or '-',
            'created_at': record[6].strftime('%Y-%m-%d %H:%M:%S') if record[6] else '-'
        })
    return jsonify(payload)

@app.route('/api/admin/users/delete', methods=['POST'])
@admin_required
def api_delete_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User id is required'}), 400

    deleted = delete_user_account(int(user_id))
    if deleted:
        return jsonify({'success': True, 'message': 'User deleted successfully'})

    return jsonify({'error': 'User could not be deleted'}), 404

@app.route('/api/analytics/trend')
def api_trend():
    """API endpoint for prediction trend data."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    trend = get_prediction_trend(session['user_id'])
    trend_data = defaultdict(lambda: {'Fake': 0, 'Real': 0})
    
    for day, prediction, count in trend:
        trend_data[str(day)][prediction] = count
    
    return jsonify(dict(trend_data))

@app.route('/api/analytics/confidence')
def api_confidence():
    """API endpoint for confidence distribution."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conf_dist = get_confidence_distribution(session['user_id'])
    confidence_data = {}
    
    for conf_range, count, prediction in conf_dist:
        key = f"{prediction}_{conf_range}"
        confidence_data[key] = count
    
    return jsonify(confidence_data)

@app.route('/api/analytics/heatmap')
def api_heatmap():
    """API endpoint for heatmap data."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    heatmap_data = get_heatmap_data()
    heatmap_dict = {}
    
    for hour, day, prediction, count in heatmap_data:
        key = f"{day}_{hour}"
        if key not in heatmap_dict:
            heatmap_dict[key] = {'Fake': 0, 'Real': 0}
        heatmap_dict[key][prediction] = count
    
    return jsonify(heatmap_dict)

@app.route('/api/predict-voice', methods=['POST'])
def api_predict_voice():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    voice_text = data.get('voice_text', '').strip()

    if not voice_text:
        return jsonify({'error': 'No voice text provided'}), 400

    prediction, confidence, reasons = predict_news(voice_text, pac_model, tfidf_vectorizer)
    save_prediction(session['user_id'], voice_text[:500], prediction, confidence, source_type='voice')
    save_history_record(session['user_id'], voice_text[:500], prediction, confidence, source_type='voice')

    return jsonify({
        'prediction': prediction,
        'confidence': round(confidence * 100, 2),
        'text': voice_text[:200] + '...' if len(voice_text) > 200 else voice_text,
        'reasons': reasons,
        'source_type': 'voice'
    })

@app.route('/api/predict-url', methods=['POST'])
def api_predict_url():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    article_url = data.get('url', '').strip()
    if not article_url:
        return jsonify({'error': 'No URL provided'}), 400

    article_text = extract_text_from_url(article_url)
    if not article_text:
        return jsonify({'error': 'Unable to extract article text from that URL'}), 422

    prediction, confidence, reasons = predict_news(article_text, pac_model, tfidf_vectorizer)
    save_prediction(session['user_id'], article_text[:500], prediction, confidence, source_type='url', source_url=article_url)
    save_history_record(session['user_id'], article_text[:500], prediction, confidence, source_type='url', source_url=article_url)

    return jsonify({
        'prediction': prediction,
        'confidence': round(confidence * 100, 2),
        'text': article_text[:200] + '...' if len(article_text) > 200 else article_text,
        'reasons': reasons,
        'source_type': 'url',
        'source_url': article_url
    })

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint for real-time prediction."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    news_text = data.get('text', '').strip()
    
    if not news_text:
        return jsonify({'error': 'No text provided'}), 400
    
    prediction, confidence, reasons = predict_news(news_text, pac_model, tfidf_vectorizer)
    
    save_prediction(session['user_id'], news_text[:500], prediction, confidence, source_type='text')
    save_history_record(session['user_id'], news_text[:500], prediction, confidence, source_type='text')
    
    return jsonify({
        'prediction': prediction,
        'confidence': round(confidence * 100, 2),
        'text': news_text[:200] + '...' if len(news_text) > 200 else news_text,
        'reasons': reasons,
        'source_credibility': 'Pending verification'

    })


@app.errorhandler(Exception)
def handle_api_exception(e):
    if request.path.startswith('/api/'):
        if isinstance(e, HTTPException):
            return jsonify({'error': e.description}), e.code
        return jsonify({'error': str(e)}), 500
    if isinstance(e, HTTPException):
        return e
    raise e

if __name__ == '__main__':
    # Create database tables
    print("=" * 70)
    print("INITIALIZING AI FAKE NEWS DETECTION APPLICATION")
    print("=" * 70)
    
    print("\n📊 Database Configuration:")
    print("  - host: localhost")
    print("  - user: root")
    print("  - password: Divyas@123")
    print("  - database: fake_news_db")
    
    print("\n🔄 Initializing database connection...")
    try:
        create_tables()
        print("✓ Database tables created/verified successfully!")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
    
    print("\n📧 Email Configuration (for password reset):")
    if os.environ.get('SMTP_SERVER'):
        print(f"✓ Email service configured: {os.environ.get('SMTP_SERVER')}")
    else:
        print("ℹ Email service NOT configured")
        print("  OTP codes will be displayed in the console for development")
        print("  To enable real email sending, set environment variables:")
        print("    SMTP_SERVER=smtp.gmail.com")
        print("    SMTP_PORT=587")
        print("    SMTP_USERNAME=your-email@gmail.com")
        print("    SMTP_PASSWORD=your-app-password")
        print("    EMAIL_FROM=your-email@gmail.com (optional)")
    
    print("\n" + "=" * 70)
    print("🚀 Starting Flask Application...")
    print("🌐 Open: http://localhost:5000")
    print("=" * 70 + "\n")
    
    app.run(debug=True)