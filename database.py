import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import hashlib

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'Divyas@123'),
    'database': os.environ.get('DB_NAME', 'fake_news_detection')
}

def create_connection():
    """Create a database connection and auto-create the database if needed."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        # If the database does not exist, create it automatically
        if getattr(e, 'errno', None) == 1049:
            try:
                temp_config = DB_CONFIG.copy()
                temp_config.pop('database', None)
                connection = mysql.connector.connect(**temp_config)
                cursor = connection.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
                connection.commit()
                cursor.close()
                connection.close()
                connection = mysql.connector.connect(**DB_CONFIG)
                if connection.is_connected():
                    return connection
            except Error as e2:
                print(f"Database creation error: '{e2}'")
                return None
        print(f"Error: '{e}'")
        return None

def column_exists(cursor, table_name, column_name):
    """Return True if a column exists in the specified table."""
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = %s AND table_name = %s AND column_name = %s",
        (DB_CONFIG['database'], table_name, column_name)
    )
    return cursor.fetchone()[0] > 0


def create_tables():
    """Create users and predictions tables if they don't exist."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'user',
                    registered_via VARCHAR(50) NOT NULL DEFAULT 'app',
                    policies_accepted BOOLEAN NOT NULL DEFAULT FALSE,
                    policies_accepted_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            if not column_exists(cursor, 'users', 'role'):
                cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'")
            if not column_exists(cursor, 'users', 'registered_via'):
                cursor.execute("ALTER TABLE users ADD COLUMN registered_via VARCHAR(50) NOT NULL DEFAULT 'app'")
            if not column_exists(cursor, 'users', 'policies_accepted'):
                cursor.execute("ALTER TABLE users ADD COLUMN policies_accepted BOOLEAN NOT NULL DEFAULT FALSE")
            if not column_exists(cursor, 'users', 'policies_accepted_at'):
                cursor.execute("ALTER TABLE users ADD COLUMN policies_accepted_at TIMESTAMP NULL")

            # Create predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    news_text TEXT NOT NULL,
                    prediction VARCHAR(10) NOT NULL,
                    confidence FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            if not column_exists(cursor, 'predictions', 'source_type'):
                cursor.execute("ALTER TABLE predictions ADD COLUMN source_type VARCHAR(20) DEFAULT 'text'")
            if not column_exists(cursor, 'predictions', 'source_url'):
                cursor.execute("ALTER TABLE predictions ADD COLUMN source_url VARCHAR(255) DEFAULT NULL")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    news_text TEXT NOT NULL,
                    source_type VARCHAR(20) DEFAULT 'text',
                    source_url VARCHAR(255) DEFAULT NULL,
                    prediction VARCHAR(10) NOT NULL,
                    confidence FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    subject VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    username VARCHAR(50) NOT NULL,
                    login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    token VARCHAR(255) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX (token),
                    INDEX (email)
                )
            """)

            # Create OTP table for password reset verification
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_reset_otp (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) NOT NULL,
                    otp VARCHAR(6) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX (email),
                    INDEX (otp)
                )
            """)

            connection.commit()
            ensure_admin_user()
            print("Tables created successfully.")
        except Error as e:
            print(f"Error creating tables: '{e}'")
        finally:
            cursor.close()
            connection.close()

def ensure_admin_user():
    """Create or update a database-backed admin account for the admin portal."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@1234')
            admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
            admin_password_hash = generate_password_hash(admin_password)

            cursor.execute("SELECT id FROM users WHERE username = %s", (admin_username,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE users SET email = %s, password = %s, role = 'admin', registered_via = 'admin' WHERE username = %s",
                    (admin_email, admin_password_hash, admin_username)
                )
            else:
                cursor.execute(
                    "INSERT INTO users (username, email, password, role, registered_via) VALUES (%s, %s, %s, 'admin', 'admin')",
                    (admin_username, admin_email, admin_password_hash)
                )
            connection.commit()
        except Error as e:
            print(f"Error ensuring admin user: '{e}'")
        finally:
            cursor.close()
            connection.close()


def register_user(username, email, password):
    """Register a new user."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Normalize email to lowercase for consistency
            email_lower = email.lower()
            cursor.execute("INSERT INTO users (username, email, password, registered_via) VALUES (%s, %s, %s, 'app')",
                         (username, email_lower, password))
            connection.commit()
            return True
        except Error as e:
            print(f"Error registering user: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def authenticate_user(username, password):
    """Authenticate a normal user using a securely stored password hash."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id, username, password FROM users WHERE username = %s AND role != 'admin'", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[2], password):
                return (user[0], user[1])
            return None
        except Error as e:
            print(f"Error authenticating user: '{e}'")
            return None
        finally:
            cursor.close()
            connection.close()


def authenticate_admin_user(username, password):
    """Authenticate an admin user using a securely stored password hash."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id, username, password FROM users WHERE username = %s AND role = 'admin'", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[2], password):
                return (user[0], user[1])
            return None
        except Error as e:
            print(f"Error authenticating admin user: '{e}'")
            return None
        finally:
            cursor.close()
            connection.close()


