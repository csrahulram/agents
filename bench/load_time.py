"""Measure llama-server load time, GPU memory and first-request latency for each model.

  python bench/load_time.py              # all models, 3 warm runs each
  python bench/load_time.py --runs 1

Cold load (file not in the Windows cache) is estimated as:
  warm load + file size / uncached drive read speed
because Windows keeps recently read files in RAM, so a true cold load can't be repeated.
"""
import argparse
import ctypes
import json
import os
import subprocess
import time
import urllib.request
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "tools" / "llama.cpp" / "llama-server.exe"
MODELS = Path(os.environ.get("MODELS_DIR", r"E:\models\gguf"))
PORT = 8199

# name, model file, extra args
CASES = [
    ("coder-1.5b", "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf", ["-c", "8192", "--parallel", "4"]),
    ("general-1b", "MiniCPM5-1B-Q4_K_M.gguf", ["-c", "8192"]),
    ("vision", "MiniCPM-V-4_6-Q4_K_M.gguf", ["-c", "4096", "--mmproj", str(MODELS / "MiniCPM-V-4_6-mmproj-f16.gguf")]),
    ("embed", "nomic-embed-text-v1.5.Q8_0.gguf", ["-c", "2048", "--embedding"]),
    ("coder-3b", "qwen2.5-coder-3b-instruct-q4_k_m.gguf", ["-c", "8192"]),
]


def gpu_used_mb():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout
    return int(out.strip().splitlines()[0])


def get(path, timeout=2):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=timeout) as r:
        return r.status, r.read()


def post(path, payload, timeout=120):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def measure(name, file, extra):
    base = gpu_used_mb()
    cmd = [str(SERVER), "-m", str(MODELS / file), "-ngl", "99", "--port", str(PORT), "--host", "127.0.0.1", *extra]
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while True:
            if proc.poll() is not None:
                raise RuntimeError(f"{name}: server exited with code {proc.returncode}")
            try:
                if get("/health")[0] == 200:
                    break
            except Exception:
                pass
            if time.perf_counter() - t0 > 180:
                raise RuntimeError(f"{name}: not ready after 180 s")
            time.sleep(0.05)
        load = time.perf_counter() - t0
        vram = gpu_used_mb() - base
        t1 = time.perf_counter()
        if "--embedding" in extra:
            post("/v1/embeddings", {"input": "hello world"})
        else:
            post("/v1/chat/completions", {"messages": [{"role": "user", "content": "Say OK."}],
                                          "max_tokens": 8, "temperature": 0})
        first = time.perf_counter() - t1
        return load, vram, first
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
        time.sleep(1.5)  # let the driver release memory before the next run


def uncached_read_mb_s(path, limit=512 * 1024 * 1024):
    """Read a file with FILE_FLAG_NO_BUFFERING so the Windows cache is bypassed."""
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    k32.VirtualAlloc.restype = ctypes.c_void_p
    k32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
    k32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD]
    k32.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                             ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k32.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x20000000 | 0x08000000, None)
    if h in (None, ctypes.c_void_p(-1).value):
        raise OSError(ctypes.get_last_error())
    chunk = 8 * 1024 * 1024
    buf = k32.VirtualAlloc(None, chunk, 0x3000, 0x04)  # page-aligned buffer, required for unbuffered reads
    read, got = 0, wintypes.DWORD()
    t0 = time.perf_counter()
    while read < limit and k32.ReadFile(h, buf, chunk, ctypes.byref(got), None) and got.value:
        read += got.value
    dt = time.perf_counter() - t0
    k32.CloseHandle(h)
    k32.VirtualFree(buf, 0, 0x8000)
    return read / 1e6 / dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--drives", default=r"E:\models\gguf,D:\Projects\agents\models,C:\models-test",
                    help="folders holding a copy of the coder file, for drive speed")
    args = ap.parse_args()

    results = {}
    for name, file, extra in CASES:
        runs = [measure(name, file, extra) for _ in range(args.runs)]
        load = sorted(r[0] for r in runs)[len(runs) // 2]
        vram = max(r[1] for r in runs)
        first = sorted(r[2] for r in runs)[len(runs) // 2]
        size = (MODELS / file).stat().st_size / 1e6
        if "--mmproj" in extra:
            size += (MODELS / "MiniCPM-V-4_6-mmproj-f16.gguf").stat().st_size / 1e6
        results[name] = {"file_mb": round(size), "warm_load_s": round(load, 2),
                         "gpu_mb": vram, "first_request_s": round(first, 2)}
        print(f"{name:<12} file {size:6.0f} MB  warm load {load:5.2f} s  GPU {vram:5d} MB  first request {first:5.2f} s")

    speeds = {}
    probe = CASES[0][1]
    for folder in args.drives.split(","):
        p = Path(folder) / probe
        if p.exists():
            speeds[folder[:2]] = max(1, round(uncached_read_mb_s(p)))
            print(f"uncached read {folder[:2]}  {speeds[folder[:2]]} MB/s")

    print("\nEstimated cold load (warm load + file / drive speed):")
    print(f"{'model':<12}" + "".join(f"{d:>10}" for d in speeds))
    for name, r in results.items():
        row = "".join(f"{r['warm_load_s'] + r['file_mb'] / s:9.1f}s" for s in speeds.values())
        print(f"{name:<12}{row}")
    out = ROOT / "bench" / "load_time.json"
    out.write_text(json.dumps({"results": results, "drive_mb_s": speeds}, indent=2))
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
