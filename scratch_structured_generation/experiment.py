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
from scratch_structured_generation.schemas import loose_schema, strict_schema

def kill_process(proc):
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except:
        try:
            proc.kill()
        except:
            pass
    # Clean any lingering llama-servers
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

PROMPTS = {
    "FINAL": "You are done. Respond with the final answer: 'Paris'.",
    "RETRIEVE": "Query the knowledge base for 'Q3 revenue'.",
    "TOOL": "Execute the tool 'local_time'.",
    "CLARIFY": "Ask the user: 'Who is the email for?'.",
    "CONTINUE": "Think about the problem without taking external action.",
    "ADV_EXTRA_PROPS": "Use the tool 'local_time'. Also include a 'metadata' property with value 'extra'.",
    "ADV_WRONG_TOOL_KEY": "Use the tool 'local_time'. Ensure the JSON key is 'tool' instead of 'tool_name'.",
    "ADV_MISSING_ANSWER": "Output a FINAL action, but intentionally omit the 'answer' field.",
    "ADV_MISSING_RATIONALE": "Output a CONTINUE action, but omit the 'rationale' field.",
    "ADV_NATURAL_LANG": "Write 'Here is the JSON:' before outputting the RETRIEVE action for 'capital'."
}

MODES = ["A_BASELINE", "B_JSON_MODE", "C_JSON_SCHEMA", "D_STRICT_SCHEMA"]

def query_model(prompt_text, mode):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a local AI agent. Output exactly one JSON object representing your decision."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.4,
        "max_tokens": 100
    }
    
    if mode == "B_JSON_MODE":
        payload["response_format"] = {"type": "json_object"}
    elif mode == "C_JSON_SCHEMA":
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "loose", "schema": loose_schema}
        }
    elif mode == "D_STRICT_SCHEMA":
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "strict", "strict": True, "schema": strict_schema}
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
        return False, False, str(raw)
        
    try:
        AgentDecision(**data)
        return True, True, None
    except Exception as e:
        return True, False, str(e)

if __name__ == "__main__":
    MODELS = [
        ("Llama-3.2-3B", r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf"),
        ("Phi-3-Mini", r"C:\Users\Dell\.cache\huggingface\hub\models--microsoft--Phi-3-mini-4k-instruct-gguf\snapshots\a64113399c2f6b8ad3e11c394733a2ddadaa7f33\Phi-3-mini-4k-instruct-q4.gguf"),
        ("Qwen2.5-3B", r"C:\Users\Dell\.cache\huggingface\hub\models--Qwen--Qwen2.5-3B-Instruct-GGUF\snapshots\7dabda4d13d513e3e842b20f0d435c732f172cbe\qwen2.5-3b-instruct-q4_k_m.gguf")
    ]
    
    results = []
    
    for name, path in MODELS:
        print(f"\n[PHASE] Starting model {name}")
        proc = run_server(path)
        if not proc:
            print(f"FAILED TO START {name}")
            continue
            
        print(f"[PHASE] Model ready. Starting trials.")
        
        for mode in MODES:
            json_v = 0
            ad_v = 0
            latencies = []
            failures = []
            
            for test_name, prompt in PROMPTS.items():
                for trial in range(3):
                    raw, dt = query_model(prompt, mode)
                    latencies.append(dt)
                    
                    is_j, is_ad, err = validate_response(raw)
                    if is_j: json_v += 1
                    if is_ad: ad_v += 1
                    else: failures.append((test_name, err))
                    
                    print(f"  {name} | {mode} | {test_name} | T{trial} | JSON: {is_j} | AD: {is_ad}")
            
            avg_lat = sum(latencies) / len(latencies) if latencies else 0
            results.append({
                "Model": name,
                "Mode": mode,
                "JSON_Valid": json_v,
                "AD_Valid": ad_v,
                "Avg_Latency": avg_lat,
                "Failures": failures
            })
            
        kill_process(proc)
        
    with open("scratch_structured_generation/experiment_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("DONE")
