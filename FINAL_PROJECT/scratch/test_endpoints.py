import requests

BASE = 'http://127.0.0.1:5000'

def test_api():
    print("--- 1. Testing University Login (simat / simat@123) ---")
    res = requests.post(f"{BASE}/api/auth/login", json={"username": "simat", "password": "simat@123"})
    print("Status:", res.status_code)
    simat_data = res.json()
    token = simat_data.get("token")
    print("Institution User:", simat_data.get("user"))

    print("\n--- 2. Testing University GET /api/institution/students ---")
    headers = {"Authorization": f"Bearer {token}"}
    s_res = requests.get(f"{BASE}/api/institution/students", headers=headers)
    print("Status:", s_res.status_code)
    students = s_res.json().get("students", [])
    print("Students found:", len(students))
    for s in students:
        print(f" -> Student: {s.get('username')} ({s.get('full_name')}), Reg: {s.get('register_number')}, Pw: {s.get('current_password')}")

    print("\n--- 3. Testing Student Login (priya22 / password123) ---")
    s_login = requests.post(f"{BASE}/api/auth/login", json={"username": "priya22", "password": "password123"})
    print("Status:", s_login.status_code)
    s_login_data = s_login.json()
    priya_token = s_login_data.get("token")
    print("Priya User:", s_login_data.get("user"))

    print("\n--- 4. Testing Student GET /api/certificates ---")
    priya_headers = {"Authorization": f"Bearer {priya_token}"}
    c_res = requests.get(f"{BASE}/api/certificates", headers=priya_headers)
    print("Status:", c_res.status_code)
    certs = c_res.json()
    print("Certificates returned for priya22:", len(certs.get("certificates", [])))
    for c in certs.get("certificates", []):
        print(f" - Cert ID: {c.get('cert_id')}, Student: {c.get('student_name')}, Reg: {c.get('register_number')}")

    print("\n--- 5. Testing Student cannot register via /api/auth/register ---")
    reg_res = requests.post(f"{BASE}/api/auth/register", json={
        "username": "selfstudent",
        "email": "self@test.com",
        "password": "validpassword123",
        "role": "student"
    })
    print("Status (should be 403):", reg_res.status_code, reg_res.json())

    print("\n--- 6. Testing Student Password Change ---")
    pw_res = requests.post(f"{BASE}/api/auth/change-password", headers=priya_headers, json={
        "current_password": "password123",
        "new_password": "newpassword456"
    })
    print("Change Password Status:", pw_res.status_code, pw_res.json())

    print("\n--- 7. Testing University sees updated student password ---")
    s_res_after = requests.get(f"{BASE}/api/institution/students", headers=headers)
    students_after = s_res_after.json().get("students", [])
    for s in students_after:
        if s.get('username') == 'priya22':
            print(f"Priya updated password in university section: '{s.get('current_password')}' (Should be 'newpassword456')")

    print("\n--- 8. Testing Student login with new password and reset back ---")
    new_login = requests.post(f"{BASE}/api/auth/login", json={"username": "priya22", "password": "newpassword456"})
    print("Login with new password status:", new_login.status_code)
    # Reset back to password123 for consistency
    new_token = new_login.json().get("token")
    reset_pw = requests.post(f"{BASE}/api/auth/change-password", headers={"Authorization": f"Bearer {new_token}"}, json={
        "current_password": "newpassword456",
        "new_password": "password123"
    })
    print("Reset back to password123 status:", reset_pw.status_code)

if __name__ == '__main__':
    test_api()
