import sys, math, csv, statistics as st
sys.path.insert(0, r"C:\dev\Nconnect\tools")
from pathlib import Path
import numpy as np
from go2_climb_count import alive_rows, gained_steps
K = Path(r"C:\dev\Nconnect\workspace\_keep")
RUNS = {"A033":"go2_g_a033_a017_track_lin_vel_xy_150","A044":"go2_g_a044_a033_lin_vel_z_m175","A043":"go2_g_a043_a033_lin_vel_z_m15","A050":"go2_g_a050_a033_lin_vel_z_m1375","A048":"go2_g_a048_a033_lin_vel_z_m125","A049":"go2_g_a049_a033_lin_vel_z_m1"}
DT = 0.02
out = []
for arm, d in RUNS.items():
    for seed in (101, 202, 303):
        for case, h in (("stairs_10_down", .10), ("stairs_15_down", .15)):
            p = K / d / f"evaluation/candidate/cases/seed_{seed}/{case}/steps.csv"
            # all rows incl. after termination for fall time
            by = alive_rows(p)
            for env, rows in by.items():
                n = len(rows)
                g = gained_steps(rows, "climb", h)
                A = lambda k: np.array([float(r[k]) for r in rows])
                z, tz, hr, pg, sp, vx, vy, wz = A("root_z"), A("terrain_z"), A("height_rel"), A("proj_grav_z"), A("speed_xy"), A("actual_vx"), A("actual_vy"), A("actual_wz")
                tilt = np.degrees(np.arccos(np.clip(-pg, -1, 1)))
                vz = np.gradient(z, DT)
                rec = dict(arm=arm, seed=seed, case=case, env=env, steps=g, alive_s=n*DT)
                a0, a1 = 50, min(150, n)  # approach 1-3 s
                if a1 - a0 > 50:
                    zz = z[a0:a1] - np.polyval(np.polyfit(np.arange(a1-a0), z[a0:a1], 1), np.arange(a1-a0))
                    f = np.fft.rfftfreq(len(zz), DT); P = np.abs(np.fft.rfft(zz))**2; P[0] = 0
                    band = (f > 0.8)
                    rec.update(ap_hrel=hr[a0:a1].mean(), ap_tilt=tilt[a0:a1].mean(), ap_speed=sp[a0:a1].mean(),
                               ap_vz_rms=math.sqrt((vz[a0:a1]**2).mean()), ap_bob_hz=f[band][P[band].argmax()],
                               ap_bob_amp=zz.std(), ap_vy=abs(vy[a0:a1]).mean(), ap_wz=abs(wz[a0:a1]).mean())
                tz0 = tz[min(50, n-1)]
                edge = next((i for i in range(50, n) if tz[i] - tz0 > 0.5*h), None)
                rec["reached_edge"] = edge is not None
                if edge is not None:
                    w0, w1 = max(0, edge-25), min(n, edge+75)
                    z0 = z[max(0, edge-25)]
                    rec.update(t_edge=edge*DT, ed_rise=(z[w0:w1]-z0).max(), ed_vz_max=vz[w0:w1].max(),
                               ed_tilt_max=tilt[w0:w1].max(), ed_tilt_mean=tilt[w0:w1].mean(),
                               ed_hrel_min=hr[w0:w1].min(), ed_speed_min=sp[edge:w1].min() if w1>edge else float('nan'),
                               ed_vx_mean=vx[edge:w1].mean() if w1>edge else float('nan'),
                               pre_hrel=hr[max(0,edge-25):edge].mean() if edge>0 else float('nan'),
                               pre_tilt=tilt[max(0,edge-25):edge].mean() if edge>0 else float('nan'),
                               pre_speed=sp[max(0,edge-25):edge].mean() if edge>0 else float('nan'))
                out.append(rec)
keys = sorted({k for r in out for k in r})
with open(Path(sys.argv[1]), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)
def med(rows, k):
    v = [r[k] for r in rows if k in r and not (isinstance(r[k], float) and math.isnan(r[k]))]
    return (st.median(v), len(v)) if v else (float('nan'), 0)
metrics = ["ap_hrel","ap_tilt","ap_speed","ap_vz_rms","ap_bob_hz","ap_bob_amp","ap_vy","ap_wz","pre_hrel","pre_tilt","pre_speed","ed_rise","ed_vz_max","ed_tilt_max","ed_tilt_mean","ed_hrel_min","ed_speed_min","ed_vx_mean"]
for case in ("stairs_10_down","stairs_15_down"):
    for grp, cond in (("ALL", lambda r: True), ("climb>=2", lambda r: r["steps"]>=2), ("climb<2", lambda r: r["steps"]<2)):
        print(f"\n== {case} {grp}")
        for arm in RUNS:
            rs = [r for r in out if r["arm"]==arm and r["case"]==case and cond(r)]
            edge = sum(r["reached_edge"] for r in rs)
            print(f"  {arm} n={len(rs)} edge={edge} " + " ".join(f"{m}={med(rs,m)[0]:.3f}" for m in metrics))
