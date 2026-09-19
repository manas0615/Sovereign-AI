from sovereign.infrastructure.config import get_settings
from sovereign.core.runtime.models import InferenceRequest
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
import time

settings = get_settings()
print(f"Loaded config:")
print(f" - Model: {settings.model_name}")
print(f" - Context Size: {settings.context_size}")
print(f" - GPU Layers: {settings.gpu_layers}")
print(f" - Path: {settings.model_path}")

print("\nInitializing adapter...")
adapter = LlamaCppAdapter()
print(f"Initial status: {adapter.get_status().value}")

print("\nStarting inference (will spin up llama-server)...")
request = InferenceRequest(prompt='Hello, tell me a very short joke.', max_tokens=30)
start_time = time.time()
response = adapter.generate(request)
end_time = time.time()

print(f"\nStatus after start: {adapter.get_status().value}")
print(f"Response: {response.text.strip()}")
print(f"Latency: {end_time - start_time:.2f}s")
print(f"Usage: {response.usage}")

print("\nStopping server...")
adapter._lifecycle.stop()
print(f"Final status: {adapter.get_status().value}")
