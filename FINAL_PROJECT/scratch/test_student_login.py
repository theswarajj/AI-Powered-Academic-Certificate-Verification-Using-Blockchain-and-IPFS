import requests

# Test 1: Login using username
res1 = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'arjun4117', 'password': 'Arjun#4794'})
print('Login with username arjun4117:', res1.status_code, res1.json().get('user', {}).get('full_name'))
token1 = res1.json().get('token')

# Test 2: Login using register number
res2 = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': '21EC04117', 'password': 'Arjun#4794'})
print('Login with register number 21EC04117:', res2.status_code, res2.json().get('user', {}).get('full_name'))

# Test 3: List certificates as student
certs_res = requests.get('http://127.0.0.1:5000/api/certificates', headers={'Authorization': f'Bearer {token1}'})
certs = certs_res.json().get('certificates', [])
print(f'Student certs count: {len(certs)}')
for c in certs:
    print('  - Cert:', c.get('cert_id'), c.get('student_name'), c.get('register_number'))
