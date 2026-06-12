"""Runner: chạy toàn bộ pipeline Phase 1–9 trong cùng namespace."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

_show_count = [0]


def _auto_save(*args, **kwargs):
    _show_count[0] += 1
    fname = f"d:/Python/output_fig_{_show_count[0]:02d}.png"
    plt.savefig(fname, bbox_inches="tight", dpi=100)
    print(f"[Biểu Đồ lưu] {fname}")
    plt.close("all")
plt.show = _auto_save

_ns = {"__name__": "__main__", "plt": plt}

phases = [
    "d:/Python/phase1_rainfall_preprocessing.py",
    "d:/Python/phase2_eda.py",
    "d:/Python/phase3_feature_engineering.py",
    "d:/Python/phase4_modeling.py",
    "d:/Python/phase5_evaluation.py",
    "d:/Python/phase6_residual_diagnostics.py",
    "d:/Python/phase7_forecast.py",
    "d:/Python/phase8_report_conclusions.py",
]

for phase_file in phases:
    print("\n" + "#" * 70)
    print(f"# CHẠY: {phase_file}")
    print("#" * 70)
    with open(phase_file, encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, phase_file, "exec"), _ns)

print("\n" + "=" * 70)
print("TẤT CẢ PHASE ĐÃ HOÀN THÀNH")
print("=" * 70)
