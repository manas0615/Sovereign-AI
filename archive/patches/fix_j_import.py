with open('exp_j_suite.py', 'r') as f:
    content = f.read()

content = content.replace("from sovereign.infrastructure.runtime.llama_cpp_adapter import LlamaCppAdapter", "from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter")

with open('exp_j_suite.py', 'w') as f:
    f.write(content)