def get_user_by_email(email):
    """Retrieve a user by email address."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Normalize email to lowercase for case-insensitive lookup
            email_lower = email.lower()
            cursor.execute("SELECT id, username, email FROM users WHERE LOWER(email) = %s", (email_lower,))
            return cursor.fetchone()
        except Error as e:
            print(f"Error getting user by email: '{e}'")
            return None
        finally:
            cursor.close()
            connection.close()


def get_user_policy_status(user_id):
    """Get the policy acceptance status for a user."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT policies_accepted, policies_accepted_at FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'policies_accepted': bool(row[0]),
                    'policies_accepted_at': row[1]
                }
            return {'policies_accepted': False, 'policies_accepted_at': None}
        except Error as e:
            print(f"Error getting policy status: '{e}'")
            return {'policies_accepted': False, 'policies_accepted_at': None}
        finally:
            cursor.close()
            connection.close()


def update_user_policy_acceptance(user_id):
    """Persist the user's policy acceptance status in the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE users SET policies_accepted = TRUE, policies_accepted_at = NOW() WHERE id = %s",
                (user_id,)
            )
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating policy acceptance: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()
    return False


def get_admin_users():
    """Get users for the admin dashboard with prediction counts and activity."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.role, u.created_at,
                       COUNT(DISTINCT p.id) AS prediction_count,
                       MAX(p.created_at) AS last_activity
                FROM users u
                LEFT JOIN predictions p ON p.user_id = u.id
                WHERE u.role != 'admin' AND u.registered_via = 'app'
                GROUP BY u.id, u.username, u.email, u.role, u.created_at
                ORDER BY u.created_at DESC
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting admin users: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def record_login_history(user_id, username):
    """Record every successful login as a distinct history row with the server timestamp."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO login_history (user_id, username, login_time) VALUES (%s, %s, CURRENT_TIMESTAMP)",
                (user_id, username)
            )
            connection.commit()
            return True
        except Error as e:
            print(f"Error recording login history: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()


def get_login_history():
    """Get all login history entries for admin display."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT lh.id, lh.user_id, u.username, lh.login_time
                FROM login_history lh
                JOIN users u ON u.id = lh.user_id
                WHERE u.role != 'admin' AND u.registered_via = 'app'
                ORDER BY lh.login_time DESC
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting login history: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def get_prediction_activity():
    """Get all prediction activity for admin display."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT p.id, u.username, p.news_text, p.source_type, p.source_url, p.prediction, p.created_at
                FROM predictions p
                JOIN users u ON u.id = p.user_id
                WHERE u.role != 'admin' AND u.registered_via = 'app'
                ORDER BY p.created_at DESC
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"Error getting prediction activity: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def delete_user_account(user_id):
    """Delete a user and all related data from the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return False

            email = user[0]
            cursor.execute("DELETE FROM predictions WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM history WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM feedback WHERE user_id = %s", (user_id,))
            if email:
                email_lower = email.lower()
                cursor.execute("DELETE FROM password_reset_tokens WHERE LOWER(email) = %s", (email_lower,))
                cursor.execute("DELETE FROM password_reset_otp WHERE LOWER(email) = %s", (email_lower,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error deleting user account: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()


def create_password_reset_token(email, otp, expires_at):
    """Store a password reset OTP for an email."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            token_hash = hashlib.sha256(otp.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO password_reset_tokens (email, token, expires_at, used) VALUES (%s, %s, %s, FALSE)",
                (email, token_hash, expires_at)
            )
            connection.commit()
            return True
        except Error as e:
            print(f"Error creating password reset token: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def verify_password_reset_token(email, otp):
    """Verify an OTP for a password reset request."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            token_hash = hashlib.sha256(otp.encode()).hexdigest()
            cursor.execute(
                "SELECT id, email FROM password_reset_tokens WHERE email = %s AND token = %s AND used = FALSE AND expires_at > %s",
                (email, token_hash, datetime.utcnow())
            )
            return cursor.fetchone()
        except Error as e:
            print(f"Error verifying password reset token: '{e}'")
            return None
        finally:
            cursor.close()
            connection.close()

def mark_password_reset_token_used(token_id):
    """Mark a password reset token as used."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE password_reset_tokens SET used = TRUE WHERE id = %s", (token_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error marking password reset token used: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def update_password(email, password):
    """Update the password for a given user email."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Normalize email to lowercase for case-insensitive update
            email_lower = email.lower()
            cursor.execute("UPDATE users SET password = %s WHERE LOWER(email) = %s", (password, email_lower))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error updating password: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def save_prediction(user_id, news_text, prediction, confidence, source_type='text', source_url=None):
    """Save a prediction to the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SHOW COLUMNS FROM predictions LIKE 'source_type'")
            has_source_type = cursor.fetchone() is not None
            cursor.execute("SHOW COLUMNS FROM predictions LIKE 'source_url'")
            has_source_url = cursor.fetchone() is not None

            if has_source_type and has_source_url:
                cursor.execute(
                    "INSERT INTO predictions (user_id, news_text, source_type, source_url, prediction, confidence) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, news_text, source_type, source_url, prediction, confidence)
                )
            elif has_source_type:
                cursor.execute(
                    "INSERT INTO predictions (user_id, news_text, source_type, prediction, confidence) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, news_text, source_type, prediction, confidence)
                )
            else:
                cursor.execute(
                    "INSERT INTO predictions (user_id, news_text, prediction, confidence) VALUES (%s, %s, %s, %s)",
                    (user_id, news_text, prediction, confidence)
                )
            connection.commit()
            return True
        except Error as e:
            print(f"Error saving prediction: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def delete_prediction(prediction_id, user_id):
    """Delete a prediction from the database (only if it belongs to the user)."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM predictions WHERE id = %s AND user_id = %s",
                         (prediction_id, user_id))
            connection.commit()
            return cursor.rowcount > 0  # Return True if a row was deleted
        except Error as e:
            print(f"Error deleting prediction: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def save_feedback(user_id, subject, message):
    """Save user feedback to the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO feedback (user_id, subject, message) VALUES (%s, %s, %s)",
                         (user_id, subject, message))
            connection.commit()
            return True
        except Error as e:
            print(f"Error saving feedback: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def get_user_predictions(user_id):
    """Get prediction history for a user."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id, news_text, prediction, confidence, created_at FROM predictions WHERE user_id = %s ORDER BY created_at DESC",
                         (user_id,))
            predictions = cursor.fetchall()
            return predictions
        except Error as e:
            print(f"Error getting predictions: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def save_history_record(user_id, news_text, prediction, confidence, source_type='text', source_url=None):
    """Persist a detection history entry for a user in the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO history (user_id, news_text, source_type, source_url, prediction, confidence) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, news_text, source_type, source_url, prediction, confidence)
            )
            connection.commit()
            return True
        except Error as e:
            print(f"Error saving history record: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()


def get_history_records(user_id, search_query=None):
    """Get detailed history records for a user from the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            if search_query:
                query = "%" + search_query + "%"
                cursor.execute(
                    "SELECT id, news_text, source_type, source_url, prediction, confidence, created_at FROM history WHERE user_id = %s AND (news_text LIKE %s OR source_url LIKE %s) ORDER BY created_at DESC",
                    (user_id, query, query)
                )
            else:
                cursor.execute(
                    "SELECT id, news_text, source_type, source_url, prediction, confidence, created_at FROM history WHERE user_id = %s ORDER BY created_at DESC",
                    (user_id,)
                )
            records = cursor.fetchall()
            return records
        except Error as e:
            print(f"Error getting history records: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def delete_history_record(record_id, user_id):
    """Delete a history record from the database for the specified user."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM history WHERE id = %s AND user_id = %s", (record_id, user_id))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error deleting history record: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()


def get_global_statistics():
    """Get global statistics on predictions."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    prediction,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM predictions
                GROUP BY prediction
            """)
            stats = cursor.fetchall()
            return stats
        except Error as e:
            print(f"Error getting statistics: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()

def get_prediction_trend(user_id=None):
    """Get prediction trend over time for a specific user."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            if user_id:
                cursor.execute("""
                    SELECT
                        DATE(created_at) AS day,
                        prediction,
                        COUNT(*) AS count
                    FROM predictions
                    WHERE user_id = %s
                    GROUP BY day, prediction
                    ORDER BY day ASC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT
                        DATE(created_at) AS day,
                        prediction,
                        COUNT(*) AS count
                    FROM predictions
                    GROUP BY day, prediction
                    ORDER BY day ASC
                """)
            trend = cursor.fetchall()
            return trend
        except Error as e:
            print(f"Error getting trend: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def get_confidence_distribution(user_id=None):
    """Get confidence score distribution for a specific user."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            if user_id:
                cursor.execute("""
                    SELECT
                        CASE
                            WHEN confidence >= 0.9 THEN '90-100%'
                            WHEN confidence >= 0.7 THEN '70-89%'
                            WHEN confidence >= 0.5 THEN '50-69%'
                            ELSE '0-49%'
                        END as confidence_range,
                        COUNT(*) as count,
                        prediction
                    FROM predictions
                    WHERE user_id = %s
                    GROUP BY confidence_range, prediction
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT
                        CASE
                            WHEN confidence >= 0.9 THEN '90-100%'
                            WHEN confidence >= 0.7 THEN '70-89%'
                            WHEN confidence >= 0.5 THEN '50-69%'
                            ELSE '0-49%'
                        END as confidence_range,
                        COUNT(*) as count,
                        prediction
                    FROM predictions
                    GROUP BY confidence_range, prediction
                """)
            dist = cursor.fetchall()
            return dist
        except Error as e:
            print(f"Error getting confidence distribution: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def get_user_statistics(user_id):
    """Get statistics for a specific user."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    prediction,
                    COUNT(*) as count,
                    AVG(confidence) as avg_confidence
                FROM predictions
                WHERE user_id = %s
                GROUP BY prediction
            """, (user_id,))
            stats = cursor.fetchall()
            return stats
        except Error as e:
            print(f"Error getting user statistics: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def get_user_analytics_summary(user_id):
    """Get a compact summary of user analytics from the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_predictions,
                    SUM(CASE WHEN prediction = 'Fake' THEN 1 ELSE 0 END) AS fake_count,
                    SUM(CASE WHEN prediction = 'Real' THEN 1 ELSE 0 END) AS real_count,
                    AVG(confidence) AS average_confidence
                FROM predictions
                WHERE user_id = %s
            """, (user_id,))
            row = cursor.fetchone()
            total_predictions = int(row[0] or 0)
            fake_count = int(row[1] or 0)
            real_count = int(row[2] or 0)
            average_confidence = float(row[3] or 0.0)
            fake_percentage = round((fake_count / total_predictions) * 100, 2) if total_predictions else 0.0
            return {
                'total_predictions': total_predictions,
                'fake_count': fake_count,
                'real_count': real_count,
                'average_confidence': round(average_confidence * 100, 2),
                'fake_percentage': fake_percentage
            }
        except Error as e:
            print(f"Error getting user analytics summary: '{e}'")
            return {
                'total_predictions': 0,
                'fake_count': 0,
                'real_count': 0,
                'average_confidence': 0.0,
                'fake_percentage': 0.0
            }
        finally:
            cursor.close()
            connection.close()


def get_top_fake_patterns():
    """Get top patterns found in fake news."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    SUBSTR(news_text, 1, 50) as pattern,
                    COUNT(*) as occurrences,
                    AVG(confidence) as avg_confidence
                FROM predictions
                WHERE prediction = 'Fake'
                GROUP BY SUBSTR(news_text, 1, 50)
                ORDER BY occurrences DESC
                LIMIT 10
            """)
            patterns = cursor.fetchall()
            return patterns
        except Error as e:
            print(f"Error getting fake patterns: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()


def get_heatmap_data():
    """Get data for heatmap visualization (time and prediction distribution)."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    DATE_FORMAT(created_at, '%H') as hour,
                    DAYNAME(created_at) as day,
                    prediction,
                    COUNT(*) as count
                FROM predictions
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY hour, day, prediction
                ORDER BY created_at DESC
            """)
            heatmap_data = cursor.fetchall()
            return heatmap_data
        except Error as e:
            print(f"Error getting heatmap data: '{e}'")
            return []
        finally:
            cursor.close()
            connection.close()

def get_total_predictions():
    """Get total number of predictions made."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM predictions")
            count = cursor.fetchone()[0]
            return count or 0
        except Error as e:
            print(f"Error getting total predictions: '{e}'")
            return 0
        finally:
            cursor.close()
            connection.close()


def get_prediction_counts():
    """Get total fake and real prediction counts."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN prediction = 'Fake' THEN 1 ELSE 0 END) AS fake_count,
                    SUM(CASE WHEN prediction = 'Real' THEN 1 ELSE 0 END) AS real_count,
                    COUNT(*) AS total_count
                FROM predictions
            """)
            row = cursor.fetchone()
            return {
                'fake': row[0] or 0,
                'real': row[1] or 0,
                'total': row[2] or 0
            }
        except Error as e:
            print(f"Error getting prediction counts: '{e}'")
            return {'fake': 0, 'real': 0, 'total': 0}
        finally:
            cursor.close()
            connection.close()


def get_total_users():
    """Get total registered users."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username != 'admin'")
            return cursor.fetchone()[0] or 0
        except Error as e:
            print(f"Error getting total users: '{e}'")
            return 0
        finally:
            cursor.close()
            connection.close()


def get_total_logins():
    """Get total login history entries."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM login_history")
            return cursor.fetchone()[0] or 0
        except Error as e:
            if getattr(e, 'errno', None) == 1146:
                return 0
            print(f"Error getting total logins: '{e}'")
            return 0
        finally:
            cursor.close()
            connection.close()


def get_fake_percentage():
    """Get percentage of fake news detected."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN prediction = 'Fake' THEN 1 ELSE 0 END) as fake_count,
                    COUNT(*) as total_count
                FROM predictions
            """)
            result = cursor.fetchone()
            if result[1] > 0:
                percentage = (result[0] / result[1]) * 100
                return round(percentage, 2)
            return 0
        except Error as e:
            print(f"Error getting fake percentage: '{e}'")
            return 0
        finally:
            cursor.close()
            connection.close()

