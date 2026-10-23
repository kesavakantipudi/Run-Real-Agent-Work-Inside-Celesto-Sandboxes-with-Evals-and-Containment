"""
Probe real Celesto Cloud sandbox creation, execution, and cleanup.
Uses the correct Celesto 0.1.8 SDK API:
- Computer(provider="cloud")
- comp.start()
- comp.run("command", timeout=30)
- comp.id and comp._provider.vm_id
- comp.delete()
- comp.close()
"""

import os
import sys
import time

api_key = os.environ.get("CELESTO_API_KEY", "")
provider = os.environ.get("CELESTO_PROVIDER", "cloud")

print(f"CELESTO_PROVIDER: {provider}")
print(f"CELESTO_API_KEY present: {bool(api_key)}")
print(f"CELESTO_API_KEY length: {len(api_key)}")

if not api_key or api_key in ["replace-me", "placeholder"]:
    print("ERROR: CELESTO_API_KEY is not set or contains placeholder value.")
    sys.exit(1)

# Import Celesto Computer
try:
    from celesto import Computer
    print("Successfully imported celesto.Computer")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

comp = None
exit_code = 1
stdout = ""
stderr = ""
cleanup_ok = False
computer_id = "N/A"
vm_id = "N/A"
boot_time = 0.0

try:
    t0 = time.time()
    print("Initializing Computer(provider=provider)...")
    comp = Computer(provider=provider)
    print("Calling comp.start()...")
    comp.start()
    boot_time = time.time() - t0
    computer_id = comp.id
    if hasattr(comp, "_provider") and hasattr(comp._provider, "vm_id"):
        vm_id = comp._provider.vm_id
    print(f"comp.start() succeeded in {boot_time:.2f}s! Computer ID: {computer_id}, VM ID: {vm_id}")

    print("Executing harmless guest command: echo REAL_CELESTO_SANDBOX_OK")
    res = comp.run("echo REAL_CELESTO_SANDBOX_OK", timeout=30)
    exit_code = res.exit_code
    stdout = res.stdout
    stderr = res.stderr
    print(f"Command execution exit_code: {exit_code}")
    print(f"Stdout:\n{stdout}")
    print(f"Stderr:\n{stderr}")
except Exception as e:
    print(f"Execution failed with exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
finally:
    if comp:
        print("Cleaning up sandbox...")
        try:
            comp.delete()
            print("comp.delete() completed.")
            cleanup_ok = True
        except Exception as de:
            print(f"comp.delete() error: {de}")
        try:
            comp.close()
            print("comp.close() completed.")
        except Exception as ce:
            print(f"comp.close() error: {ce}")

print("\n--- SUMMARY REPORT ---")
print(f"Computer ID: {computer_id}")
print(f"VM ID: {vm_id}")
print(f"Provider: {provider}")
print(f"Boot Duration: {boot_time:.3f}s")
print(f"Exit Code: {exit_code}")
print(f"Stdout Content: {repr(stdout)}")
print(f"Contains REAL_CELESTO_SANDBOX_OK: {'REAL_CELESTO_SANDBOX_OK' in stdout}")
print(f"Cleanup Successful: {cleanup_ok}")
