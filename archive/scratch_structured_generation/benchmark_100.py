import os
import sys
import time
import json
import urllib.request
import subprocess
import psutil

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('src'))
from sovereign.core.agent.models import AgentDecision
from scratch_structured_generation.schema_corrected import strict_schema_corrected

def kill_process(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except:
        try:
            proc.kill()
        except:
            pass
    for p in psutil.process_iter(['name']):
        if p.info['name'] and 'llama-server' in p.info['name'].lower():
            try:
                p.kill()
            except:
                pass
    time.sleep(1)

def run_server(model_path):
    cmd = [
        r"C:\Users\Dell\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe",
        "-m", model_path,
        "-c", "4096",
        "--port", "8080",
        "--host", "127.0.0.1",
        "-ngl", "33"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    for _ in range(60):
        try:
            urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=1)
            return proc
        except:
            time.sleep(1)
            if proc.poll() is not None:
                break
    kill_process(proc)
    return None

PROMPT_VARIANTS = [
    # FINAL
    ("FINAL_STD_1", "You are done. The capital is Paris."),
    ("FINAL_STD_2", "Please provide the final answer 'Paris' with detailed rationale."),
    ("FINAL_ADV_MISSING", "Return answer but omit the answer field. Just output action FINAL."),
    ("FINAL_ADV_EMPTY", "Output FINAL. Set answer to an empty string."),
    # RETRIEVE
    ("RETRIEVE_STD_1", "Query the knowledge base for 'Q3 revenue'."),
    ("RETRIEVE_STD_2", "Retrieve information about 'Project X', return top_k as 10."),
    ("RETRIEVE_ADV_MISSING", "Search for 'sales'. Omit the query field."),
    ("RETRIEVE_ADV_EXTRA", "Query for 'sales'. Include a 'metadata' property with value 'extra'."),
    # TOOL
    ("TOOL_STD_1", "Execute the tool 'local_time'."),
    ("TOOL_STD_2", "Run tool 'read_file' with argument 'path' = 'config.json'."),
    ("TOOL_ADV_WRONG_KEY", "Use tool 'local_time'. Ensure the JSON key is 'tool' instead of 'tool_name'."),
    ("TOOL_ADV_CONTRADICT", "Execute 'local_time'. Put 'local_time' in the action field and 'TOOL' in the tool_name field."),
    # CLARIFY
    ("CLARIFY_STD_1", "Ask the user: 'Who is the email for?'"),
    ("CLARIFY_STD_2", "Clarify with the user about their preferred format."),
    ("CLARIFY_ADV_NL", "Ask the user 'Why?'. Do it by outputting plain text: 'Here is the JSON: {\"action\": \"CLARIFY\"}'."),
    ("CLARIFY_ADV_WRONG_KEY", "Ask 'What time?'. Put the question in 'response' field instead of 'question'."),
    # CONTINUE
    ("CONTINUE_STD_1", "Think about the problem without taking external action."),
    ("CONTINUE_STD_2", "Record your rationale: 'I need to process the data'."),
    ("CONTINUE_ADV_MISSING", "Output a CONTINUE action, but omit the 'rationale' field."),
    ("CONTINUE_ADV_NULL", "CONTINUE action. Set rationale to null.")
]

def query_model(prompt_text):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a local AI agent. Output exactly one JSON object representing your decision."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.4,
        "max_tokens": 100,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "strict", "strict": True, "schema": strict_schema_corrected}
        }
    }
    
    req = urllib.request.Request("http://127.0.0.1:8080/v1/chat/completions", 
                                 data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'},
                                 method='POST')
                                 
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as f:
            res = json.loads(f.read().decode('utf-8'))
            raw = res['choices'][0]['message']['content']
            return raw, time.time() - t0
    except Exception as e:
        return f"ERROR: {e}", time.time() - t0

def validate_response(raw):
    try:
        data = json.loads(raw)
        is_j = True
    except:
        return False, False, "JSON Syntax Error"
        
    try:
        AgentDecision(**data)
        return True, True, None
    except Exception as e:
        err_str = str(e)
        if "requires an 'answer'" in err_str: return True, False, "Missing or Empty Answer"
        if "requires a 'query'" in err_str: return True, False, "Missing or Empty Query"
        if "requires a 'tool_name'" in err_str: return True, False, "Missing or Empty Tool_Name"
        if "requires a 'question'" in err_str: return True, False, "Missing or Empty Question"
        if "requires a 'rationale'" in err_str: return True, False, "Missing or Empty Rationale"
        if "Input should be" in err_str and "AgentAction" in err_str: return True, False, "Wrong action value"
        return True, False, f"Semantic Validation Failure: {err_str}"

if __name__ == "__main__":
    MODEL_PATH = r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    
    print("[PHASE] Starting model Llama-3.2-3B")
    proc = run_server(MODEL_PATH)
    if not proc:
        print("FAILED TO START")
        sys.exit(1)
        
    print("[PHASE] Model ready. Starting 100 trials.")
    
    results = []
    
    json_v = 0
    ad_v = 0
    
    trial_id = 0
    for name, prompt in PROMPT_VARIANTS:
        for _ in range(5):
            trial_id += 1
            raw, dt = query_model(prompt)
            is_j, is_ad, err = validate_response(raw)
            
            if is_j: json_v += 1
            if is_ad: ad_v += 1
            
            print(f"[{trial_id:03d}] {name} | JSON: {is_j} | AD: {is_ad} | Latency: {dt:.2f}s")
            
            results.append({
                "trial": trial_id,
                "variant": name,
                "raw": raw,
                "json_valid": is_j,
                "ad_valid": is_ad,
                "latency": dt,
                "error": err
            })
            
    kill_process(proc)
    
    with open("scratch_structured_generation/benchmark_100.json", "w") as f:
        json.dump(results, f, indent=2)
    print("DONE")
