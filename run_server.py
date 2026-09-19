import sys
import os
from pathlib import Path

# Ensure src/ is in python path
src_dir = Path(__file__).resolve().parent / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

if __name__ == '__main__':
    import uvicorn
    print(f'Starting Sovereign AI API server on http://127.0.0.1:8000 (app-dir: {src_dir})...')
    uvicorn.run('sovereign.application.api:app', host='127.0.0.1', port=8000, reload=True, app_dir=str(src_dir))
