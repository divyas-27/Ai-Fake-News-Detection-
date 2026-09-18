from pathlib import Path

templates = {
    'templates/dashboard.html': '''{% extends 'base.html' %}

{% block title %}Dashboard | AI Fake News Detection{% endblock %}

{% block content %}
<div class="app-shell">
    <aside class="sidebar">
        <div class="brand">
            <div class="brand-badge">AI</div>
            <div>
                <h1>News Pulse</h1>
                <p>AI-driven insights for trustworthy reporting.</p>
            </div>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ url_for('dashboard') }}" class="active"><span class="icon">🏠</span>Dashboard</a>
            <a href="{{ url_for('predict') }}"><span class="icon">🧠</span>Fake News Detection</a>
            <a href="{{ url_for('analytics') }}"><span class="icon">📊</span>Analytics</a>
            <a href="{{ url_for('profile') }}"><span class="icon">👤</span>Profile</a>
            <a href="{{ url_for('feedback') }}"><span class="icon">✉️</span>Feedback</a>
            <a href="{{ url_for('admin_dashboard') }}"><span class="icon">🛠️</span>Admin</a>
        </nav>

        <div class="sidebar-bottom">
            <p>Logged in as <strong>{{ session.username }}</strong></p>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
        </div>
    </aside>

    <main class="main-content">
        <section class="topbar glass-card">
            <div class="greeting">
                <h2>Welcome back, {{ session.username }} 👋</h2>
                <p>Track your fake news predictions and review AI insights in one place.</p>
            </div>
            <div class="hero-actions">
                <a href="{{ url_for('predict') }}" class="btn btn-primary btn-glow">Detect news</a>
                <a href="{{ url_for('analytics') }}" class="btn btn-secondary">View analytics</a>
            </div>
        </section>

        <section class="stats-grid">
            <article class="stat-card">
                <strong>Total predictions</strong>
                <span class="count">{{ total_predictions }}</span>
            </article>
            <article class="stat-card">
                <strong>Fake labels</strong>
                <span class="count">{{ fake_count }}</span>
            </article>
            <article class="stat-card">
                <strong>Real labels</strong>
                <span class="count">{{ real_count }}</span>
            </article>
        </section>

        <section class="result-panel glass-panel">
            <div class="hero-copy">
                <h3>AI confidence at a glance</h3>
                <p>Use real-time veracity scoring to understand how the model interprets news content.</p>
            </div>
            <div class="confidence-ring" style="--percent: {{ (fake_count + real_count) and ((fake_count / (fake_count + real_count)) * 100) or 0 }}">
                <span>{{ fake_count + real_count }} total</span>
            </div>
        </section>

        <section class="history-panel glass-panel">
            <div class="hero-copy">
                <h3>Recent prediction history</h3>
                <p>Review your latest detections and remove any predictions you no longer need.</p>
            </div>

            {% if predictions %}
            <div class="history-table">
                <table>
                    <thead>
                        <tr>
                            <th>News text</th>
                            <th>Prediction</th>
                            <th>Confidence</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for prediction in predictions[:6] %}
                        <tr>
                            <td>{{ prediction[1][:70] }}{% if prediction[1]|length > 70 %}...{% endif %}</td>
                            <td><span class="prediction-tag prediction-{{ prediction[2].lower() }}">{{ prediction[2] }}</span></td>
                            <td>{{ "%.2f"|format(prediction[3] * 100) }}%</td>
                            <td>{{ prediction[4] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <p class="auth-hint">You have no predictions yet. Start by using the Fake News Detection page.</p>
            {% endif %}
        </section>
    </main>
</div>
{% endblock %}
''',
    'templates/analytics.html': '''{% extends 'base.html' %}

{% block title %}Analytics | AI Fake News Detection{% endblock %}

{% block content %}
<div class="app-shell">
    <aside class="sidebar">
        <div class="brand">
            <div class="brand-badge">AI</div>
            <div>
                <h1>News Pulse</h1>
                <p>Analytics and inference tracking for your account.</p>
            </div>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ url_for('dashboard') }}"><span class="icon">🏠</span>Dashboard</a>
            <a href="{{ url_for('predict') }}"><span class="icon">🧠</span>Fake News Detection</a>
            <a href="{{ url_for('analytics') }}" class="active"><span class="icon">📊</span>Analytics</a>
            <a href="{{ url_for('profile') }}"><span class="icon">👤</span>Profile</a>
            <a href="{{ url_for('feedback') }}"><span class="icon">✉️</span>Feedback</a>
            <a href="{{ url_for('admin_dashboard') }}"><span class="icon">🛠️</span>Admin</a>
        </nav>

        <div class="sidebar-bottom">
            <p>Logged in as <strong>{{ session.username }}</strong></p>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
        </div>
    </aside>

    <main class="main-content">
        <section class="topbar glass-card">
            <div class="greeting">
                <h2>Advanced Analytics</h2>
                <p>Explore prediction accuracy, confidence profiles, and trend charts powered by your news data.</p>
            </div>
        </section>

        <section class="chart-panel glass-panel">
            <h3>Prediction Mix</h3>
            <canvas id="breakdownChart"></canvas>
        </section>

        <section class="chart-panel glass-panel">
            <h3>Trend Over Time</h3>
            <canvas id="trendChart"></canvas>
        </section>

        <section class="chart-panel glass-panel">
            <h3>Confidence Distribution</h3>
            <canvas id="confidenceChart"></canvas>
        </section>
    </main>
</div>
{% endblock %}

{% block extra_js %}
<script>
    const userStats = {{ user_stats | tojson }};
    const breakdownCtx = document.getElementById('breakdownChart');
    if (breakdownCtx && userStats) {
        new Chart(breakdownCtx, {
            type: 'doughnut',
            data: {
                labels: userStats.map(stat => stat[0]),
                datasets: [{
                    data: userStats.map(stat => stat[1]),
                    backgroundColor: ['#38bdf8', '#22c55e', '#fb7185'],
                    borderWidth: 0
                }]
            },
            options: {
                plugins: {
                    legend: { position: 'bottom' }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    fetch('{{ url_for('api_trend') }}')
        .then(res => res.json())
        .then(data => {
            const keys = Object.keys(data).sort();
            const fakeData = keys.map(key => data[key]['Fake'] || 0);
            const realData = keys.map(key => data[key]['Real'] || 0);
            const trendCtx = document.getElementById('trendChart');
            if (trendCtx) {
                new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: keys,
                        datasets: [
                            {
                                label: 'Fake',
                                data: fakeData,
                                borderColor: '#fb7185',
                                backgroundColor: 'rgba(251,113,133,0.18)',
                                tension: 0.3,
                                fill: true
                            },
                            {
                                label: 'Real',
                                data: realData,
                                borderColor: '#22c55e',
                                backgroundColor: 'rgba(34,197,94,0.18)',
                                tension: 0.3,
                                fill: true
                            }
                        ]
                    },
                    options: {
                        scales: { x: { display: false }, y: { beginAtZero: true } },
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
        });

    fetch('{{ url_for('api_confidence') }}')
        .then(res => res.json())
        .then(data => {
            const ranges = ['0-49%', '50-69%', '70-89%', '90-100%'];
            const fakeData = ranges.map(range => data[`Fake_${range}`] || 0);
            const realData = ranges.map(range => data[`Real_${range}`] || 0);
            const confidenceCtx = document.getElementById('confidenceChart');
            if (confidenceCtx) {
                new Chart(confidenceCtx, {
                    type: 'bar',
                    data: {
                        labels: ranges,
                        datasets: [
                            { label: 'Fake', data: fakeData, backgroundColor: '#fb7185' },
                            { label: 'Real', data: realData, backgroundColor: '#22c55e' }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { y: { beginAtZero: true } }
                    }
                });
            }
        });
</script>
{% endblock %}
''',
    'templates/predict.html': '''{% extends 'base.html' %}

{% block title %}Detect Fake News | AI Fake News Detection{% endblock %}

{% block content %}
<div class="app-shell">
    <aside class="sidebar">
        <div class="brand">
            <div class="brand-badge">AI</div>
            <div>
                <h1>News Pulse</h1>
                <p>Real-time detection powered by explainable AI.</p>
            </div>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ url_for('dashboard') }}"><span class="icon">🏠</span>Dashboard</a>
            <a href="{{ url_for('predict') }}" class="active"><span class="icon">🧠</span>Detect News</a>
            <a href="{{ url_for('analytics') }}"><span class="icon">📊</span>Analytics</a>
            <a href="{{ url_for('profile') }}"><span class="icon">👤</span>Profile</a>
            <a href="{{ url_for('feedback') }}"><span class="icon">✉️</span>Feedback</a>
        </nav>

        <div class="sidebar-bottom">
            <p>Logged in as <strong>{{ session.username }}</strong></p>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
        </div>
    </aside>

    <main class="main-content">
        <section class="topbar glass-card">
            <div class="greeting">
                <h2>Fake News Detection</h2>
                <p>Paste your article, URL, or image text and get instant credibility results.</p>
            </div>
            <div class="hero-actions">
                <span class="prediction-tag prediction-real">AI Assist</span>
            </div>
        </section>

        <section class="result-panel glass-panel">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'success' if category == 'success' else 'danger' }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form id="predictForm" class="form-grid">
                <div class="form-group">
                    <label for="news_text">News content</label>
                    <textarea id="news_text" name="news_text" rows="8" placeholder="Paste news text here..." required></textarea>
                    <p class="helper">You can also upload a file with the previous version of the app.</p>
                </div>
                <button type="submit" class="btn btn-primary btn-glow">Analyze now</button>
            </form>

            <div id="loadingSpinner" class="loading-screen" style="display:none;">
                <div class="loader">
                    <div class="loader-dot"></div>
                    <div class="loader-dot"></div>
                    <div class="loader-dot"></div>
                </div>
                <p>Analyzing with the AI engine...</p>
            </div>

            <section id="resultContainer" class="prediction-panel glass-panel" style="display:none;">
                <div>
                    <h3>Result Overview</h3>
                    <p><strong>Prediction:</strong> <span id="predictionLabel" class="prediction-tag prediction-real">Real</span></p>
                    <p><strong>Confidence:</strong> <span id="predictionConfidence">0</span>%</p>
                    <p><strong>Explanation:</strong> <span id="explanationText">AI model reasoning appears here.</span></p>
                </div>
            </section>
        </section>
    </main>
</div>
{% endblock %}

{% block extra_js %}
<script>
    document.getElementById('predictForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const newsText = document.getElementById('news_text').value.trim();
        if (!newsText) return;

        const resultContainer = document.getElementById('resultContainer');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const predictionLabel = document.getElementById('predictionLabel');
        const predictionConfidence = document.getElementById('predictionConfidence');
        const explanationText = document.getElementById('explanationText');

        resultContainer.style.display = 'none';
        loadingSpinner.style.display = 'grid';

        fetch('{{ url_for('api_predict') }}', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: newsText })
        })
        .then(resp => resp.json())
        .then(data => {
            loadingSpinner.style.display = 'none';
            predictionLabel.textContent = data.prediction;
            predictionLabel.className = 'prediction-tag prediction-' + data.prediction.toLowerCase();
            predictionConfidence.textContent = data.confidence;
            explanationText.textContent = data.reasons || 'Explanation not available.';
            resultContainer.style.display = 'block';
        })
        .catch(() => {
            loadingSpinner.style.display = 'none';
            alert('Unable to analyze news at this time. Please try again later.');
        });
    });
</script>
{% endblock %}
''',
    'templates/result.html': '''{% extends 'base.html' %}

{% block title %}Prediction Result | AI Fake News Detection{% endblock %}

{% block content %}
<div class="app-shell">
    <aside class="sidebar">
        <div class="brand">
            <div class="brand-badge">AI</div>
            <div>
                <h1>News Pulse</h1>
                <p>Review the latest prediction and reasoning.</p>
            </div>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ url_for('dashboard') }}"><span class="icon">🏠</span>Dashboard</a>
            <a href="{{ url_for('predict') }}"><span class="icon">🧠</span>Detect News</a>
            <a href="{{ url_for('analytics') }}"><span class="icon">📊</span>Analytics</a>
            <a href="{{ url_for('profile') }}"><span class="icon">👤</span>Profile</a>
            <a href="{{ url_for('feedback') }}"><span class="icon">✉️</span>Feedback</a>
        </nav>

        <div class="sidebar-bottom">
            <p>Logged in as <strong>{{ session.username }}</strong></p>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
        </div>
    </aside>

    <main class="main-content">
        <section class="topbar glass-card">
            <div class="greeting">
                <h2>Prediction Result</h2>
                <p>Analyze the verdict, confidence score, and interpretability notes.</p>
            </div>
        </section>

        <section class="result-panel glass-panel">
            <div class="feature-grid">
                <div>
                    <h3>News excerpt</h3>
                    <p>{{ news_text }}</p>
                </div>
                <div class="confidence-ring" style="--percent: {{ confidence }}">
                    <span>{{ confidence }}%</span>
                </div>
            </div>

            <div class="form-group">
                <label>Prediction</label>
                <span class="prediction-tag prediction-{{ prediction.lower() }}">{{ prediction }}</span>
            </div>
            <div class="form-group">
                <label>Reasoning</label>
                <div class="glass-card" style="padding: 18px;">
                    <p>{{ reasons or 'AI inference generated for this classification.' }}</p>
                </div>
            </div>

            <div class="hero-actions">
                <a href="{{ url_for('predict') }}" class="btn btn-primary">Analyze another</a>
                <a href="{{ url_for('dashboard') }}" class="btn btn-secondary">View history</a>
            </div>
        </section>
    </main>
</div>
{% endblock %}
''',
    'templates/test.html': '''{% extends 'base.html' %}

{% block title %}Test Input | AI Fake News Detection{% endblock %}

{% block content %}
<div class="app-shell">
    <aside class="sidebar">
        <div class="brand">
            <div class="brand-badge">AI</div>
            <div>
                <h1>News Pulse</h1>
                <p>Test sample scenarios and sharpen attribution confidence.</p>
            </div>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ url_for('dashboard') }}"><span class="icon">🏠</span>Dashboard</a>
            <a href="{{ url_for('predict') }}"><span class="icon">🧠</span>Detect News</a>
            <a href="{{ url_for('analytics') }}"><span class="icon">📊</span>Analytics</a>
            <a href="{{ url_for('profile') }}"><span class="icon">👤</span>Profile</a>
            <a href="{{ url_for('feedback') }}"><span class="icon">✉️</span>Feedback</a>
        </nav>

        <div class="sidebar-bottom">
            <p>Logged in as <strong>{{ session.username }}</strong></p>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
        </div>
    </aside>

    <main class="main-content">
        <section class="topbar glass-card">
            <div class="greeting">
                <h2>Try sample headlines</h2>
                <p>Load curated real or fake news samples to understand how the AI model responds.</p>
            </div>
        </section>

        <section class="result-panel glass-panel">
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>Pick a sample</h3>
                    <div class="sample-buttons">
                        {% for sample in samples %}
                        <button type="button" class="btn btn-tertiary sample-btn" data-text="{{ sample.text | e }}">{{ sample.title }}</button>
                        {% endfor %}
                    </div>
                </div>
                <form method="POST" action="{{ url_for('predict') }}" enctype="multipart/form-data" class="form-grid">
                    <div class="form-group">
                        <label for="news_text">Test News Text</label>
                        <textarea id="news_text" name="news_text" rows="8" placeholder="Choose a sample or paste your own text..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Detect headline</button>
                </form>
            </div>
        </section>
    </main>
</div>
{% endblock %}
''',
    'templates/admin_dashboard.html': '''{% extends 'base.html' %}

{% block title %}Admin Dashboard | AI Fake News Detection{% endblock %}

{% block content %}
<div class="app-shell">
    <aside class="sidebar">
        <div class="brand">
            <div class="brand-badge">AI</div>
            <div>
                <h1>Admin Pulse</h1>
                <p>Global view of model performance and system health.</p>
            </div>
        </div>

        <nav class="sidebar-nav">
            <a href="{{ url_for('dashboard') }}"><span class="icon">🏠</span>Dashboard</a>
            <a href="{{ url_for('predict') }}"><span class="icon">🧠</span>Detect News</a>
            <a href="{{ url_for('analytics') }}"><span class="icon">📊</span>Analytics</a>
            <a href="{{ url_for('admin_dashboard') }}" class="active"><span class="icon">🛠️</span>Admin</a>
        </nav>

        <div class="sidebar-bottom">
            <p>Logged in as <strong>{{ session.username }}</strong></p>
            <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
        </div>
    </aside>

    <main class="main-content">
        <section class="topbar glass-card">
            <div class="greeting">
                <h2>Admin dashboard</h2>
                <p>Monitor global activity and see how the prediction engine is performing.</p>
            </div>
        </section>

        <section class="stats-grid">
            <article class="stat-card">
                <strong>Total predictions</strong>
                <span class="count">{{ total_predictions }}</span>
            </article>
            <article class="stat-card">
                <strong>Fake detection</strong>
                <span class="count">{{ fake_percentage }}%</span>
            </article>
        </section>

        <section class="chart-panel glass-panel">
            <h3>Global Predictions Distribution</h3>
            <canvas id="globalStatsChart"></canvas>
        </section>

        <section class="chart-panel glass-panel">
            <h3>Fake News Heatmap (Last 7 Days)</h3>
            <canvas id="heatmapChart"></canvas>
        </section>

        <section class="chart-panel glass-panel">
            <h3>System Activity Timeline</h3>
            <canvas id="activityChart"></canvas>
        </section>
    </main>
</div>
{% endblock %}

{% block extra_js %}
<script>
    const globalStats = {{ global_stats | tojson }};
    const globalCtx = document.getElementById('globalStatsChart');
    if (globalCtx && globalStats) {
        new Chart(globalCtx, {
            type: 'bar',
            data: {
                labels: globalStats.map(stat => stat[0]),
                datasets: [{ label: 'Count', data: globalStats.map(stat => stat[1]), backgroundColor: ['#fb7185', '#22c55e'] }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    fetch('{{ url_for('api_heatmap') }}')
        .then(res => res.json())
        .then(data => {
            const labels = Object.keys(data).sort();
            const values = labels.map(key => data[key]?.Fake || 0);
            const heatmapCtx = document.getElementById('heatmapChart');
            if (heatmapCtx) {
                new Chart(heatmapCtx, {
                    type: 'bar',
                    data: {
                        labels,
                        datasets: [{ label: 'Fake count', data: values, backgroundColor: '#f97316' }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
            }
        });

    fetch('{{ url_for('api_trend') }}')
        .then(res => res.json())
        .then(data => {
            const keys = Object.keys(data).sort();
            const totals = keys.map(key => (data[key].Fake || 0) + (data[key].Real || 0));
            const activityCtx = document.getElementById('activityChart');
            if (activityCtx) {
                new Chart(activityCtx, {
                    type: 'line',
                    data: {
                        labels: keys,
                        datasets: [{ label: 'Total predictions', data: totals, borderColor: '#38bdf8', backgroundColor: 'rgba(56,189,248,0.18)', fill: true }]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
            }
        });
</script>
{% endblock %}
'''
}

for path, content in templates.items():
    Path(path).write_text(content, encoding='utf-8')

print('templates written')
