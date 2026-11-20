import requests

# 1. Login as simat (institution)
res = requests.post('http://127.0.0.1:5000/api/auth/login', json={'username': 'simat', 'password': 'simat@123'})
print('Login status:', res.status_code)
token = res.json().get('token')

# 2. Get students
headers = {'Authorization': f'Bearer {token}'}
s_res = requests.get('http://127.0.0.1:5000/api/institution/students', headers=headers)
print('Students response code:', s_res.status_code)
students = s_res.json().get('students', [])
for s in students:
    print(f"Student: {s.get('full_name')} | Reg: {s.get('register_number')} | Username: {s.get('username')} | Password: {s.get('current_password')} | Certs: {s.get('certificates_count')}")
