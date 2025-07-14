import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List
from FPFServer import sync               # 你们已有的 API
from autocall_pricer import (            # 上一步封装好的函数
    build_pricer_request, TermSheet
)

# ---------- 0. 连接 FPF ----------
env = {"name": "axel", "password": "gnud2458927qeqhn745"}
fpf = sync("mkcoe04", 3456, env)

# ---------- 1. 读取 strikes & spot ----------
vol_handle   = {"get": {"what": "volatility index", "id": "NDX.IDX"}}
strike_meta  = fpf(vol_handle)           # 这里返回整张 vol surface meta
spot         = strike_meta["spot"]
strikes_abs  = strike_meta["strikes"]    # list[float]

# 把绝对 strike → 百分比
strikes_pct  = [k / spot for k in strikes_abs]

# ---------- 2. 构建 tenor grid ----------
tenor_months = list(range(0, 61, 6))     # 0m, 6m, …, 60m
tenor_grid   = [f"{m}m" for m in tenor_months]

# ---------- 3. 预先准备 TermSheet ----------
# （示例：ts 已在前一段代码里构造，这里直接复用）
ts = your_prepared_termsheet

# ---------- 4. 循环请求 Vega ----------
vega_matrix = np.zeros((len(strikes_pct), len(tenor_grid)))

for i_strike, strike_abs in enumerate(strikes_abs):
    for j_tenor, tenor in enumerate(tenor_grid):
        # 构造 bump 矩阵：只有 [i_strike, j_tenor] 是 0.0025 其余都 0
        bump_mat = np.zeros((len(strikes_pct), len(tenor_grid)))
        bump_mat[i_strike, j_tenor] = 0.0025
        
        req = build_pricer_request(
            term_sheet       = ts,
            strikes          = strike_abs,          # 单个 float
            tenors           = tenor_grid,
            tenor_bump_sizes = bump_mat.tolist(),   # 2-D list
            max_paths        = 100000,              # 视需要调整
        )
        resp = fpf(req)                 # 发送
        vega_matrix[i_strike, j_tenor] = resp["Vega"]  # <——按实际字段改

# ---------- 5. 画热力图 ----------
fig, ax = plt.subplots(figsize=(10, 6))

# x 轴：年份
x = np.array(tenor_months) / 12         # months → years
# y 轴：strike pct
y = np.array(strikes_pct)

c = ax.pcolormesh(x, y, vega_matrix, shading="auto")
fig.colorbar(c, ax=ax, label="Vega")

ax.set_xlabel("Tenor (years)")
ax.set_ylabel("Strike / Spot")
ax.set_title("Autocallable Note Vega Map")

plt.tight_layout()
plt.show()

from pathlib import Path
import matplotlib.pyplot as plt
# ...（前面的代码同上，生成 fig / ax / vega_matrix 等）...

# 5. 画热力图
fig, ax = plt.subplots(figsize=(10, 6))
c = ax.pcolormesh(x, y, vega_matrix, shading="auto")
fig.colorbar(c, ax=ax, label="Vega")
ax.set_xlabel("Tenor (years)")
ax.set_ylabel("Strike / Spot")
ax.set_title("Autocallable Note Vega Map")
plt.tight_layout()

# ---------- 把图保存到 Temp/ 目录 ----------
out_dir = Path("Temp")          # or Path("/mnt/data/Temp") 若你想放到绝对路径
out_dir.mkdir(parents=True, exist_ok=True)   # 如果目录不存在就创建
fig.savefig(out_dir / "vega_map.png", dpi=300, bbox_inches="tight")

plt.close(fig)  # 不再弹窗显示，节省内存
