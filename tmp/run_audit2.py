import subprocess
result = subprocess.run(['python3', '/tmp/analyze_audit2.py'], capture_output=True, text=True, timeout=30)
print(result.stdout[:15000])
if result.stderr:
    print("STDERR:", result.stderr[:3000])
