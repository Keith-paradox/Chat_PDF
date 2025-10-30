import requests

def test_ask():
    payload = {"session_id": "testsession", "question": "What is the main theorem?"}
    resp = requests.post("http://localhost:8000/v1/ask", json=payload)
    print(resp.json())

if __name__ == "__main__":
    test_ask()
