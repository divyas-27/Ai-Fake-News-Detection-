from app import app

client = app.test_client()
with client.session_transaction() as sess:
    sess['user_id'] = 1
    sess['privacy_policy_pending'] = True

resp = client.get('/privacy-policy')
post_resp = client.post('/privacy-policy/accept')
print('privacy_policy_status', resp.status_code)
print('accept_status', post_resp.status_code)
print('accept_location', post_resp.headers.get('Location'))
