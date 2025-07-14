
tenor_months = list(range(0, 61, 6))         
tenor_grid   = [f"{m}m" for m in tenor_months]

n_strike, n_tenor = len(strikes_abs), len(tenor_grid)
vega_matrix = np.zeros((n_strike, n_tenor))

for i, strike_abs in enumerate(strikes_abs):

    for j, tenor in enumerate(tenor_grid):
        bump_list = [0.0025 if k == j else 0.0 for k in range(n_tenor)]

        req = build_pricer_request(
            term_sheet       = ts,
            strikes          = strike_abs,  
            tenors           = tenor_grid,   
            tenor_bump_sizes = bump_list, 
            max_paths        = 100000,
        )

        resp = fpf(req)
        vega_matrix[i, j] = resp["Vega"]    

x = np.array(tenor_months) / 12           
y = np.array(strikes_pct)

fig, ax = plt.subplots(figsize=(10, 6))
c = ax.pcolormesh(x, y, vega_matrix, shading="auto")
fig.colorbar(c, ax=ax, label="Vega")

ax.set_xlabel("Tenor (years)")
ax.set_ylabel("Strike / Spot")
ax.set_title("Autocallable Note Vega Map")
plt.tight_layout()

out_dir = Path("Temp")
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "vega_map.png", dpi=300, bbox_inches="tight")
plt.close(fig)

pd.DataFrame(vega_matrix, index=strikes_pct, columns=tenor_grid)\
  .to_csv(out_dir / "vega_map.csv")
