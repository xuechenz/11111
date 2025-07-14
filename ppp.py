from FPFServer import sync                     
from term_sheet_classes import (             
    BarrierShiftParameters,
    TermSheet,
    build_pricer_request,
)

env = {
    "name":     "1",
    "password": "1",
}
fpf = sync("1", 1, env)            

vol_handle = {
    "get": {
        "what": "volatility index",
        "id":   "NDX.IDX"
    }
}
strike_meta = fpf(vol_handle)                  
strikes_list = strike_meta["top"][0]["strikes"]
strike_for_bump = [strikes_list[10]]         


bsp = BarrierShiftParameters(
    Autocall_Absolute_Shift=[-0.0087, -0.0087, -0.0087, -0.0087],
    Autocall_Shift_Dates=["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
    Coupon_Absolute_Shift=[-0.0087, -0.0087, -0.0087, -0.0087],
    Coupon_Absolute_Spread=[0.0174, 0.0174, 0.0174, 0.0174],
    Coupon_Shift_Dates=["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
    Maturity_Barrier_Absolute_Shift=-0.0087,
    Maturity_Barrier_Absolute_Spread=0.0174,
    Maturity_Barrier_Knock_Out_Levels_Absolute_Shift=[-0.0087],
)

ts = TermSheet(
    Accrues_When="Inside Range",
    Autocall_Barrier=[1, 1, 1, 1],
    Autocall_Dates=["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
    Autocall_Ex_Dates=["2025-11-10","2026-02-10","2026-05-08","2026-08-10"],
    Autocall_Pay_Dates=["2025-11-12","2026-02-12","2026-05-12","2026-08-12"],
    Basket_Level_Type="Weighted Sum of Asset Returns",
    Basket_Weights=[1],
    Coupon_Determination_Dates=["2025-11-10","2026-02-09","2026-05-07","2026-08-07"],
    Coupon_Determination_Ex_Dates=["2025-11-10","2026-02-10","2026-05-08","2026-08-10"],
    Coupon_Low_Barrier=[0.7, 0.7, 0.7, 0.7],
    Coupon_Memory_Cutoff_Dates=["2026-08-07"]*4,
    Coupon_Memory_Multiplier=[1, 1, 1, 1],
    Coupon_Multiple_Observation_Barrier_Type="Knock-Out",
    Coupon_Pay_Dates=["2025-11-12","2026-02-12","2026-05-12","2026-08-12"],
    Daycount_Basis="ACT/365",
    Downside_Participation=1,
    Fixed_Return=[0, 0, 0, 0],
    Floating_Payment_Multiplier=-1,
    Guaranteed_Minimum_Maturity_Return=0,
    Initial_Levels=[22726.012561111645],
    Is_Note=True,
    Maturity_Barrier=0.7,
    Maturity_Date="2026-08-07",
    Maturity_Option_Barrier_Type="Knock-In",
    Maturity_Settlement_Date="2026-08-12",
    Participation=[0, 0, 0, 0],
    Participation_With_Memory_Coupons=[0, 0, 0, 0],
    Pay_ID="USD",
    Premium_Settlement_Date="2025-07-10",
    Return_Notional_At_Recall=True,
    Stock_IDs=["NDX.IDX"],
    Strike_Setting_Date=["2025-07-07"],
    Variable_Coupon_Strike=[1, 1, 1, 1],
    Variable_Coupon_Strike_With_Memory_Coupons=[0, 0, 0, 0, 0],
    Barrier_Shift_Parameters=bsp,
)


tenor_grid        = ["3m", "6m", "9m", "12m"]
tenor_bump_sizes  = [0, 0.0025, 0, 0]

request_dict = build_pricer_request(
    term_sheet        = ts,
    strikes           = strike_for_bump,  
    tenors            = tenor_grid,
    tenor_bump_sizes  = tenor_bump_sizes,
    bump_size_abs     = 0.0025,
    stock_ids         = ["NDX.IDX"],
    max_paths         = 5000             
)


response = fpf(request_dict)

print("Vega  (abs bump 25bp, strike idx=10, tenor 6m):",
      response["greeks"]["Vega"])
