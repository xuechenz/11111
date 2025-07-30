import time, numpy as np, pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
BUMP_SIZE   = 0.0025
MAX_PATHS   = 100_000
THREADS     = 16
STOCK_ID    = "AAPL.US"               

strike_edges   = np.round(np.arange(0.5, 1.5 + 0.1, 0.1), 2)      
tenor_edges_m  = np.arange(0, 60 + 3, 3)                          
strike_centers = (strike_edges[:-1] + strike_edges[1:]) / 2     
tenor_centers  = (tenor_edges_m[:-1] + tenor_edges_m[1:]) // 2     

n_strike, n_tenor = len(strike_centers), len(tenor_centers)
vega_matrix = np.zeros((n_strike, n_tenor))

# ---------------- baseline PV (一次) ----------------
req_base = build_pricer_request_no_bump(ts, [STOCK_ID], MAX_PATHS)
pv0 = float(fpf(req_base)["M2M Value"])
print(f"Baseline PV ({STOCK_ID}) = {pv0:.4f}")

# ---------------- 计算单元格 vega ----------------
def compute_vega_cell(i: int, j: int) -> tuple[int, int, float]:
    k_low, k_high = strike_edges[i], strike_edges[i + 1]
    t_low, t_high = tenor_edges_m[j], tenor_edges_m[j + 1]

    req = build_pricer_request(
        term_sheet      = ts,
        rel_low_strk    = [k_low],
        rel_high_strk   = [k_high],
        short_term      = [f"{t_low}m"],
        long_term       = [f"{t_high}m"],
        tenor_bump_sizes= [BUMP_SIZE],
        stock_ids       = [STOCK_ID],
        max_paths       = MAX_PATHS,
    )
    pv_bump = float(fpf(req)["M2M Value"])
    vega = (pv_bump - pv0) / BUMP_SIZE
    return i, j, vega

# ---------------- 并⾏填充矩阵 ----------------
start = time.time()
with ThreadPoolExecutor(max_workers=THREADS) as exe:
    futures = {
        exe.submit(compute_vega_cell, i, j): (i, j)
        for i in range(n_strike)
        for j in range(n_tenor)
    }
    for fut in as_completed(futures):
        i, j, vega = fut.result()
        vega_matrix[i, j] = vega
print(f"Vega grid done in {time.time() - start:.1f}s")

# ---------------- 画热图 ----------------
cmap = LinearSegmentedColormap.from_list(
    "red_white_green",
    [(0.80, 0.00, 0.00),
     (1.00, 1.00, 1.00),
     (0.00, 0.50, 0.00)],
    N=256,
)
abs_max = np.abs(vega_matrix).max()
norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0.0, vmax=abs_max)

fig, ax = plt.subplots(figsize=(10, 6))
mesh = ax.pcolormesh(
    tenor_centers / 12,                
    strike_centers,                     
    vega_matrix,
    cmap=cmap,
    norm=norm,
    shading="auto",
)
fig.colorbar(mesh, ax=ax, label="Vega")
ax.set_xlabel("Tenor (years)")
ax.set_ylabel("Strike / Spot")
ax.set_title(f"Autocallable Note – {STOCK_ID} Vega Map")
plt.tight_layout()
plt.show()

# ---------------- 保存 PNG & CSV ----------------
out_dir = Path("Temp"); out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "vega_map.png", dpi=300, bbox_inches="tight"); plt.close(fig)

pd.DataFrame(
    vega_matrix,
    index=strike_centers,
    columns=[f"{t}m" for t in tenor_centers],
).to_csv(out_dir / "vega_map.csv")

print(f"PNG & CSV saved to → {out_dir.resolve()}")


def build_pricer_request(
    term_sheet: TermSheet,
    strikes: float,
    tenors: List[str],
    tenor_bump_sizes: List[float],
    bump_size_abs: float = 0.0025,
    stock_ids: List[str] = None,
    max_paths: int = 100000
) -> Dict[str, Any]:
    if stock_ids is None:
        stock_ids = term_sheet.Stock_IDs

    request: Dict[str, Any] = {
        "action": "price",
        "pricer": "Autocallable Note",
        "greeks": {
            "M2M Value": True,
            "Vega": True,
            "Gamma": True,
            "Average Lifetime": True
        },
        "numeric_parameters": {
            "Calibrate Dupire on Full Strike Range": True,
            "Computation Type": "Monte Carlo",
            "Implied Volatility Average Fitting Error Tolerance": [1e-7, 2e-5],
            "Implied Volatility Fitting Error Tenor": [1, 2],
            "Implied Volatility Surface Fitter": "TD Fitter",
            "Maximum Euler Timestep": 1,
            "Maximum Euler Timestep Tenors": [0, 0.5, 1, 2],
            "Maximum Euler Timestep Values": [1, 5, 10, 10],
            "Number of Paths": max_paths,
            "Random Sampler Type": "NormalCNDInvSampler",
            "Random Uniform Generator": "RandomSobol",
            "Use Unadjusted Barrier For Memory Event": True
        },
        "assumptions": {
            "Dividend Model": "Discrete Proportional",
            "Volatility Model": "Local Volatility Surface",
            "Volatility Sub Type": "Effective Strike"
        },
        "termsheet": term_sheet.to_dict(),
        "bumps": [
            {
                "Type": "Volatility Bump",
                "Bump Method": "Absolute",
                "Stock IDs": stock_ids,
                "Strike": strikes,
                "Tenor Bump Sizes": tenor_bump_sizes,
                "Tenors": tenors
            }
        ],
        "curve_mapping": {
            "Mongo Curve Mapping": {
                "ID": "cof_discounting_USA"
            }
        },
        "split_mc": False,
        "with_slave": True,
        "priority": -5,
        "storing_pricing_data": False
    }

    return request
