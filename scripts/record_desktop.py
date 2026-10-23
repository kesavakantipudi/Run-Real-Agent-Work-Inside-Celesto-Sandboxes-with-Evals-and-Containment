import win32service, win32gui, win32ui, win32con, win32api, subprocess, time, threading, os

def record_screen(output_path, duration=150, fps=15):
    hdesk = win32service.OpenDesktop('default', 0, False, win32con.GENERIC_ALL)
    hdesk.SetThreadDesktop()
    w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    h = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    hwnd = win32gui.GetDesktopWindow()
    wnd_dc = win32gui.GetWindowDC(hwnd)
    dc = win32ui.CreateDCFromHandle(wnd_dc)
    mem_dc = dc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(dc, w, h)
    mem_dc.SelectObject(bmp)
    
    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{w}x{h}',
        '-pix_fmt', 'bgra',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'fast',
        '-crf', '22',
        output_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total_frames = int(duration * fps)
    frame_interval = 1.0 / fps
    start_t = time.time()
    
    try:
        for i in range(total_frames):
            if os.path.exists("stop_recording.flag"):
                print("Stop flag detected, finishing recording early...")
                break
            mem_dc.BitBlt((0, 0), (w, h), dc, (0, 0), win32con.SRCCOPY)
            bits = bmp.GetBitmapBits(True)
            proc.stdin.write(bits)
            next_t = start_t + (i + 1) * frame_interval
            sleep_t = next_t - time.time()
            if sleep_t > 0:
                time.sleep(sleep_t)
    finally:
        proc.stdin.close()
        proc.wait()
        dc.DeleteDC()
        mem_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, wnd_dc)
        win32gui.DeleteObject(bmp.GetHandle())
        print(f"Screen recording completed: {output_path}")

if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "demo/walkthrough.mp4"
    dur = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    t = threading.Thread(target=record_screen, args=(out, dur))
    t.start()
    t.join()
