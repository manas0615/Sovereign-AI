import os
import sys
import time
import json
import subprocess
import psutil

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('src'))

from sovereign.core.runtime.models import InferenceRequest, InferenceResponse, RuntimeStatus
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.agent.models import AgentDecision, AGENT_DECISION_RESPONSE_FORMAT, AgentAction
from sovereign.core.agent.parser import ModelOutputParser

def clean_llama():
    for p in psutil.process_iter(['name']):
        if p.info['name'] and 'llama-server' in p.info['name'].lower():
            try:
                p.kill()
            except:
                pass
    time.sleep(1)

def run_hardware_validation():
    clean_llama()
    
    # Configure settings for Llama-3.2-3B-Instruct-Q4_K_M
    import sovereign.infrastructure.config as config
    llama_path = r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    server_exe = r"C:\Users\Dell\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"
    
    config._settings = config.AppSettings(
        llama_server_path=server_exe,
        model_path=llama_path,
        model_name="Llama-3.2-3B",
        model_device="Vulkan1",
        gpu_layers=33,
        context_size=4096,
        server_host="127.0.0.1",
        server_port=8080
    )
    
    print("[1] Initializing LlamaCppAdapter and ModelGateway...")
    adapter = LlamaCppAdapter()
    gateway = ModelGateway(adapter)
    
    status = gateway.get_status()
    print(f"    Initial Gateway Status: {status}")
    
    # 1 & 2 & 3: Normal inference request (should auto-start server via adapter)
    print("\n[2] Testing Normal Inference Request (response_format=None)...")
    req_normal = InferenceRequest(prompt="What is the capital of France? Answer in one word.", max_tokens=32, temperature=0.1)
    resp_normal = gateway.generate(req_normal)
    print(f"    Normal Response: {resp_normal.text.strip()}")
    print(f"    Usage: {resp_normal.usage}")
    print(f"    Stop Reason: {resp_normal.stop_reason}")
    assert len(resp_normal.text) > 0
    print("    Normal inference PASSED.")
    
    # 4 & 5 & 6: Representative FINAL decision
    print("\n[3] Testing Structured FINAL Decision...")
    prompt_final = "Task: Report the capital of France.\nCurrent State: {}\nSupported actions: FINAL, RETRIEVE, TOOL, CLARIFY, CONTINUE.\nDecide your next action."
    req_final = InferenceRequest(prompt=prompt_final, response_format=AGENT_DECISION_RESPONSE_FORMAT, max_tokens=256, temperature=0.2)
    resp_final = gateway.generate(req_final)
    print(f"    Raw Output: {resp_final.text.strip()}")
    dec_final = ModelOutputParser.parse_decision(resp_final.text)
    print(f"    Parsed Decision: action={dec_final.action}, answer={dec_final.answer}")
    assert isinstance(dec_final, AgentDecision)
    assert dec_final.action in [AgentAction.FINAL, AgentAction.RETRIEVE]
    print("    Structured FINAL decision PASSED.")
    
    # 7: Representative RETRIEVE decision
    print("\n[4] Testing Structured RETRIEVE Decision...")
    prompt_retrieve = "Task: Retrieve document 404 from the knowledge base.\nCurrent State: {}\nSupported actions: FINAL, RETRIEVE, TOOL, CLARIFY, CONTINUE.\nDecide your next action."
    req_retrieve = InferenceRequest(prompt=prompt_retrieve, response_format=AGENT_DECISION_RESPONSE_FORMAT, max_tokens=256, temperature=0.2)
    resp_retrieve = gateway.generate(req_retrieve)
    print(f"    Raw Output: {resp_retrieve.text.strip()}")
    dec_retrieve = ModelOutputParser.parse_decision(resp_retrieve.text)
    print(f"    Parsed Decision: action={dec_retrieve.action}, query={dec_retrieve.query}")
    assert isinstance(dec_retrieve, AgentDecision)
    print("    Structured RETRIEVE decision PASSED.")

    # 8: Representative TOOL decision
    print("\n[5] Testing Structured TOOL Decision...")
    prompt_tool = "Task: Execute the local_time tool.\nCurrent State: {}\nSupported actions: FINAL, RETRIEVE, TOOL, CLARIFY, CONTINUE.\nDecide your next action."
    req_tool = InferenceRequest(prompt=prompt_tool, response_format=AGENT_DECISION_RESPONSE_FORMAT, max_tokens=256, temperature=0.2)
    resp_tool = gateway.generate(req_tool)
    print(f"    Raw Output: {resp_tool.text.strip()}")
    dec_tool = ModelOutputParser.parse_decision(resp_tool.text)
    print(f"    Parsed Decision: action={dec_tool.action}, tool_name={dec_tool.tool_name}")
    assert isinstance(dec_tool, AgentDecision)
    print("    Structured TOOL decision PASSED.")

    # 9: Representative CLARIFY decision
    print("\n[6] Testing Structured CLARIFY Decision...")
    prompt_clarify = "Task: Ask the user for clarification about their missing account ID.\nCurrent State: {}\nSupported actions: FINAL, RETRIEVE, TOOL, CLARIFY, CONTINUE.\nDecide your next action."
    req_clarify = InferenceRequest(prompt=prompt_clarify, response_format=AGENT_DECISION_RESPONSE_FORMAT, max_tokens=256, temperature=0.2)
    resp_clarify = gateway.generate(req_clarify)
    print(f"    Raw Output: {resp_clarify.text.strip()}")
    dec_clarify = ModelOutputParser.parse_decision(resp_clarify.text)
    print(f"    Parsed Decision: action={dec_clarify.action}, question={dec_clarify.question}")
    assert isinstance(dec_clarify, AgentDecision)
    print("    Structured CLARIFY decision PASSED.")

    # 10: Representative CONTINUE decision
    print("\n[7] Testing Structured CONTINUE Decision...")
    prompt_continue = "Task: Continue reasoning and state your internal rationale before taking further actions.\nCurrent State: {}\nSupported actions: FINAL, RETRIEVE, TOOL, CLARIFY, CONTINUE.\nDecide your next action."
    req_continue = InferenceRequest(prompt=prompt_continue, response_format=AGENT_DECISION_RESPONSE_FORMAT, max_tokens=256, temperature=0.2)
    resp_continue = gateway.generate(req_continue)
    print(f"    Raw Output: {resp_continue.text.strip()}")
    dec_continue = ModelOutputParser.parse_decision(resp_continue.text)
    print(f"    Parsed Decision: action={dec_continue.action}, rationale={dec_continue.rationale}")
    assert isinstance(dec_continue, AgentDecision)
    print("    Structured CONTINUE decision PASSED.")

    # 11: Intentionally semantically invalid decision rejection test
    print("\n[8] Testing Semantic Rejection of Invalid Output via Pydantic...")
    invalid_samples = [
        '{"action": "FINAL"}', # Missing answer
        '{"action": "FINAL", "answer": ""}', # Empty answer
        '{"action": "TOOL"}', # Missing tool_name
        '{"action": "RETRIEVE"}', # Missing query
        '{"action": "CLARIFY"}', # Missing question
        '{"action": "CONTINUE"}' # Missing rationale
    ]
    for sample in invalid_samples:
        rejected = False
        try:
            ModelOutputParser.parse_decision(sample)
        except ValueError:
            rejected = True
        assert rejected, f"Failed to reject invalid sample: {sample}"
        print(f"    Successfully rejected: {sample}")
    print("    Semantic rejection test PASSED.")

    clean_llama()
    print("\nALL REAL HARDWARE VALIDATION CHECKS PASSED.")

if __name__ == "__main__":
    run_hardware_validation()
