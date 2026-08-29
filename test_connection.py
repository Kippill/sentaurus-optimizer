import subprocess

VM = "sentaurus-vm"
PROJECT = "/home/student/sentaurus/diod_heterostructure_1"

result = subprocess.run(
    [
        "ssh",
        VM,
        f"cd {PROJECT} && pwd && which sde && which sdevice"
    ],
    capture_output=True,
    text=True
)

print("Return code:", result.returncode)
print(result.stdout)

if result.stderr:
    print("STDERR:")
    print(result.stderr)