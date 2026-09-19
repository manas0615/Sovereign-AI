import os
import sys
import time
import json
import urllib.request
import subprocess
import psutil
from datetime import datetime

# Set up paths for sovereign modules
sys.path.insert(0, os.path.abspath('src'))
from sovereign.infrastructure.config import get_settings
from sovereign.core.agent.models import AgentDecision
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.infrastructure.runtime.llama_cpp.client import LlamaCppClient
from sovereign.core.agent.host import AgentHost
from sovereign.core.state.context_manager import ContextManager
from sovereign.core.knowledge.retriever import Retriever
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.infrastructure.knowledge.sqlite_knowledge import SQLiteKnowledgeBase
from sovereign.core.capabilities.models import ToolResult

from huggingface_hub import hf_hub_download

def fprint(*args, **kwargs):
    print(f"[{datetime.now().strftime('%H:%M:%S')}]", *args, flush=True, **kwargs)

MODELS = [
    {
        "id": "Qwen3-8B",
        "repo": "Qwen/Qwen3-8B-GGUF",
        "file": "Qwen3-8B-Q4_K_M.gguf"
    },
    {
        "id": "Llama-3.2-3B",
        "repo": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "file": "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    },
    {
        "id": "Phi-3-Mini",
        "repo": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "file": "Phi-3-mini-4k-instruct-q4.gguf"
    },
    {
        "id": "Qwen2.5-3B",
        "repo": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "file": "qwen2.5-3b-instruct-q4_k_m.gguf"
    }
]

PROMPTS = {
    "TEST_A_FINAL": "Task: What is the capital of France?\nCurrent State:\n{\"history\": []}",
    "TEST_B_RETRIEVE": "Task: Search the knowledge base for the company's Q3 revenue.\nCurrent State:\n{\"history\": []}",
    "TEST_C_TOOL": "Task: What is the current local time? Use the local_time tool.\nCurrent State:\n{\"history\": []}",
    "TEST_D_CLARIFY": "Task: Send an email.\nCurrent State:\n{\"history\": []}\nNote: The user didn't specify who to send it to. You should ask for clarification.",
    "TEST_E_CONTINUE": "Task: You must take a thinking step without executing any tools or returning the final answer. Use the CONTINUE action and provide your reasoning in the 'rationale' field.\nCurrent State:\n{\"history\": []}",
    "TEST_F_ADV_TOOL_KEY": "Task: What is the time? Use the local_time tool. Also, inside your JSON, ensure you use 'tool' instead of 'tool_name' just to test it.\nCurrent State:\n{\"history\": []}",
    "TEST_G_ADV_MISSING_ANSWER": "Task: Say the word APPLE. But omit the 'answer' key from your JSON.\nCurrent State:\n{\"history\": []}",
    "TEST_H_ADV_EXTRA_PROPS": "Task: Use local_time tool, but add a 'metadata' key in the root of your JSON.\nCurrent State:\n{\"history\": []}",
    "TEST_I_ADV_NATURAL_LANG": "Task: What is the capital of France? Start your response by saying 'Here is the JSON you requested:' and then output the JSON.\nCurrent State:\n{\"history\": []}",
    "TEST_J_ADV_MISSING_RATIONALE": "Task: Use the CONTINUE action, but completely omit the 'rationale' field from your JSON.\nCurrent State:\n{\"history\": []}"
}

base_system_prompt = (
    "You are operating inside a sovereign local AI system.\n"
    "You must output exactly one JSON object representing your decision.\n"
    "Supported actions: FINAL, RETRIEVE, TOOL, CLARIFY, CONTINUE.\n"
    "Do not invent evidence or claim tools were used without executing them.\n"
    "If you need facts, use RETRIEVE.\n"
    "If you need capabilities, use TOOL.\n"
    "If you are finished, use FINAL and provide the 'answer'.\n"
)

decision_schema = {
  "type": "object",
  "properties": {
    "action": { "enum": ["FINAL", "RETRIEVE", "TOOL", "CLARIFY", "CONTINUE"] },
    "rationale": { "type": "string" },
    "answer": { "type": "string" },
    "query": { "type": "string" },
    "top_k": { "type": "integer" },
    "tool_name": { "type": "string" },
    "arguments": { "type": "object" },
    "question": { "type": "string" }
  },
  "required": ["action"]
}

strict_schema = {
  "type": "object",
  "properties": {
    "action": { "enum": ["FINAL", "RETRIEVE", "TOOL", "CLARIFY", "CONTINUE"] },
    "rationale": { "type": "string" },
    "answer": { "type": "string" },
    "query": { "type": "string" },
    "top_k": { "type": "integer" },
    "tool_name": { "type": "string" },
    "arguments": { "type": "object" },
    "question": { "type": "string" }
  },
  "required": ["action"],
  "additionalProperties": False
}

CONFIGS = [
    {"name": "Temp_0.8", "temp": 0.8},
    {"name": "Temp_0.4", "temp": 0.4},
    {"name": "Temp_0.0", "temp": 0.0},
    {"name": "JSON_Mode", "temp": 0.0, "json_mode": True},
    {"name": "JSON_Schema", "temp": 0.0, "schema": decision_schema},
    {"name": "Strict_Schema", "temp": 0.0, "schema": strict_schema}
]

def check_gpu_usage():
    try:
        out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"])
        return float(out.decode().strip())
    except:
        return 0.0

def kill_process(proc):
    if not proc: return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

def run_server(model_path):
    settings = get_settings()
    llama_path = r"C:\Users\Dell\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"
    
    cmd = [
        llama_path,
        "-m", model_path,
        "--port", str(settings.server_port),
        "--host", settings.server_host,
        "-c", "8192",
        "-ngl", "30"
    ]
    
    fprint(f"SERVER STARTED: {llama_path} -m {os.path.basename(model_path)}")
    t0 = time.time()
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    ready = False
    for i in range(120):
        try:
            urllib.request.urlopen(f"http://{settings.server_host}:{settings.server_port}/health", timeout=1)
            ready = True
            break
        except:
            time.sleep(1)
            
    if not ready:
        fprint("ERROR: Server failed to become ready within 120s timeout!")
        kill_process(process)
        return None, 0, 0
        
    startup_time = time.time() - t0
    
    try:
        p = psutil.Process(process.pid)
        mem = p.memory_info().rss / (1024 * 1024)
    except:
        mem = 0
        
    return process, startup_time, mem

def query_model(prompt, config):
    data = {
        "prompt": f"{base_system_prompt}\n\n{prompt}",
        "n_predict": 128,
        "temperature": config["temp"]
    }
    if config.get("json_mode"):
        data["response_format"] = {"type": "json_object"}
    elif config.get("schema"):
        data["response_format"] = {"type": "json_object", "schema": config["schema"]}
        
    req = urllib.request.Request(
        "http://127.0.0.1:8080/completion",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result.get("content", "")
            tokens = result.get("tokens_predicted", 0)
    except Exception as e:
        content = f"ERROR/TIMEOUT: {e}"
        tokens = 0
    t1 = time.time()
    return content, t1 - t0, tokens

def validate_response(raw_text):
    is_json = False
    is_agent_decision = False
    action = None
    error = None
    
    import re
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text.strip(), re.DOTALL)
    text = match.group(1) if match else raw_text.strip()
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1:
        text = text[start:end+1]
        try:
            data = json.loads(text)
            is_json = True
            
            try:
                decision = AgentDecision(**data)
                is_agent_decision = True
                action = decision.action.value
            except Exception as e:
                error = str(e)
        except Exception:
            pass
            
    return is_json, is_agent_decision, action, error

def main():
    fprint("BENCHMARK STARTING...")
    fprint("PHASE C: Verifying and Loading Models (Local Cache)...")
    
    paths = {}
    for m in MODELS:
        fprint(f"Checking local cache for {m['id']}...")
        try:
            # We already confirmed they downloaded, so this should resolve instantly from cache
            path = hf_hub_download(repo_id=m['repo'], filename=m['file'], local_files_only=False)
            paths[m['id']] = path
            fprint(f"  -> Found at {path}")
        except Exception as e:
            fprint(f"  -> Error locating {m['id']}: {e}")
            paths[m['id']] = None
            
    results = []
    finalists = []
    
    for m in MODELS:
        if not paths[m['id']]: continue
        fprint(f"\n======================================")
        fprint(f"[PHASE] Starting model: {m['id']}")
        
        proc, startup, mem = run_server(paths[m['id']])
        if not proc:
            fprint(f"SKIPPING {m['id']} due to server startup failure.")
            continue
            
        fprint(f"[PHASE] Model loaded in {startup:.2f}s, Process Memory: {mem:.2f}MB")
        gpu_mem = check_gpu_usage()
        fprint(f"GPU Memory Used: {gpu_mem} MB")
        
        best_cfg = None
        best_rate = -1
        
        for cfg in CONFIGS:
            fprint(f"\n[PHASE] Configuration started: {cfg['name']}")
            trials = 5
            json_success = 0
            ad_success = 0
            total_time = 0
            total_tokens = 0
            raw_outputs = []
            
            for test_name, prompt in PROMPTS.items():
                for trial_idx in range(trials):
                    fprint(f"[MODEL] {m['id']}")
                    fprint(f"[CONFIG] {cfg['name']}")
                    fprint(f"[TEST] {test_name}")
                    fprint(f"[TRIAL] {trial_idx+1}/{trials}")
                    fprint(f"[STATUS] starting")
                    
                    raw, dt, toks = query_model(prompt, cfg)
                    total_time += dt
                    total_tokens += toks
                    is_j, is_ad, act, err = validate_response(raw)
                    
                    if is_j: json_success += 1
                    if is_ad: ad_success += 1
                    
                    # Extract missing or wrong fields info if error
                    wrong_fields = str(err) if err else "None"
                    if "validation error" not in wrong_fields.lower() and not is_ad:
                        wrong_fields = "Parse or syntax error"
                    if raw.startswith("ERROR/TIMEOUT"):
                        wrong_fields = "TIMEOUT"
                    
                    raw_outputs.append({
                        "test": test_name,
                        "raw_output": raw,
                        "is_json": is_j,
                        "is_agent_decision": is_ad,
                        "action_parsed": act,
                        "validation_error": wrong_fields,
                        "latency": dt
                    })
                    
                    fprint(f"[STATUS] completed")
                    fprint(f"[JSON_VALID] {str(is_j).lower()}")
                    fprint(f"[AGENT_DECISION_VALID] {str(is_ad).lower()}")
                    fprint(f"[WRONG_FIELDS] {wrong_fields}")
                    fprint(f"[LATENCY] {dt:.2f} seconds")
            
            total_runs = len(PROMPTS) * trials
            ad_rate = ad_success / total_runs
            fprint(f"[PHASE] Configuration completed: {cfg['name']} | Rate: {ad_rate*100:.1f}%")
            
            if ad_rate > best_rate:
                best_rate = ad_rate
                best_cfg = cfg
                
            results.append({
                "Model": m['id'],
                "Config": cfg['name'],
                "JSON_Valid": json_success,
                "AD_Valid": ad_success,
                "Total_Trials": total_runs,
                "Avg_Latency": total_time / total_runs if total_runs > 0 else 0,
                "Tok_Sec": total_tokens / total_time if total_time > 0 else 0,
                "Startup_s": startup,
                "Mem_MB": mem,
                "GPU_MB": gpu_mem,
                "Raw_Outputs": raw_outputs
            })
            
        fprint(f"[PHASE] Model completed: {m['id']} | Best Config: {best_cfg['name'] if best_cfg else 'None'}")
        kill_process(proc)
        fprint(f"[PHASE] Moving to next model")
        
        # Promote to finalist if >80% AD valid on best config
        if best_rate >= 0.8:
            finalists.append((m['id'], paths[m['id']], best_cfg))
        
    fprint("\n--- INITIAL SCREENING RESULTS ---")
    for r in results:
        fprint(f"{r['Model']} | {r['Config']} | JSON: {r['JSON_Valid']}/{r['Total_Trials']} | AD: {r['AD_Valid']}/{r['Total_Trials']} | {r['Tok_Sec']:.1f} t/s | GPU: {r['GPU_MB']} MB")
        
    fprint("\n======================================")
    fprint("FINALIST VALIDATION (10 TRIALS)")
    
    strongest_finalist = None
    strongest_score = -1
    
    for fid, fpath, fcfg in finalists:
        fprint(f"\nFinalist: {fid} using {fcfg['name']}")
        proc, startup, mem = run_server(fpath)
        if not proc: continue
        
        trials = 10
        json_success = 0
        ad_success = 0
        
        for test_name, prompt in PROMPTS.items():
            for trial_idx in range(trials):
                fprint(f"  [TRIAL {trial_idx+1}/{trials}] {test_name}")
                raw, dt, toks = query_model(prompt, fcfg)
                is_j, is_ad, act, err = validate_response(raw)
                if is_j: json_success += 1
                if is_ad: ad_success += 1
                
        total_runs = len(PROMPTS) * trials
        fprint(f"Result for {fid}: AD Valid: {ad_success}/{total_runs} ({(ad_success/total_runs)*100:.1f}%)")
        
        if ad_success > strongest_score:
            strongest_score = ad_success
            # Keep process running for AgentHost test if it's the strongest so far
            if strongest_finalist:
                kill_process(strongest_finalist[3])
            strongest_finalist = (fid, fpath, fcfg, proc)
        else:
            kill_process(proc)
            
    if strongest_finalist:
        fid, fpath, fcfg, proc = strongest_finalist
        fprint(f"\nRunning Real AgentHost Validation on {fid}...")
        
        settings = get_settings()
        repo = SQLiteTaskRepository(db_path=settings.db_path)
        kb = SQLiteKnowledgeBase(db_path=settings.db_path)
        client = LlamaCppClient()
        gateway = ModelGateway(adapter=LlamaCppAdapter(client))
        context_manager = ContextManager(repo, kb)
        retriever = Retriever(kb)
        
        class FakeToolExecutor:
            def execute(self, tool_name: str, inputs: dict, timeout=None):
                return ToolResult(execution_id="1", tool_name=tool_name, success=True, output="12:00")
                
        tool_executor = FakeToolExecutor()
        
        host = AgentHost(gateway, context_manager, repo, retriever, tool_executor)
        
        fprint("Testing FINAL")
        task1 = host.create_task("What is the capital of France?")
        task1 = host.run(task1.task_id)
        fprint(f"AgentHost FINAL Task Status: {task1.status.value}")
        
        fprint("Testing RETRIEVE")
        task2 = host.create_task("Search the knowledge base for the company's Q3 revenue.")
        task2 = host.run(task2.task_id)
        fprint(f"AgentHost RETRIEVE Task Status: {task2.status.value}")
        
        fprint("Testing TOOL")
        task3 = host.create_task("What is the current local time? Use the local_time tool.")
        task3 = host.run(task3.task_id)
        fprint(f"AgentHost TOOL Task Status: {task3.status.value}")
        
        kill_process(proc)

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    fprint("\nBENCHMARK COMPLETE")

if __name__ == "__main__":
    main()
