import json
data = json.load(open('benchmark_results.json'))
print("--- MODEL SUMMARY ---")
for d in data:
    print(f"{d['Model']} | {d['Config']} | JSON: {d['JSON_Valid']}/50 | AD: {d['AD_Valid']}/50 | Latency: {d['Avg_Latency']:.2f}s")
