import urllib.request
import json

def test_inference(payload):
    req = urllib.request.Request("http://127.0.0.1:8080/completion", 
                                 data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'},
                                 method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            res = json.loads(f.read().decode('utf-8'))
            print("Response:", res.get("content", ""))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    from schema_def import strict_schema
    # Mode B: json_format
    print("Testing Mode B: json format")
    test_inference({
        "prompt": "Answer with a JSON object { \"hello\": \"world\" }:\n",
        "n_predict": 20,
        "response_format": {"type": "json_object"}
    })
    
    # Mode C: json_schema
    print("\nTesting Mode C: json_schema")
    test_inference({
        "prompt": "You must decide an action. Output JSON matching the schema.\n",
        "n_predict": 100,
        "response_format": {
            "type": "json_schema",
            "schema": strict_schema
        }
    })
