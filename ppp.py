from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class BarrierShiftParameters:
    Autocall_Absolute_Shift:        List[float]
    Autocall_Shift_Dates:           List[str]
    Coupon_Absolute_Shift:          List[float]
    Coupon_Absolute_Spread:         List[float]
    Coupon_Shift_Dates:             List[str]
    Maturity_Barrier_Absolute_Shift:         float
    Maturity_Barrier_Absolute_Spread:        float
    Maturity_Barrier_Knock_Out_Levels_Absolute_Shift: List[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Autocall Absolute Shift":                self.Autocall_Absolute_Shift,
            "Autocall Shift Dates":                   self.Autocall_Shift_Dates,
            "Coupon Absolute Shift":                  self.Coupon_Absolute_Shift,
            "Coupon Absolute Spread":                 self.Coupon_Absolute_Spread,
            "Coupon Shift Dates":                     self.Coupon_Shift_Dates,
            "Maturity Barrier Absolute Shift":        self.Maturity_Barrier_Absolute_Shift,
            "Maturity Barrier Absolute Spread":       self.Maturity_Barrier_Absolute_Spread,
            "Maturity Barrier Knock-Out Levels Absolute Shift":
                self.Maturity_Barrier_Knock_Out_Levels_Absolute_Shift,
        }


@dataclass
class TermSheet:
    Accrues_When:                        str
    Autocall_Barrier:                    List[float]
    Autocall_Dates:                      List[str]
    Autocall_Ex_Dates:                   List[str]
    Autocall_Pay_Dates:                  List[str]
    Basket_Level_Type:                   str
    Basket_Weights:                      List[float]
    Coupon_Determination_Dates:          List[str]
    Coupon_Determination_Ex_Dates:       List[str]
    Coupon_Low_Barrier:                  List[float]
    Coupon_Memory_Cutoff_Dates:          List[str]
    Coupon_Memory_Multiplier:            List[float]
    Coupon_Multiple_Observation_Barrier_Type: str
    Coupon_Pay_Dates:                    List[str]
    Daycount_Basis:                      str
    Downside_Participation:              float
    Fixed_Return:                        List[float]
    Floating_Payment_Multiplier:         float
    Guaranteed_Minimum_Maturity_Return:  float
    Initial_Levels:                      List[float]
    Is_Note:                             bool
    Maturity_Barrier:                    float
    Maturity_Date:                       str
    Maturity_Option_Barrier_Type:        str
    Maturity_Settlement_Date:            str
    Participation:                       List[float]
    Participation_With_Memory_Coupons:   List[float]
    Pay_ID:                              str
    Premium_Settlement_Date:             str
    Return_Notional_At_Recall:           bool
    Stock_IDs:                           List[str]
    Strike_Setting_Date:                 List[str]
    Variable_Coupon_Strike:              List[float]
    Variable_Coupon_Strike_With_Memory_Coupons: List[float]
    Barrier_Shift_Parameters:            BarrierShiftParameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Accrues When":                         self.Accrues_When,
            "Autocall Barrier":                     self.Autocall_Barrier,
            "Autocall Dates":                       self.Autocall_Dates,
            "Autocall Ex Dates":                    self.Autocall_Ex_Dates,
            "Autocall Pay Dates":                   self.Autocall_Pay_Dates,
            "Basket Level Type":                    self.Basket_Level_Type,
            "Basket Weights":                       self.Basket_Weights,
            "Coupon Determination Dates":           self.Coupon_Determination_Dates,
            "Coupon Determination Ex Dates":        self.Coupon_Determination_Ex_Dates,
            "Coupon Low Barrier":                   self.Coupon_Low_Barrier,
            "Coupon Memory Cutoff Dates":           self.Coupon_Memory_Cutoff_Dates,
            "Coupon Memory Multiplier":             self.Coupon_Memory_Multiplier,
            "Coupon Multiple Observation Barrier Type":
                                                    self.Coupon_Multiple_Observation_Barrier_Type,
            "Coupon Pay Dates":                     self.Coupon_Pay_Dates,
            "Daycount Basis":                       self.Daycount_Basis,
            "Downside Participation":               self.Downside_Participation,
            "Fixed Return":                         self.Fixed_Return,
            "Floating Payment Multiplier":          self.Floating_Payment_Multiplier,
            "Guaranteed Minimum Maturity Return":   self.Guaranteed_Minimum_Maturity_Return,
            "Initial Levels":                       self.Initial_Levels,
            "Is Note?":                             self.Is_Note,
            "Maturity Barrier":                     self.Maturity_Barrier,
            "Maturity Date":                        self.Maturity_Date,
            "Maturity Option Barrier Type":         self.Maturity_Option_Barrier_Type,
            "Maturity Settlement Date":             self.Maturity_Settlement_Date,
            "Participation":                        self.Participation,
            "Participation With Memory Coupons":    self.Participation_With_Memory_Coupons,
            "Pay ID":                               self.Pay_ID,
            "Premium Settlement Date":              self.Premium_Settlement_Date,
            "Return Notional At Recall":            self.Return_Notional_At_Recall,
            "Stock IDs":                            self.Stock_IDs,
            "Strike Setting Date":                  self.Strike_Setting_Date,
            "Variable Coupon Strike":               self.Variable_Coupon_Strike,
            "Variable Coupon Strike With Memory Coupons":
                                                    self.Variable_Coupon_Strike_With_Memory_Coupons,
            "Barrier Shift Parameters":             self.Barrier_Shift_Parameters.to_dict(),
        }


