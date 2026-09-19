import os
import psutil
import time
import json
from datetime import datetime

print("=========================================================")
print(" SOVEREIGN AI - NETWORK OBSERVATION UTILITY")
print("=========================================================")
print("WARNING: This is an observational auditing tool, not a ")
print("firewall. It inspects established and listening sockets")
print("for relevant application processes. It does NOT block ")
print("outbound traffic or enforce a physical air gap.")
print("=========================================================\n")

def get_target_processes():
    targets = {}
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name'].lower()
            if 'python' in name or 'node' in name or 'llama-server' in name:
                targets[proc.info['pid']] = proc.info
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return targets

def monitor_network(duration_seconds=10, interval=2):
    log_file = f"network_audit_{int(time.time())}.json"
    observations = []
    
    start_time = time.time()
    print(f"[*] Starting {duration_seconds}s network audit for Python, Node, and Llama processes...")
    
    while time.time() - start_time < duration_seconds:
        targets = get_target_processes()
        current_obs = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "connections": []
        }
        
        for pid, pinfo in targets.items():
            try:
                proc = psutil.Process(pid)
                conns = proc.connections(kind='inet')
                for c in conns:
                    laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A"
                    raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"
                    
                    is_loopback = False
                    if c.raddr:
                        if c.raddr.ip.startswith("127.") or c.raddr.ip == "::1":
                            is_loopback = True
                    elif c.laddr:
                        if c.laddr.ip.startswith("127.") or c.laddr.ip == "::1" or c.laddr.ip == "0.0.0.0":
                            is_loopback = True
                            
                    current_obs["connections"].append({
                        "pid": pid,
                        "process": pinfo['name'],
                        "laddr": laddr,
                        "raddr": raddr,
                        "status": c.status,
                        "is_loopback": is_loopback
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        observations.append(current_obs)
        
        # Print summary
        non_loopback = [c for c in current_obs["connections"] if not c["is_loopback"] and c["status"] == "ESTABLISHED"]
        if non_loopback:
            print(f"[!] WARNING: Found {len(non_loopback)} non-loopback established connections!")
            for c in non_loopback:
                print(f"    {c['process']} (PID {c['pid']}) -> {c['raddr']}")
        else:
            print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] OK: All {len(current_obs['connections'])} observed sockets are local/loopback or listening.")
            
        time.sleep(interval)
        
    with open(log_file, "w") as f:
        json.dump(observations, f, indent=2)
        
    print(f"\n[*] Audit complete. Machine-readable log saved to {log_file}")

if __name__ == "__main__":
    monitor_network(10, 2)
