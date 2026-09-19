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

def query_model(prompt_text, max_tokens):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a local AI agent. Output exactly one JSON object representing your decision."},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.4,
        "max_tokens": max_tokens,
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
        with urllib.request.urlopen(req, timeout=120) as f:
            res = json.loads(f.read().decode('utf-8'))
            raw = res['choices'][0]['message']['content']
            finish_reason = res['choices'][0].get('finish_reason', 'unknown')
            usage = res.get('usage', {})
            generated_tokens = usage.get('completion_tokens', 0)
            return raw, time.time() - t0, finish_reason, generated_tokens
    except Exception as e:
        return f"ERROR: {e}", time.time() - t0, "error", 0

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
        return True, False, f"Semantic Validation Failure: {str(e)}"

if __name__ == "__main__":
    MODEL_PATH = r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    
    print("[PHASE] Starting model Llama-3.2-3B")
    proc = run_server(MODEL_PATH)
    if not proc:
        print("FAILED TO START")
        sys.exit(1)
        
    print("[PHASE] Model ready. Starting trials.")
    
    PROMPT = "Please provide the final answer 'Paris' with detailed rationale."
    budgets = [100, 256, 512]
    
    results = []
    
    trial_id = 0
    for limit in budgets:
        for _ in range(3):
            trial_id += 1
            raw, dt, finish, gen_toks = query_model(PROMPT, limit)
            is_j, is_ad, err = validate_response(raw)
            
            print(f"[{trial_id:03d}] max_tokens={limit} | Toks: {gen_toks} | Finish: {finish} | JSON: {is_j} | AD: {is_ad} | Latency: {dt:.2f}s")
            
            results.append({
                "trial": trial_id,
                "max_tokens": limit,
                "generated_tokens": gen_toks,
                "finish_reason": finish,
                "raw": raw,
                "json_valid": is_j,
                "ad_valid": is_ad,
                "latency": dt,
                "error": err
            })
            
    kill_process(proc)
    
    with open("scratch_structured_generation/truncation_test.json", "w") as f:
        json.dump(results, f, indent=2)
    print("DONE")
