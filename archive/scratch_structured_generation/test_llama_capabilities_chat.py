import urllib.request
import json
from schema_def import strict_schema

def test_inference(payload):
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions", 
                                 data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'},
                                 method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            res = json.loads(f.read().decode('utf-8'))
            print("Response:", res['choices'][0]['message']['content'])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    print("Testing Mode C: json_schema via chat/completions")
    test_inference({
        "messages": [{"role": "user", "content": "You must decide an action."}],
        "max_tokens": 100,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "decision",
                "strict": True,
                "schema": strict_schema
            }
        }
    })
