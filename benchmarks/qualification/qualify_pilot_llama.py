import json
import logging
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from sovereign.core.qualification.models import (
    DeploymentProfile, CapabilityContract, ModelProfile, RuntimeEnvironment, CapabilityPassport
)
from sovereign.core.qualification.engine import QualificationEngine, QualificationTestCase
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.runtime.models import ModelDeploymentConfig
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.core.agent.models import AGENT_DECISION_RESPONSE_FORMAT
from sovereign.infrastructure.paths import get_data_dir
from sovereign.infrastructure.config import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("pilot_llama")

def setup_run_directory(run_name: str) -> Path:
    base_dir = Path(__file__).parent.resolve()
    run_dir = base_dir / "runs" / run_name
    
    if run_dir.exists():
        raise FileExistsError(f"Run directory already exists: {run_dir}. Refusing to overwrite.")
    
    run_dir.mkdir(parents=True, exist_ok=False)
    
    # Path Isolation Checks
    settings = get_settings()
    primary_db = (get_data_dir() / settings.db_filename).resolve()
    pilot_db = (run_dir / "pilot.db").resolve()
    
    if pilot_db == primary_db:
        raise ValueError(f"Pilot DB path aliases primary DB: {pilot_db}")
    if pilot_db.parent != run_dir:
        raise ValueError(f"Pilot DB escaped run directory: {pilot_db}")
        
    return run_dir, pilot_db

def extract_json(txt: str) -> dict:
    try:
        return json.loads(txt)
    except Exception:
        pass
    m = re.search(r'\{.*\}', txt, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No JSON")

def validate_doc(txt: str, schema: dict) -> bool:
    try:
        d = extract_json(txt)
        return d.get("action") in ["RETRIEVE", "FINAL"]
    except Exception:
        return False

def validate_code(txt: str, schema: dict) -> bool:
    # Note: This strictly validates API schema compliance (structural), 
    # and does NOT execute untrusted code or invoke TrustedCodeVerifier.
    try:
        d = extract_json(txt)
        return d.get("action") in ["TOOL", "FINAL"]
    except Exception:
        return False

def main():
    run_name = f"llama_pilot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    run_dir, pilot_db = setup_run_directory(run_name)
    logger.info(f"Isolated run directory: {run_dir}")
    logger.info(f"Isolated database: {pilot_db}")
    
    # Strictly injected repository to prevent global state mutation
    repo = SQLiteTaskRepository(db_path=pilot_db)
    # Double check injection propagated
    if repo.db_path.resolve() != pilot_db:
        raise ValueError(f"Repository DB path injection failed. Got: {repo.db_path}")

    # Launch Monitor Script safely using parameterized launch command
    monitor_script = Path(__file__).parent / "monitor_pilot.ps1"
    logger.info(f"Starting resource monitor: powershell.exe -File monitor_pilot.ps1 -RunDir {run_dir}")
    import subprocess
    import time
    monitor_proc = subprocess.Popen(
        ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(monitor_script), "-RunDir", str(run_dir)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Detect monitor startup failure before model loading
    time.sleep(2.0)
    if monitor_proc.poll() is not None:
        raise RuntimeError(f"Monitor failed to start (exit code {monitor_proc.returncode}). Aborting pilot to preserve safety constraints.")

    # Llama Profile exactly as originally configured
    dep_llama = ModelDeploymentConfig(
        model_name="Llama-3.2-3B-Instruct",
        model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        device="Vulkan1", gpu_layers=20, context_size=8192
    )
    prof_llama = DeploymentProfile(
        model=ModelProfile(name="Llama-3.2-3B-Instruct", architecture="llama", parameters_b=3.2, context_length=8192),
        quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="Vulkan1_gl20", context_budget=8192
    )

    contract_doc = CapabilityContract(name="DocumentRetrieval_v1", version="1.0", expected_schema=AGENT_DECISION_RESPONSE_FORMAT, required_trials=1, pass_rate_threshold=1.0)
    contract_code = CapabilityContract(name="AutomatedCoding_v1", version="1.0", expected_schema=AGENT_DECISION_RESPONSE_FORMAT, required_trials=1, pass_rate_threshold=1.0)
    contract_agent = CapabilityContract(name="AgentDecision_v1", version="1.0", expected_schema=AGENT_DECISION_RESPONSE_FORMAT, required_trials=1, pass_rate_threshold=1.0)

    t_doc = QualificationTestCase(
        "t_doc",
        "You are a sovereign agent. The user says: Search for vessel inspection standards. Format: {\"action\": \"RETRIEVE\", \"query\": \"vessel inspection standards\"}",
        validate_doc
    )
    t_code = QualificationTestCase(
        "t_code",
        "You are a sovereign agent. The user says: Write python email validator. Format: {\"action\": \"TOOL\", \"tool_name\": \"execute_python\", \"arguments\": {\"code\": \"def is_valid_email(email): return True\"}}",
        validate_code
    )

    adapter = LlamaCppAdapter()
    gateway = ModelGateway(adapter)
    engine = QualificationEngine(gateway=gateway, repository=repo)

    results_meta = {
        "run_name": run_name,
        "model": prof_llama.model.name,
        "quantization": prof_llama.quantization,
        "context_size": prof_llama.context_budget,
        "gpu_layers": dep_llama.gpu_layers,
        "passports": []
    }
    
    try:
        logger.info("Initializing Llama-3.2-3B-Instruct for isolated pilot qualification...")
        adapter.switch(dep_llama)
        
        # 1. DocumentRetrieval_v1
        p1 = engine.run_qualification(prof_llama, contract_doc, [t_doc])
        results_meta["passports"].append(p1.model_dump(mode='json'))
        
        # 2. AutomatedCoding_v1
        p2 = engine.run_qualification(prof_llama, contract_code, [t_code])
        results_meta["passports"].append(p2.model_dump(mode='json'))
        
        # 3. AgentDecision_v1 (Uses t_doc as intended in original script)
        p3 = engine.run_qualification(prof_llama, contract_agent, [t_doc])
        results_meta["passports"].append(p3.model_dump(mode='json'))
        
        logger.info("Pilot qualification completed successfully.")
        results_meta["status"] = "COMPLETED"
        
    except Exception as e:
        logger.error(f"Pilot run failed: {e}", exc_info=True)
        results_meta["status"] = f"FAILED: {str(e)}"
        
    finally:
        logger.info("Attempting cleanup. Unloading adapter...")
        try:
            adapter.unload()
        except Exception as e:
            logger.error(f"Failed to cleanly unload adapter: {e}")
            results_meta["cleanup_error"] = str(e)
            
        logger.info("Stopping resource monitor...")
        try:
            if monitor_proc.poll() is None:
                monitor_proc.terminate()
                try:
                    monitor_proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning("Monitor did not terminate in time. Forcing kill on specific child PID.")
                    monitor_proc.kill()
                    monitor_proc.wait(timeout=2)
        except Exception as e:
            logger.error(f"Failed to terminate monitor process: {e}")
            
        out_path = run_dir / "run_metadata.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results_meta, f, indent=2)
        logger.info(f"Saved run metadata to {out_path}")

if __name__ == "__main__":
    main()
