from __future__ import annotations
import json
from typing import Dict, List
from datetime import datetime, timedelta
from pathlib import Path

from FPFServer import sync 

def _shift(date_str: str, days: int) -> str:
    return (
        datetime.fromisoformat(date_str) + timedelta(days=days)
    ).strftime("%Y-%m-%d")

def build_termsheet(
    underlying_id: str,
    obs_dates: List[str],
    initial_level: float,
    coupon_barrier: float = 0.7,
    maturity_barrier: float = 0.7,
) -> Dict:

    return {
        "Accrues When": "Inside Range",

        "Autocall Barrier": [1.0] * len(obs_dates),
        "Autocall Dates": obs_dates,
        "Autocall Ex Dates": [_shift(d, 3) for d in obs_dates],
        "Autocall Pay Dates": [_shift(d, 5) for d in obs_dates],

        "Basket Level Type": "Weighted Sum of Asset Returns",
        "Basket Weights": [1],

        "Coupon Determination Dates": obs_dates,
        "Coupon Determination Ex Dates": [_shift(d, 3) for d in obs_dates],
        "Coupon Low Barrier": [coupon_barrier] * len(obs_dates),
        "Coupon Memory Cutoff Dates": [obs_dates[-1]] * len(obs_dates),
        "Coupon Memory Multiplier": [1] * len(obs_dates),
        "Coupon Multiple Observation Barrier Type": "Knock-Out",
        "Coupon Pay Dates": [_shift(d, 5) for d in obs_dates],

        "Daycount Basis": "ACT/365",
        "Downside Participation": 1,
        "Fixed Return": [0] * len(obs_dates),
        "Floating Payment Multiplier": -1,
        "Guaranteed Minimum Maturity Return": 0,
        "Initial Levels": [initial_level],
        "Is Note?": True,

        "Maturity Barrier": maturity_barrier,
        "Maturity Date": obs_dates[-1],
        "Maturity Option Barrier Type": "Knock-In",
        "Maturity Settlement Date": _shift(obs_dates[-1], 5),

        "Participation": [0] * len(obs_dates),
        "Participation With Memory Coupons": [0] * len(obs_dates),

        "Pay ID": "USD",
        "Premium Settlement Date": _shift(datetime.now().strftime("%Y-%m-%d"), 2),
        "Return Notional At Recall": True,
        "Stock IDs": [underlying_id],
        "Strike Setting Date": [datetime.now().strftime("%Y-%m-%d")],

        "Variable Coupon Strike": [1] * len(obs_dates),
        "Variable Coupon Strike With Memory Coupons": [0] * len(obs_dates),

        "Barrier Shift Parameters": {
            "Autocall Absolute Shift": [-0.0087] * len(obs_dates),
            "Autocall Shift Dates": obs_dates,
            "Coupon Absolute Shift": [-0.0087] * len(obs_dates),
            "Coupon Absolute Spread": [0.0174] * len(obs_dates),
            "Coupon Shift Dates": obs_dates,
            "Maturity Barrier Absolute Shift": -0.0087,
            "Maturity Barrier Absolute Spread": 0.0174,
            "Maturity Barrier Knock-Out Levels Absolute Shift": [-0.0087],
        },

        "Initial Fixing Date": datetime.now().strftime("%Y-%m-%d"),
    }


def price_autocall(
    host: str,
    port: int,
    env: Dict[str, str],
    underlying_id: str,
    autocall_dates: List[str],
    initial_level: float,
    *,
    strike_idx: int = 10,
    bump_tenor: str = "3m",
    bump_size: float = 0.0025,
    paths: int = 100_000,
) -> Dict:

    fpf = sync(host, port, env)

    vol_handle = fpf({"get": {"what": "volatility index", "id": underlying_id}})["top"][0]
    surface = fpf({"get": vol_handle})
    strike_val = surface["strikes"][strike_idx]

    termsheet = build_termsheet(underlying_id, autocall_dates, initial_level)

    request = {
        "action": "price",
        "pricer": "Autocallable Note",
        "greeks": {
            "M2M Value": True,
            "Vega": True,
            "Gamma": True,
            "Average Lifetime": True,
        },
        "numeric_parameters": {
            "Calibrate Dupire on Full Strike Range": True,
            "Computation Type": "Monte Carlo",
            "Implied Volatility Average Fitting Error Tolerance": [1e-7, 0.00002],
            "Implied Volatility Fitting Error Tenor": [1, 2],
            "Implied Volatility Surface Fitter": "TD Fitter",
            "Maximum Euler Timestep": 1,
            "Maximum Euler Timestep Tenors": [0, 0.5, 1, 2],
            "Maximum Euler Timestep Values": [1, 5, 10, 10],
            "Number of Paths": paths,
            "Random Sampler Type": "NormalCNDFInvSampler",
            "Random Uniform Generator": "RandomSobol",
            "Use Unadjusted Barrier For Memory Event": True,
        },
        "assumptions": {
            "Dividend Model": "Discrete Proportional",
            "Volatility Model": "Local Volatility Surface",
            "Volatility Sub Type": "Effective Strike",
        },
        "termsheet": termsheet,
        "bumps": [
            {
                "Type": "Volatility Bump",
                "Bump Method": "Absolute",
                "Stock IDs": [underlying_id],
                "Strike": strike_val,
                "Tenor Bump Sizes": [[bump_size]],
                "Tenors": [bump_tenor],
            }
        ],
        "curve_mapping": {
            "Mongo Curve Mapping": {"ID": "cof_discounting_USA"}
        },
        "max_paths": 5000,
        "with_slave": True,
        "priority": -5,
        "storing_pricing_data": False,
        "rid": "single-run",
    }

    return fpf(request)
