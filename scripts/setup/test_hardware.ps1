param (
    [string]$ModelPath = "C:\Users\Dell\.cache\huggingface\hub\models--Qwen--Qwen3-8B-GGUF\snapshots\7c41481f57cb95916b40956ab2f0b139b296d974\Qwen3-8B-Q4_K_M.gguf",
    [string]$LlamaServerPath = "C:\Users\Dell\AppData\Local\Microsoft\WinGet\Packages\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-server.exe"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting Hardware Validation for Package 01..." -ForegroundColor Cyan

# 1. Setup environment for test
$env:MODEL_PATH = $ModelPath
$env:LLAMA_SERVER_PATH = $LlamaServerPath
$env:CONTEXT_SIZE = 8192
$env:GPU_LAYERS = 20

# 2. Start server via Python adapter
Write-Host "`nTesting Adapter Lifecycle..." -ForegroundColor Yellow
$pythonTest = @"
from sovereign.core.runtime.models import InferenceRequest
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
import time

print('Initializing adapter...')
adapter = LlamaCppAdapter()
print(f'Initial status: {adapter.get_status().value}')

print('Starting inference...')
# generate() automatically starts the server if it's not running
request = InferenceRequest(prompt='Who are you?', max_tokens=20)
start_time = time.time()
response = adapter.generate(request)
end_time = time.time()

print(f'Status after start: {adapter.get_status().value}')
print(f'Response: {response.text.strip()}')
print(f'Latency: {end_time - start_time:.2f}s')
print(f'Usage: {response.usage}')

print('Testing Context Overflow Rejection...')
try:
    oversized_prompt = 'a ' * 20000  # Will definitely estimate > 8192 tokens
    req = InferenceRequest(prompt=oversized_prompt, max_tokens=10)
    adapter.generate(req)
    print('FAIL: Oversized request was not rejected.')
except Exception as e:
    print(f'SUCCESS: Oversized request rejected correctly -> {type(e).__name__}: {e}')

print('Testing Streaming...')
stream_req = InferenceRequest(prompt='Count from 1 to 5.', max_tokens=20, stream=True)
chunks = list(adapter.stream(stream_req))
print(f'Stream received {len(chunks)} chunks.')

print('Stopping server...')
adapter._lifecycle.stop()
print(f'Final status: {adapter.get_status().value}')
"@

$testFile = "test_hardware_temp.py"
Set-Content -Path $testFile -Value $pythonTest

$activateScript = ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    $env:PYTHONPATH = "src"
    python $testFile
} else {
    Write-Error "Virtual environment not found."
}

Remove-Item -Path $testFile -Force
Write-Host "Hardware Validation Complete." -ForegroundColor Cyan
