"""Run one unittest target in this process and report its peak working set."""
import ctypes, os, pathlib, sys, unittest
from ctypes import wintypes
# 저장소 위치는 이 파일의 위치에서 유도한다 — 다른 PC 에서도 그대로 돈다.
ROOT = pathlib.Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
os.chdir(ROOT)

class PMC(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

# 64비트 핸들이 int 로 잘리면 호출이 조용히 실패한다 — restype/argtypes 를 반드시 준다.
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.GetCurrentProcess.restype = wintypes.HANDLE
psapi = ctypes.WinDLL("psapi", use_last_error=True)
psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

def peak_mb():
    p = PMC(); p.cb = ctypes.sizeof(PMC)
    if psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(p), p.cb):
        return p.PeakWorkingSetSize >> 20, p.WorkingSetSize >> 20
    return -ctypes.get_last_error(), -1

target = sys.argv[1]
suite = unittest.defaultTestLoader.loadTestsFromName(target)
result = unittest.TextTestRunner(verbosity=0).run(suite)
pk, now = peak_mb()
print(f"TARGET {target}")
print(f"RAN {result.testsRun}  FAIL {len(result.failures)}  ERR {len(result.errors)}  "
      f"SKIP {len(result.skipped)}")
for who, _ in result.failures: print("  FAIL:", who)
for who, _ in result.errors:   print("  ERR :", who)
print(f"PEAK_MB {pk}  END_MB {now}")
