# Fake News Detection System

A web application for detecting fake news using machine learning, built with Flask, Scikit-learn, and MySQL.

## Features

- User registration and login
- Fake news detection using TF-IDF and PassiveAggressiveClassifier
- Text input or file upload for news analysis
- Prediction confidence display
- Prediction history storage in MySQL database
- Responsive web interface

## Project Structure

```
fake_news_detection/
├── app.py                 # Main Flask application
├── model.py               # Machine learning model training and prediction
├── database.py            # MySQL database operations
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── templates/             # HTML templates
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── predict.html
│   └── result.html
├── static/                # Static files (CSS, JS)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── models/                # Trained ML models
└── uploads/               # Temporary file uploads (created automatically)
```

## Prerequisites

- Python 3.7+
- MySQL Server
- VS Code (recommended)

## Setup Instructions

### 1. Install MySQL

Download and install MySQL Server from https://dev.mysql.com/downloads/mysql/

During installation, set up a root password (remember this for the database configuration).

### 2. Create Database

Open MySQL command line or a MySQL client (like MySQL Workbench) and run the commands in `setup.sql`:

```sql
source setup.sql;
```

Or manually:

```sql
CREATE DATABASE fake_news_db;
USE fake_news_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    news_text TEXT NOT NULL,
    prediction VARCHAR(10) NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3. Clone or Download the Project

Place the project files in your desired directory.

### 4. Set up Python Virtual Environment

Open VS Code in the project directory and run:

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure Database Connection

Edit `database.py` and update the `DB_CONFIG` with your MySQL credentials:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Your MySQL username
    'password': 'your_password',  # Your MySQL password
    'database': 'fake_news_db'
}
```

### 7. Run the Application

```bash
python app.py
```

The application will start at http://localhost:5000

## Usage

1. Register a new account or login with existing credentials
2. Navigate to the "Detect News" page
3. Enter news text directly or upload a .txt file
4. Click "Detect" to get the prediction
5. View your prediction history on the dashboard

## Database Schema

### users table
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- username (VARCHAR(50), UNIQUE)
- email (VARCHAR(100), UNIQUE)
- password (VARCHAR(255))
- created_at (TIMESTAMP)

### predictions table
- id (INT, PRIMARY KEY, AUTO_INCREMENT)
- user_id (INT, FOREIGN KEY to users.id)
- news_text (TEXT)
- prediction (VARCHAR(10))
- confidence (FLOAT)
- created_at (TIMESTAMP)

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Machine Learning**: Scikit-learn (TF-IDF Vectorizer, PassiveAggressiveClassifier)
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with responsive design

## Model Training

The model is trained on a sample dataset included in `model.py`. In a production environment, you would use a larger, more diverse dataset for better accuracy.

## Security Notes

- Passwords are hashed using SHA-256 (consider using more secure methods like bcrypt in production)
- File uploads are restricted to .txt files only
- Session management is handled by Flask

## Troubleshooting

1. **Database connection error**: Ensure MySQL is running and credentials in `database.py` are correct
2. **Import errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
3. **Model not found**: The model will be trained automatically on first run if not present
4. **Port already in use**: Change the port in `app.run(debug=True, port=5001)` if 5000 is occupied

## Future Improvements

- Use a larger, more diverse training dataset
- Implement user authentication with JWT tokens
- Add more ML algorithms for comparison
- Implement real-time news fact-checking with external APIs
- Add user feedback system for model improvement