// Global app helpers

// Password visibility toggle
function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const passwordInput = this.parentElement.querySelector('input[type="password"], input[type="text"]');
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            this.classList.toggle('active');
        });
    });
}

// Palette of professional, attractive colors
const colorPalette = [
    { r: 70, g: 130, b: 180 },    // Steel Blue - Trustworthy & Professional
    { r: 140, g: 100, b: 150 },   // Muted Purple - Elegant & Sophisticated
    { r: 90, g: 120, b: 100 },    // Muted Green - Calming & Balanced
    { r: 130, g: 110, b: 80 },    // Muted Brown - Warm & Grounded
];

// Function to generate random RGB color from palette
function getRandomColor() {
    return colorPalette[Math.floor(Math.random() * colorPalette.length)];
}

// Function to convert RGB to HEX
function rgbToHex(r, g, b) {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
}

// Function to update background color
function updateBackgroundColor() {
    const color = getRandomColor();
    const rgbString = `rgb(${color.r}, ${color.g}, ${color.b})`;
    
    // Apply color directly to background
    document.body.style.backgroundColor = rgbString;
}

// Initialize and start automatic color changes
document.addEventListener('DOMContentLoaded', function() {
    // Start automatic color changing (every 4 seconds)
    updateBackgroundColor();
    setInterval(updateBackgroundColor, 4000);

    // Password visibility toggle
    initPasswordToggle();

    // Allow manual color change on click
    document.addEventListener('click', function(e) {
        // Don't trigger on form inputs or buttons
        if (e.target.tagName !== 'INPUT' && 
            e.target.tagName !== 'TEXTAREA' && 
            e.target.tagName !== 'BUTTON' &&
            !e.target.closest('button')) {
            updateBackgroundColor();
        }
    });

    // Allow spacebar to change color
    document.addEventListener('keydown', function(e) {
        if (e.code === 'Space') {
            e.preventDefault();
            updateBackgroundColor();
        }
    });

    const predictForm = document.getElementById('predictForm');
    if (predictForm) {
        predictForm.addEventListener('submit', function(e) {
            const newsTextElement = document.getElementById('news_text');
            const newsText = newsTextElement ? newsTextElement.value.trim() : '';
            const fileInput = document.getElementById('file');
            const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;

            if (!newsText && !hasFile) {
                alert('Please enter news text or select a file to upload.');
                e.preventDefault();
                return false;
            }
        });
    }

    const sampleButtons = document.querySelectorAll('.sample-btn');
    sampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const text = this.dataset.text;
            const newsTextElement = document.getElementById('news_text');
            if (newsTextElement) {
                newsTextElement.value = text;
                newsTextElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    const themeToggle = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'light') {
        document.body.classList.add('light');
        if (themeToggle) themeToggle.textContent = '☀️';
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('light');
            const nextTheme = document.body.classList.contains('light') ? 'light' : 'dark';
            localStorage.setItem('theme', nextTheme);
            themeToggle.textContent = document.body.classList.contains('light') ? '☀️' : '🌙';
        });
    }
});
