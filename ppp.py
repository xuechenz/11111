BUMP_SIZE      = 0.0025
zero_bump_list = [0.0] * len(tenor_grid)

req_base  = build_pricer_request(
    term_sheet       = ts,
    strikes          = strikes_abs[0],  
    tenors           = tenor_grid,
    tenor_bump_sizes = zero_bump_list,
    max_paths        = 100_000,
)
pv_before = float(fpf(req_base)["Premium Price"])
print(f"Baseline Premium = {pv_before:.6f}")


for i, strike_abs in enumerate(strikes_abs):
    for j, tenor in enumerate(tenor_grid):

        bump_list = [BUMP_SIZE if k == j else 0.0 for k in range(len(tenor_grid))]

        req = build_pricer_request(
            term_sheet       = ts,
            strikes          = strike_abs,
            tenors           = tenor_grid,
            tenor_bump_sizes = bump_list,
            max_paths        = 100_000,
        )
        resp = fpf(req)
        pv_after = float(resp["Premium Price"]) 
        vega_matrix[i, j] = (pv_after - pv_before) / BUMP_SIZE
        print(f"Strike {strike_abs}, Tenor {tenor_grid}: Vega = {vega_matrix[i, j]:.6f}")

from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

cmap = LinearSegmentedColormap.from_list(
    "red_white_green",
    [(0.80, 0.00, 0.00), 
     (1.00, 1.00, 1.00),  
     (0.00, 0.50, 0.00)], 
    N=256,
)
abs_max = np.abs(vega_matrix).max()
norm    = TwoSlopeNorm(vmin=-abs_max, vcenter=0.0, vmax=abs_max)

fig, ax = plt.subplots(figsize=(10, 6))
mesh = ax.pcolormesh(
    np.array(tenor_months) / 12,
    np.array([k / spot for k in strikes_abs]),
    vega_matrix,
    cmap=cmap,
    norm=norm,
    shading="auto",
)
fig.colorbar(mesh, ax=ax, label="Vega")
ax.set_xlabel("Tenor (years)")
ax.set_ylabel("Strike / Spot")
ax.set_title("Autocallable Note — Vega Map")
plt.tight_layout()
plt.show()

out_dir = Path("Temp")
out_dir.mkdir(parents=True, exist_ok=True)

fig.savefig(out_dir / "vega_map.png", dpi=300, bbox_inches="tight")
plt.close(fig)                    

pd.DataFrame(
    vega_matrix,
    index=strikes_pct, 
    columns=tenor_grid
).to_csv(out_dir / "vega_map.csv")

print(f"PNG and CSV saved to -> {out_dir.resolve()}")