def build_pricer_request(term_sheet: TermSheet,
                         strikes:        List[float],
                         tenors:         List[str],
                         tenor_bump_sizes: List[float],
                         bump_size_abs:  float = 0.0025,
                         stock_ids:      List[str] = None,
                         max_paths:      int = 100000) -> Dict[str, Any]:
    if stock_ids is None:
        stock_ids = term_sheet.Stock_IDs

    request: Dict[str, Any] = {
        "action": "price",
        "pricer": "Autocallable Note",
        "greeks": {
            "M2M Value":     True,
            "Vega":          True,
            "Gamma":         True,
            "Average Lifetime": True
        },
        "numeric_parameters": {
            "Calibrate Dupire on Full Strike Range":         True,
            "Computation Type":                              "Monte Carlo",
            "Implied Volatility Average Fitting Error Tolerance": [1e-7, 2e-5],
            "Implied Volatility Fitting Error Tenor":        [1],
            "Implied Volatility Surface Fitter":             "TD Fitter",
            "Maximum Euler Timestep":                        1,
            "Maximum Euler Timestep Tenors":                 [0, 0.5, 1, 2],
            "Maximum Euler Timestep Values":                 [1, 5, 10, 10],
            "Number of Paths":                               max_paths,
            "Random Sampler Type":                           "NormalCNDFInvSampler",
            "Random Uniform Generator":                      "RandomSobol",
            "Use Unadjusted Barrier For Memory Event":       True,
        },
        "assumptions": {
            "Dividend Model":        "Discrete Proportional",
            "Volatility Model":      "Local Volatility Surface",
            "Volatility Sub Type":   "Effective Strike"
        },
        "termsheet": term_sheet.to_dict(),
        "bumps": [
            {
                "Type":        "Volatility Bump",
                "Bump Method": "Absolute",
                "Stock IDs":   stock_ids,
                "Strike":      strikes,          
                "Tenor Bump Sizes": tenor_bump_sizes,
                "Tenors":      tenors
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
        "storing_pricing_data": False,
    }

    return request

if __name__ == "__main__":
    bsp = BarrierShiftParameters(
        Autocall_Absolute_Shift=[-0.0087]*4,
        Autocall_Shift_Dates=["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
        Coupon_Absolute_Shift=[-0.0087]*4,
        Coupon_Absolute_Spread=[0.0174]*4,
        Coupon_Shift_Dates=["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
        Maturity_Barrier_Absolute_Shift=-0.0087,
        Maturity_Barrier_Absolute_Spread=0.0174,
        Maturity_Barrier_Knock_Out_Levels_Absolute_Shift=[-0.0087],
    )

    ts = TermSheet(
        Accrues_When="Inside Range",
        Autocall_Barrier=[1,1,1,1],
        Autocall_Dates=["2025-11-07","2026-02-09","2026-05-07","2026-08-07"],
        Autocall_Ex_Dates=["2025-11-10","2026-02-10","2026-05-08","2026-08-10"],
        Autocall_Pay_Dates=["2025-11-12","2026-02-12","2026-05-12","2026-08-12"],
        Basket_Level_Type="Weighted Sum of Asset Returns",
        Basket_Weights=[1],
        Coupon_Determination_Dates=["2025-11-10","2026-02-09","2026-05-07","2026-08-07"],
        Coupon_Determination_Ex_Dates=["2025-11-10","2026-02-10","2026-05-08","2026-08-10"],
        Coupon_Low_Barrier=[0.7]*4,
        Coupon_Memory_Cutoff_Dates=["2026-08-07"]*4,
        Coupon_Memory_Multiplier=[1]*4,
        Coupon_Multiple_Observation_Barrier_Type="Knock-Out",
        Coupon_Pay_Dates=["2025-11-12","2026-02-12","2026-05-12","2026-08-12"],
        Daycount_Basis="ACT/365",
        Downside_Participation=1,
        Fixed_Return=[0]*4,
        Floating_Payment_Multiplier=-1,
        Guaranteed_Minimum_Maturity_Return=0,
        Initial_Levels=[22726.012561111645],
        Is_Note=True,
        Maturity_Barrier=0.7,
        Maturity_Date="2026-08-07",
        Maturity_Option_Barrier_Type="Knock-In",
        Maturity_Settlement_Date="2026-08-12",
        Participation=[0]*4,
        Participation_With_Memory_Coupons=[0]*4,
        Pay_ID="USD",
        Premium_Settlement_Date="2025-07-10",
        Return_Notional_At_Recall=True,
        Stock_IDs=["NDX.IDX"],
        Strike_Setting_Date=["2025-07-07"],
        Variable_Coupon_Strike=[1]*4,
        Variable_Coupon_Strike_With_Memory_Coupons=[0]*5,
        Barrier_Shift_Parameters=bsp
    )

    strikes   = [0.8]       
    tenors    = ["3m","6m","9m","12m"]
    tenor_bump_sizes = [0, 0.0025, 0, 0]   

    request_dict = build_pricer_request(
        term_sheet=ts,
        strikes=strikes,
        tenors=tenors,
        tenor_bump_sizes=tenor_bump_sizes,
    )
