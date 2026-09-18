import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


def test_accept_policies_route_redirects_to_dashboard_after_success():
    app_module.app.config['TESTING'] = True
    client = app_module.app.test_client()

    app_module.update_user_policy_acceptance = lambda user_id: True

    with client.session_transaction() as session:
        session['user_id'] = 1
        session['username'] = 'demo'
        session['privacy_policy_pending'] = True

    response = client.post(
        '/accept-policies',
        data={
            'privacy_accept': 'on',
            'terms_accept': 'on',
            'data_accept': 'on',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/dashboard')
