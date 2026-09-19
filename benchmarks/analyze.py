import json
import os

path = os.path.join(os.path.dirname(__file__), 'results', 'benchmark_results.json')
if not os.path.exists(path):
    path = 'benchmark_results.json'

data = json.load(open(path))
print("--- MODEL SUMMARY ---")
for d in data:
    print(f"{d['Model']} | {d['Config']} | JSON: {d['JSON_Valid']}/50 | AD: {d['AD_Valid']}/50 | Latency: {d['Avg_Latency']:.2f}s")
