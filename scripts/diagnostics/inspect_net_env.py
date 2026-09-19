import os
import sys
import socket
import psutil
import json
from sovereign.infrastructure.config import get_settings

settings = get_settings()
print("=== SOVEREIGN AI ENVIRONMENT & CONFIGURATION ===")
print("OS:", sys.platform)
print("Python:", sys.version)
print("Backend Host:", settings.host)
print("Backend Port:", settings.port)
print("Model Name:", settings.model_name)
print("Model Path:", settings.model_path)
print("Model Device:", settings.model_device)
print("GPU Layers:", settings.gpu_layers)
print("Context Size:", settings.context_size)

print("\n=== ACTIVE NETWORK INTERFACES ===")
for iface, addrs in psutil.net_if_addrs().items():
    ip_list = [a.address for a in addrs if a.family == socket.AF_INET]
    if ip_list:
        print(f"Interface: {iface} -> IPv4: {ip_list}")
