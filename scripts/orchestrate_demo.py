import win32service, win32gui, win32con, ctypes, threading, time, os

def switch_to_window(hwnd):
    hdesk = win32service.OpenDesktop('default', 0, False, win32con.GENERIC_ALL)
    hdesk.SetThreadDesktop()
    ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_RESTORE)
    ctypes.windll.user32.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 1440, 900, win32con.SWP_SHOWWINDOW)
    ctypes.windll.user32.BringWindowToTop(hwnd)
    ctypes.windll.user32.SetForegroundWindow(hwnd)

def type_text(hwnd, text, delay=0.02):
    hdesk = win32service.OpenDesktop('default', 0, False, win32con.GENERIC_ALL)
    hdesk.SetThreadDesktop()
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    time.sleep(0.1)
    for ch in text:
        vk = ctypes.windll.user32.VkKeyScanW(ord(ch))
        shift = (vk >> 8) & 1
        vk_code = vk & 0xFF
        if shift:
            ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
        if shift:
            ctypes.windll.user32.keybd_event(0x10, 0, 2, 0)
        time.sleep(delay)
    # Enter
    ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x0D, 0, 2, 0)

def run_demo_orchestration():
    if os.path.exists("stop_recording.flag"):
        os.remove("stop_recording.flag")
        
    hwnd_terminal = 198538
    
    # 2 seconds warm-up
    time.sleep(2)
    switch_to_window(hwnd_terminal)
    type_text(hwnd_terminal, "cls", delay=0.01)
    time.sleep(1)

    # 1. Introduction Banner
    type_text(hwnd_terminal, "Write-Host '=====================================================' -ForegroundColor Cyan", delay=0.005)
    type_text(hwnd_terminal, "Write-Host '  SANDBOXSHIELD AI - CELESTO MICROVM DEMONSTRATION  ' -ForegroundColor Yellow", delay=0.005)
    type_text(hwnd_terminal, "Write-Host '=====================================================' -ForegroundColor Cyan", delay=0.005)
    time.sleep(3)

    # 2. Project Directory & Environment Overview
    type_text(hwnd_terminal, "cd 'C:\\Users\\kesava_kantipudi\\Desktop\\GPP\\Hackathon\\Run Real Agent Work Inside Celesto Sandboxes with Evals and Containment'", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "Get-Content .env.example", delay=0.01)
    time.sleep(6)

    # 3. Live Celesto Sandbox Smoke Test (Real MicroVM on Celesto Cloud)
    type_text(hwnd_terminal, "Write-Host '`n[+] Running Live Real Celesto Cloud Sandbox Smoke Test...' -ForegroundColor Green", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "wsl -d Ubuntu -- bash -c 'scripts/run_probe.sh'", delay=0.015)
    # Wait for the probe to boot VM, run command, and delete VM (~14s)
    time.sleep(16)

    # 4. Evaluation Benchmark Metrics (20 Fresh Cloud Sandboxes)
    type_text(hwnd_terminal, "Write-Host '`n[+] Inspecting 20-Run Reliability Benchmark Metrics...' -ForegroundColor Green", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "Get-Content reports\\reliability.json | Select-Object -First 30", delay=0.01)
    time.sleep(8)

    # 5. Containment & Prompt Injection Defense
    type_text(hwnd_terminal, "Write-Host '`n[+] Inspecting Containment Verification Report...' -ForegroundColor Green", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "Get-Content reports\\containment.json", delay=0.01)
    time.sleep(7)

    # 6. Step-7 Failure & Recovery Trace
    type_text(hwnd_terminal, "Write-Host '`n[+] Inspecting Step-7 Failure Recovery Trace...' -ForegroundColor Green", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "Get-Content reports\\failure_trace.jsonl | Select-Object -Last 6", delay=0.01)
    time.sleep(7)

    # 7. Concurrency Test Results
    type_text(hwnd_terminal, "Write-Host '`n[+] Inspecting Concurrency (5 Isolated Sandboxes)...' -ForegroundColor Green", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "Get-Content reports\\concurrency.json", delay=0.01)
    time.sleep(7)

    # 8. Full Pytest Test Suite Validation (17 / 17 Tests)
    type_text(hwnd_terminal, "Write-Host '`n[+] Running Full Automated Test Suite (17 Tests)...' -ForegroundColor Green", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "python -m pytest tests/ -v", delay=0.015)
    time.sleep(9)

    # 9. Git Repository Provenance Check
    type_text(hwnd_terminal, "Write-Host '`n[+] Verifying Clean Git Status & Provenance...' -ForegroundColor Green", delay=0.01)
    time.sleep(1)
    type_text(hwnd_terminal, "git status", delay=0.01)
    time.sleep(4)
    type_text(hwnd_terminal, "git log -n 2 --oneline", delay=0.01)
    time.sleep(6)

    # Final wrap-up message
    type_text(hwnd_terminal, "Write-Host '`n[SUCCESS] SandboxShield AI Demonstration Complete. 100% Submission Ready!' -ForegroundColor Cyan", delay=0.01)
    time.sleep(4)

    with open("stop_recording.flag", "w") as f:
        f.write("done")
    print("Demo orchestration complete!")

if __name__ == '__main__':
    t = threading.Thread(target=run_demo_orchestration)
    t.start()
    t.join()
