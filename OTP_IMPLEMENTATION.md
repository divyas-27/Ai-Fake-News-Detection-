# OTP Verification System for Password Reset

## Overview
This implementation adds a secure OTP (One-Time Password) verification system for password reset functionality to the AI Fake News Detection application.

## Features

### 1. **OTP Generation & Storage**
   - Generates a random 6-digit numeric OTP
   - OTPs are stored in the `password_reset_otp` database table
   - Each OTP expires after 1 hour
   - OTPs can only be used once (marked as verified after successful verification)

### 2. **Email Notification**
   - Sends the 6-digit OTP code via email to the user's registered email address
   - Uses SMTP configuration from environment variables
   - Includes clear instructions on the email

### 3. **Secure Password Reset Flow**
   - User enters email → OTP is generated and sent
   - User enters OTP on verification page
   - Upon successful OTP verification, user can set a new password
   - Passwords are hashed using SHA-256
   - Automatic redirect to login page after successful reset

## Flow Diagram

```
User Requests Password Reset
           ↓
    Enters Email Address
           ↓
    System Generates 6-digit OTP
           ↓
    OTP Sent via Email
           ↓
    User Receives Email with OTP
           ↓
    User Enters OTP on Verification Page
           ↓
    [OTP Valid?] → Yes → Mark OTP as Verified
           ↓              ↓
          No         User Sets New Password
           ↓              ↓
    Show Error      Password Hashed & Updated
    (Max 3 attempts)    ↓
           ↓        Redirect to Login Page
    Prompt to request new code or retry

```

## Routes Created

### 1. `/reset-password` (POST/GET)
   - **Purpose**: Initial password reset request
   - **GET**: Displays password reset form asking for email
   - **POST**: 
     - Accepts email address
     - Generates 6-digit OTP
     - Sends OTP via email
     - Stores OTP in database with 1-hour expiration
     - Redirects to OTP verification page
   - **Template**: `reset_password.html`

### 2. `/verify-otp` (POST/GET)
   - **Purpose**: OTP verification
   - **GET**: Displays OTP entry form
   - **POST**:
     - Accepts email and 6-digit OTP
     - Validates OTP format (must be exactly 6 digits)
     - Checks OTP against database
     - Validates OTP hasn't expired
     - Marks OTP as verified if valid
     - Redirects to password reset page upon success
   - **Template**: `verify_otp.html`

### 3. `/reset-password-new` (POST/GET)
   - **Purpose**: Password reset after OTP verification
   - **GET**: Displays new password form
   - **POST**:
     - Accepts new password and confirmation
     - Validates password length (minimum 6 characters)
     - Checks passwords match
     - Hashes password using SHA-256
     - Updates password in database
     - Cleans up session data
     - Redirects to login page
   - **Template**: `reset_password_with_otp.html`

## Templates Created

### 1. `verify_otp.html`
   - Modern, responsive design with gradient background
   - Input field for 6-digit OTP with numeric input mode
   - Email field (auto-filled from session)
   - Messages for success/error feedback
   - Option to request new code or return to login
   - Features:
     - Numeric-only input with maxlength="6"
     - Pattern validation for 6 digits
     - Clean, modern styling with gradient background
     - Responsive design for mobile devices

### 2. `reset_password_with_otp.html`
   - Form to set new password after OTP verification
   - Fields for:
     - New Password (minimum 6 characters)
     - Confirm Password
   - Messages for success/error feedback
   - Link back to login page
   - Features:
     - Password strength indication
     - Confirmation field to prevent typos
     - Clear error messages

## Database Schema

### Table: `password_reset_otp`
```sql
CREATE TABLE password_reset_otp (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    expires_at DATETIME NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (email),
    INDEX (otp)
)
```

**Fields**:
- `id`: Primary key
- `email`: User's email address
- `otp`: 6-digit OTP code
- `expires_at`: OTP expiration timestamp (1 hour from creation)
- `verified`: Boolean flag indicating if OTP has been used
- `created_at`: Timestamp of OTP creation

## Database Functions (in `database.py`)

### 1. `create_password_reset_otp(email, otp, expires_at)`
   - Creates a new OTP record in the database
   - Parameters:
     - `email`: User's email address
     - `otp`: 6-digit OTP code
     - `expires_at`: DateTime object for expiration
   - Returns: `True` if successful, `False` otherwise

