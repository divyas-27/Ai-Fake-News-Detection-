from pathlib import Path


def test_admin_dashboard_uses_ai_news_detector_branding_and_active_user_logic():
    template_path = Path(__file__).resolve().parents[1] / "templates" / "admin_dashboard.html"
    content = template_path.read_text(encoding="utf-8")

    assert "AI News Detector" in content
    assert "const activeUsers = allUsers.filter(u => u.status === 'active').length;" in content
    assert "u.status === 'active' && !isNewUser(u.joinDate)" not in content
