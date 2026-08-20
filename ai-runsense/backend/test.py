import urllib.request
import json
import urllib.error

data = json.dumps({"email": "test3@test.com", "password": "test", "name": "test"}).encode("utf-8")
req = urllib.request.Request("http://localhost:8000/api/auth/register", data=data, headers={"Content-Type": "application/json"})

try:
    res = urllib.request.urlopen(req)
    print("SUCCESS", res.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}:", e.read().decode())
except Exception as e:
    print("OTHER ERROR:", e)