def create_password_reset_otp(email, otp, expires_at):
    """Store a password reset OTP for an email and invalidate older codes."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Normalize email to lowercase for consistency
            email_lower = email.lower()
            cursor.execute("DELETE FROM password_reset_otp WHERE LOWER(email) = %s", (email_lower,))
            cursor.execute(
                "INSERT INTO password_reset_otp (email, otp, expires_at, verified) VALUES (%s, %s, %s, FALSE)",
                (email_lower, otp, expires_at)
            )
            connection.commit()
            return True
        except Error as e:
            print(f"Error creating password reset OTP: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def get_password_reset_otp(email, otp):
    """Retrieve and verify a password reset OTP with explicit status."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Normalize email to lowercase for case-insensitive lookup
            email_lower = email.lower()
            cursor.execute(
                "SELECT id, expires_at, verified FROM password_reset_otp WHERE LOWER(email) = %s AND otp = %s",
                (email_lower, otp)
            )
            row = cursor.fetchone()
            if not row:
                return {"status": "invalid"}

            otp_id, expires_at, verified = row
            if verified:
                return {"status": "used"}
            if expires_at < datetime.utcnow():
                return {"status": "expired"}
            return {"status": "valid", "id": otp_id}
        except Error as e:
            print(f"Error getting password reset OTP: '{e}'")
            return {"status": "error"}
        finally:
            cursor.close()
            connection.close()

def mark_otp_verified(otp_id):
    """Mark an OTP as verified."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE password_reset_otp SET verified = TRUE WHERE id = %s", (otp_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error marking OTP verified: '{e}'")
            return False
        finally:
            cursor.close()
            connection.close()

def delete_expired_otps():
    """Delete expired OTPs from the database."""
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM password_reset_otp WHERE expires_at < %s", (datetime.utcnow(),))
            connection.commit()
            return cursor.rowcount
        except Error as e:
            print(f"Error deleting expired OTPs: '{e}'")
            return 0
        finally:
            cursor.close()
            connection.close()