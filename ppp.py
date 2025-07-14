########################################
# 1. Imports and connect to pricing engine
########################################
import json                # used for printing request/response payloads during debugging
import time                # used to measure end‐to‐end script runtime
import numpy as np         # numerical arrays and matrix operations
import pandas as pd        # constructing DataFrame for CSV export
import matplotlib.pyplot as plt                    # plotting the heatmap
from pathlib import Path                           # cross‐platform directory and file handling
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
                                                   # custom colormap and zero‐center normalization

# sync establishes a TCP connection to the FPF pricing server
from FPFServer import sync
# TermSheet and build_pricer_request encapsulate the JSON schema for a structured note pricer
from autocall_pricer import BarrierShiftParameters, TermSheet, build_pricer_request

# connect to the FPFServer on host "mkcoe04" port 3456, using simple credentials
env        = {"name": "22", "password": "22"}
fpf        = sync("2", 2, env)
start_time = time.time()  # record script start time



########################################
# 2. Build the TermSheet object
########################################

# 2.1 Query volatility index metadata to obtain current spot and available strikes
# first build the “get” request for volatility index data
vol_request = {"get": {"what": "volatility index", "id": "NDX.IDX"}}
# send to server and extract the first element from the "top" list
vol_handle  = fpf(vol_request)["top"][0]
# fetch details for that handle: this response contains "spot" price and a list of strikes
strike_meta = fpf({"get": vol_handle})
spot         = strike_meta["spot"]    # current index level
strikes_abs  = strike_meta["strikes"] # available absolute exercise prices