### 2. `get_password_reset_otp(email, otp)`
   - Retrieves and validates an OTP
   - Checks if OTP exists, is not expired, and hasn't been verified
   - Parameters:
     - `email`: User's email address
     - `otp`: 6-digit OTP code to verify
   - Returns: Tuple `(otp_id, email, expires_at)` if valid, `None` otherwise

### 3. `mark_otp_verified(otp_id)`
   - Marks an OTP as verified (used)
   - Prevents reuse of the same OTP
   - Parameters:
     - `otp_id`: ID of the OTP record
   - Returns: `True` if successful, `False` otherwise

### 4. `delete_expired_otps()`
   - Cleans up expired OTP records
   - Can be called periodically to maintain database hygiene
   - Returns: Number of records deleted

## Helper Functions (in `app.py`)

### 1. `generate_otp()`
   - Generates a random 6-digit OTP
   - Returns: String of 6 random digits (e.g., "123456")
   - Used for each password reset request

### 2. `send_reset_email(recipient_email, otp)`
   - Sends OTP via email to user
   - Requires SMTP configuration in environment variables:
     - `SMTP_SERVER`: SMTP server address
     - `SMTP_PORT`: SMTP port (default: 587)
     - `SMTP_USERNAME`: SMTP username
     - `SMTP_PASSWORD`: SMTP password
     - `EMAIL_FROM`: Sender email (optional, defaults to SMTP_USERNAME)
   - Returns: `True` if sent successfully, `False` otherwise

## Session Management

The application uses Flask sessions to store temporary data:

1. **`session['reset_email']`**: 
   - Stores user's email during password reset process
   - Used to pre-fill the email field in OTP verification form
   - Cleared after successful password reset

2. **`session['verified_email']`**:
   - Stores verified email after successful OTP verification
   - Ensures user has verified OTP before setting new password
   - Cleared after password update

## Security Features

1. **OTP Expiration**: Each OTP expires after 1 hour
2. **Single-Use OTPs**: OTPs can only be used once
3. **Email Verification**: Ensures user has access to registered email
4. **Password Hashing**: Passwords hashed with SHA-256
5. **Input Validation**: 
   - OTP must be exactly 6 digits
   - Password minimum length: 6 characters
   - Password confirmation required
6. **Session-Based Verification**: Multi-step verification prevents unauthorized password resets
7. **Error Messages**: Generic messages don't reveal whether email exists (privacy)

## Implementation Checklist

✅ Database OTP table created
✅ OTP database functions implemented
✅ Flask routes created and configured
✅ Email sending functionality
✅ OTP verification templates created
✅ Session management implemented
✅ Input validation and error handling
✅ Password hashing and update logic
✅ Responsive UI design
✅ Security measures implemented

## Testing the Feature

1. **Request Password Reset**:
   - Navigate to `/reset-password`
   - Enter registered email
   - Check email for OTP code

2. **Verify OTP**:
   - Enter received 6-digit OTP
   - If invalid, error message appears
   - If valid, proceed to password reset

3. **Reset Password**:
   - Enter new password (minimum 6 characters)
   - Confirm password
   - Upon success, redirected to login page
   - Login with new password to verify

## Environment Configuration

Ensure the following environment variables are set for email functionality:

```bash
SMTP_SERVER=your_smtp_server.com
SMTP_PORT=587
SMTP_USERNAME=your_email@domain.com
SMTP_PASSWORD=your_password
EMAIL_FROM=noreply@fakenewsdetection.com
```

## Error Handling

The system handles various error scenarios:

1. **Invalid OTP**: Shows error, prompts to try again or request new code
2. **Expired OTP**: Shows error, prompts to request new code
3. **Password Mismatch**: Shows error, prompts to re-enter
4. **Email Not Found**: Shows generic success message (security)
5. **Email Send Failure**: Shows error, allows retry
6. **Database Errors**: Logged to console, generic error to user

## Future Enhancements

- OTP attempt limiting (max 3 attempts before lockout)
- Resend OTP functionality on verification page
- SMS-based OTP delivery option
- Two-factor authentication integration
- OTP history/audit logging
- Email template customization
- Configurable OTP expiration time
