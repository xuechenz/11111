# 2. Build the TermSheet object

# 2.1 Query volatility index metadata to obtain current spot and available strikes
spot_handle = fpf({
    "get": {
        "what": "spot index",
        "id": "NDX.IDX"
    }
})["top"][0]

strike_meta = fpf({ "get": spot_handle })
spot        = strike_meta["last"]
strike_abs = (
    [spot * pct for pct in [0.5, 0.6, 0.7, 0.8, 0.9]] +
    [spot * pct for pct in [x / 100 for x in range(92, 110, 2)]] +
    [spot * pct for pct in [1.1, 1.2, 1.3, 1.4, 1.5]]
)




# 2.2 Create shift-parameter object specifying how barriers and coupons adjust on key dates
bsp = BarrierShiftParameters(
    Autocall_Absolute_Shift         = [-0.0087, -0.0087, -0.0087, -0.0087],
    Autocall_Shift_Dates            = ["2025-11-07", "2026-02-09", "2026-05-07", "2026-08-07"],
    Coupon_Absolute_Shift           = [-0.0087, -0.0087, -0.0087, -0.0087],
    Coupon_Absolute_Spread          = [0.0174, 0.0174, 0.0174, 0.0174],
    Coupon_Shift_Dates              = ["2025-11-07", "2026-02-09", "2026-05-07", "2026-08-07"],
    Maturity_Barrier_Absolute_Shift = -0.0087,
    Maturity_Barrier_Absolute_Spread=  0.0174,
    Maturity_Barrier_Knock_Out_Levels_Absolute_Shift = [-0.0087],
)


# 2.3 Construct the TermSheet instance with all product features
ts = TermSheet(
    Accrues_When                           = "Inside Range",
    Autocall_Barrier                       = [1, 1, 1, 1],
    Autocall_Dates                         = ["2025-11-07", "2026-02-09", "2026-05-07", "2026-08-07"],
    Autocall_Ex_Dates                      = ["2025-11-10", "2026-02-10", "2026-05-08", "2026-08-10"],
    Autocall_Pay_Dates                     = ["2025-11-12", "2026-02-12", "2026-05-12", "2026-08-12"],
    Basket_Level_Type                      = "Weighted Sum of Asset Returns",
    Basket_Weights                         = [1],
    Coupon_Determination_Dates             = ["2025-11-10", "2026-02-09", "2026-05-07", "2026-08-07"],
    Coupon_Determination_Ex_Dates          = ["2025-11-10", "2026-02-10", "2026-05-08", "2026-08-10"],
    Coupon_Low_Barrier                     = [0.7, 0.7, 0.7, 0.7],
    Coupon_Memory_Cutoff_Dates             = ["2026-08-07"] * 4,
    Coupon_Memory_Multiplier               = [1, 1, 1, 1],
    Coupon_Multiple_Observation_Barrier_Type = "Knock-Out",
    Coupon_Pay_Dates                       = ["2025-11-12", "2026-02-12", "2026-05-12", "2026-08-12"],
    Daycount_Basis                         = "ACT/365",
    Downside_Participation                 = 1,
    Fixed_Return                           = [0, 0, 0, 0],
    Floating_Payment_Multiplier            = -1,
    Guaranteed_Minimum_Maturity_Return     = 0,
    Initial_Levels                         = [spot],
    Is_Note                                = True,
    Maturity_Barrier                       = 0.7,
    Maturity_Date                          = "2026-08-07",
    Maturity_Option_Barrier_Type           = "Knock-In",
    Maturity_Settlement_Date               = "2026-08-12",
    Participation                          = [0, 0, 0, 0],
    Participation_With_Memory_Coupons      = [0, 0, 0, 0],
    Pay_ID                                 = "USD",
    Premium_Settlement_Date                = "2025-07-10",
    Return_Notional_At_Recall              = True,
    Stock_IDs                              = ["NDX.IDX"],
    Strike_Setting_Date                    = ["2025-07-07"],
    Variable_Coupon_Strike                 = [1, 1, 1, 1],
    Variable_Coupon_Strike_With_Memory_Coupons = [0, 0, 0, 0],
    Barrier_Shift_Parameters               = bsp,
)


# 3. Prepare strike-tenor grid and initialize Vega matrix

strikes_pct = [k / spot for k in strikes_abs]
tenor_months = list(range(0, 61, 3))             
tenor_grid   = [f"{m}m" for m in tenor_months]  
n_strike, n_tenor = len(strikes_abs), len(tenor_grid)
vega_matrix = np.zeros((n_strike, n_tenor))


# 4. Compute baseline PV with zero volatility bump
BUMP_SIZE     = 0.0025
zero_bump_list = [0.0] * n_tenor

for i, strike_abs in enumerate(strikes_abs):
    req_base = build_pricer_request(
        term_sheet      = ts,
        strikes         = strike_abs,
        tenors          = tenor_grid,
        tenor_bump_sizes= zero_bump_list,
        max_paths       = 100_000,
    )
    resp_base = fpf(req_base)
    pv_before = float(resp_base["M2M Value"])
    print(f"Strike {strike_abs:.2f} baseline M2M = {pv_before:.6f}")

    # 5. For each tenor, apply a small vol bump and compute finite-difference Vega
    for j, tenor in enumerate(tenor_grid):
        bump_list = [BUMP_SIZE if k == j else 0.0 for k in range(n_tenor)]
        req       = build_pricer_request(
            term_sheet       = ts,
            strikes          = strike_abs,
            tenors           = tenor_grid,
            tenor_bump_sizes = bump_list,
            max_paths        = 100_000,
        )
        resp      = fpf(req)
        pv_after  = float(resp["M2M Value"])
        vega_matrix[i, j] = (pv_after - pv_before) / BUMP_SIZE
        print(f" Tenor {tenor}: Vega = {vega_matrix[i, j]:.4f}")


# 6. Plot heatmap
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
ax.set_title("Autocallable Note – Vega Map")
plt.tight_layout()
plt.show()


# 7. Save the heatmap image and Vega matrix to files
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