# 2.2 Create shift‐parameter object specifying how barriers and coupons adjust on key dates
bsp = BarrierShiftParameters(
    # shifts to the autocall barrier at each observation date (in absolute terms)
    Autocall_Absolute_Shift                  = [-0.0087, -0.0087, -0.0087, -0.0087],
    # the dates on which those autocall barrier shifts take effect
    Autocall_Shift_Dates                     = ["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
    # same pattern for coupon barrier shifts and spreads
    Coupon_Absolute_Shift                    = [-0.0087, -0.0087, -0.0087, -0.0087],
    Coupon_Absolute_Spread                   = [0.0174,  0.0174,  0.0174,  0.0174],
    Coupon_Shift_Dates                       = ["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
    # maturity barrier adjustments at final date
    Maturity_Barrier_Absolute_Shift          = -0.0087,
    Maturity_Barrier_Absolute_Spread         = 0.0174,
    Maturity_Barrier_Knock_Out_Levels_Absolute_Shift = [-0.0087],
)

# 2.3 Construct the TermSheet instance with all product features
ts = TermSheet(
    # accrual rule: coupon accrues only when index stays inside the barrier
    Accrues_When                            = "Inside Range",
    # barrier levels for autocall observation (as fraction of initial level, here 100%)
    Autocall_Barrier                        = [1, 1, 1, 1],
    # list of observation dates on which early redemption may occur
    Autocall_Dates                          = ["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
    # ex‐dividend dates corresponding to autocall dates
    Autocall_Ex_Dates                       = ["2025-11-10","2026-02-10","2026-05-08","2026-08-10"],
    # payment dates if autocall is triggered
    Autocall_Pay_Dates                      = ["2025-11-12","2026-02-12","2026-05-12","2026-08-12"],
    # weighting and type of underlying basket (here single‐asset return sum)
    Basket_Level_Type                       = "Weighted Sum of Asset Returns",
    Basket_Weights                          = [1],
    # coupon observation and payment schedule, with knockout style barrier
    Coupon_Determination_Dates              = ["2025-11-10","2026-02-09","2026-05-07","2026-08-07"],
    Coupon_Determination_Ex_Dates           = ["2025-11-10","2026-02-10","2026-05-08","2026-08-10"],
    Coupon_Pay_Dates                        = ["2025-11-12","2026-02-12","2026-05-12","2026-08-12"],
    Coupon_Low_Barrier                      = [0.7,0.7,0.7,0.7],  # 70% barrier
    Coupon_Memory_Cutoff_Dates              = ["2026-08-07"]*4,
    Coupon_Memory_Multiplier                = [1,1,1,1],
    Coupon_Multiple_Observation_Barrier_Type= "Knock-Out",
    # day count convention for discounting cash flows
    Daycount_Basis                          = "ACT/365",
    # full participation in any upside, negative multiplier for floating leg
    Downside_Participation                  = 1,
    Floating_Payment_Multiplier             = -1,
    # minimum guaranteed return at maturity
    Guaranteed_Minimum_Maturity_Return      = 0,
    # initial index level used for barrier and strike calculations
    Initial_Levels                          = [spot],
    Is_Note                                 = True,
    # barrier level at maturity for knock‐in/down feature
    Maturity_Barrier                        = 0.7,
    Maturity_Date                           = "2026-08-07",
    Maturity_Option_Barrier_Type            = "Knock-In",
    Maturity_Settlement_Date                = "2026-08-12",
    # participation settings after recall or maturity
    Participation                           = [0,0,0,0],
    Participation_With_Memory_Coupons       = [0,0,0,0],
    # market conventions
    Pay_ID                                  = "USD",
    Premium_Settlement_Date                 = "2025-07-10",
    Return_Notional_At_Recall               = True,
    # underlying asset identifiers
    Stock_IDs                               = ["NDX.IDX"],
    Strike_Setting_Date                     = ["2025-07-07"],
    Variable_Coupon_Strike                  = [1,1,1,1],
    Variable_Coupon_Strike_With_Memory_Coupons = [0,0,0,0],
    # attach barrier shift parameters object from above
    Barrier_Shift_Parameters                = bsp,
)



########################################
# 3. Prepare strike-tenor grid and initialize Vega matrix
########################################

# normalize absolute strikes by spot so vertical axis is strike/spot
strikes_pct  = [k/spot for k in strikes_abs]

# define tenor grid in months and convert to strings like "0m","6m",..., "60m"
tenor_months = list(range(0, 61, 6))
tenor_grid   = [f"{m}m" for m in tenor_months]

# dimensions of the Vega matrix: rows = number of strikes, columns = number of tenors
n_strike, n_tenor = len(strikes_abs), len(tenor_grid)
vega_matrix      = np.zeros((n_strike, n_tenor))  # will hold computed Vega values



########################################
# 4. Compute baseline PV with zero volatility bump
########################################

BUMP_SIZE      = 0.0025                     # bump size = 0.25% vol
zero_bump_list = [0.0] * n_tenor            # no bump on any tenor

# build a request that sends the term sheet, one strike, 
# full tenor grid, and zero bump sizes
req_base = build_pricer_request(
    term_sheet       = ts,
    strikes          = strikes_abs[0],    # use first strike; baseline is identical for all
    tenors           = tenor_grid,
    tenor_bump_sizes = zero_bump_list,
    max_paths        = 100_000,           # number of Monte Carlo paths or simulation granularity
)
resp_base = fpf(req_base)                 # send to pricing engine and receive response
# extract Premium Price if present; fallback to Mark-to-Market Value otherwise
pv_before = float(resp_base.get("Premium Price", resp_base.get("M2M Value")))
print(f"Baseline PV without volatility bump = {pv_before:.6f}")



########################################
# 5. Loop over strikes and tenors to compute finite-difference Vega
########################################

for i, strike_abs in enumerate(strikes_abs):
    for j, tenor in enumerate(tenor_grid):
        # create bump_list where only the j-th tenor is bumped by BUMP_SIZE
        bump_list = [BUMP_SIZE if k == j else 0.0 for k in range(n_tenor)]

        # build request for this specific bump scenario
        req = build_pricer_request(
            term_sheet       = ts,
            strikes          = strike_abs,
            tenors           = tenor_grid,
            tenor_bump_sizes = bump_list,
            max_paths        = 100_000,
        )
        resp     = fpf(req)
        # read back bumped PV; use fallback if Premium Price not returned
        pv_after = float(resp.get("Premium Price", resp.get("M2M Value")))

        # compute Vega as change in PV divided by change in vol (finite difference)
        vega_matrix[i, j] = (pv_after - pv_before) / BUMP_SIZE

        # optional: print each computed Vega for monitoring
        print(f"Computed Vega for strike {strike_abs:.0f}, tenor {tenor} = {vega_matrix[i,j]:.4f}")



########################################
# 6. Define a custom red-white-green colormap centered at zero and plot heatmap
########################################

# create a colormap that transitions from red (negative) through white (zero) to green (positive)
cmap = LinearSegmentedColormap.from_list(
    "red_white_green",
    [
        (0.80, 0.00, 0.00),  # dark red for strong negative Vega
        (1.00, 1.00, 1.00),  # white for zero Vega
        (0.00, 0.50, 0.00)   # dark green for strong positive Vega
    ],
    N=256
)
# compute the maximum absolute Vega value for symmetric normalization
abs_max = np.abs(vega_matrix).max()
norm    = TwoSlopeNorm(vmin=-abs_max, vcenter=0.0, vmax=abs_max)

# plot the heatmap: X axis = tenor in years (tenor_months/12), Y axis = strike_pct
fig, ax = plt.subplots(figsize=(10, 6))
mesh = ax.pcolormesh(
    np.array(tenor_months) / 12,
    np.array(strikes_pct),
    vega_matrix,
    cmap=cmap,
    norm=norm,
    shading="auto"
)
fig.colorbar(mesh, ax=ax, label="Vega")  # add colorbar legend
ax.set_xlabel("Tenor (years)")
ax.set_ylabel("Strike / Spot")
ax.set_title("Vega Map for Autocallable Note")
plt.tight_layout()



########################################
# 7. Save the heatmap image and Vega matrix to files
########################################

out_dir = Path("Temp")             # target directory for outputs
out_dir.mkdir(parents=True, exist_ok=True)

# save figure as high-resolution PNG for presentation
fig.savefig(out_dir / "vega_map.png", dpi=300, bbox_inches="tight")
plt.close(fig)                     # close the figure to free memory

# save the raw Vega matrix to CSV with strikes_pct as rows and tenor_grid as columns
pd.DataFrame(
    vega_matrix,
    index=strikes_pct,
    columns=tenor_grid
).to_csv(out_dir / "vega_map.csv")

print(f"Script completed in {time.time() - start_time:.2f} seconds")
