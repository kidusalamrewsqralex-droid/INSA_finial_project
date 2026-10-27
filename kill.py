import subprocess

port = 1234

# Run netstat and capture output
result = subprocess.run(
    ["netstat", "-ano"],
    capture_output=True,
    text=True,
    check=True
)

# Filter lines containing the port
lines = [line for line in result.stdout.splitlines() if f":{port}" in line]

for line in lines:
    parts = line.split()
    # Typical format: Proto LocalAddr ForeignAddr State PID
    # Example: TCP    0.0.0.0:1234    0.0.0.0:0    LISTENING    5678
    if len(parts) >= 5 and parts[3].upper() == "LISTENING":
        pid = parts[-1]
        print(f"Killing PID {pid} listening on port {port}")
        kill_result = subprocess.run(
            ["taskkill", "/PID", pid, "/F"],
            capture_output=True,
            text=True
        )
        print("Kill output:", kill_result.stdout)
