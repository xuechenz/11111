# --- 网格边界 & 中心 -----------------------------------------
strike_edges = [round(0.5 + 0.1*i, 2) for i in range(11)]          # 0.5 → 1.5
strike_centers = [(a+b)/2 for a,b in zip(strike_edges[:-1], strike_edges[1:])]

tenor_edges_m  = list(range(0, 60+3, 3))                           # 0,3,…,60
tenor_centers_m= [(a+b)//2 for a,b in zip(tenor_edges_m[:-1], tenor_edges_m[1:])]

tenors = [f"{m}m" for m in tenor_centers_m]                        # → ['1m','4m',…,'58m']
# strike_centers ⽤作 ks

def compute_vega_cell(
        ts: TermSheet,
        k_low: float, k_high: float,
        t_low_m: int, t_high_m: int,
        bump: float,
        stock_id: list[str],
        max_paths: int,
        pv0: float         
) -> float:
    req = build_pricer_request(
        term_sheet       = ts,
        rel_low_strk     = [k_low],
        rel_high_strk    = [k_high],
        short_term       = [f"{t_low_m}m"],
        long_term        = [f"{t_high_m}m"],
        tenor_bump_sizes = [bump],
        stock_ids        = stock_id,
        max_paths        = max_paths,
    )
    pv_bump = float(fpf(req)["M2M Value"])
    return (pv_bump - pv0) / bump

rows, cols = len(strike_centers), len(tenor_centers_m)
matrix_i = [[0.0]*cols for _ in range(rows)]

#调用
with ThreadPoolExecutor(max_workers=20) as exe:
    futs = {}
    for i, (k_lo,k_hi) in enumerate(zip(strike_edges[:-1], strike_edges[1:])):
        for j, (t_lo,t_hi) in enumerate(zip(tenor_edges_m[:-1], tenor_edges_m[1:])):
            fut = exe.submit(
                compute_vega_cell,
                ts, k_lo, k_hi, t_lo, t_hi,
                bump_size, [sid], max_paths, pv0
            )
            futs[fut] = (i, j)

    for fut in as_completed(futs):
        i, j = futs[fut]
        matrix_i[i][j] = fut.result()


def make_heatmap(strike_centers, tenor_centers_m,
                 matrix, avg_life, barrier_rel, stock):

    x_vals = [m/12 for m in tenor_centers_m]      
    y_vals = strike_centers                      

    vmax = max(abs(v) for row in matrix for v in row)

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=x_vals,
        y=y_vals,
        zmin=-vmax, zmax=vmax, zmid=0,
        colorscale=[[0,'red'], [0.5,'white'], [1,'green']],
        hovertemplate=("Strike: %{y:.2f}<br>"
                       "Tenor: %{x:.2f}y<br>"
                       "Vega: %{z:.4f}<extra></extra>")
    ))

    avg_m = int(round(avg_life*12))
    fig.add_vline(x=avg_m/12, line=dict(color="red", dash="dash"),
                  annotation_text=f"Avg Life: {avg_m}m",
                  annotation_position="top right")
    fig.add_hline(y=barrier_rel, line=dict(color="red", dash="dash"),
                  annotation_text=f"Barrier: {barrier_rel:.2f}",
                  annotation_position="bottom left")
    fig.add_trace(go.Scatter(x=[avg_m/12], y=[barrier_rel],
                             mode="markers",
                             marker=dict(color="red", size=8),
                             name="Intersection"))

    fig.update_xaxes(title="Tenor (years)")
    fig.update_yaxes(title="Relative Strike (×Spot)")
    fig.update_layout(title=f"{stock} Vega Map")
    return fig

#外部调用
fig_i = make_heatmap(strike_centers, tenor_centers_m,
                     matrix_i, avg_life,
                     _parse_float(vals["mat_barrier"]), sid)

matrices   = []
figs       = []
progress_bits = []

for sid in stock_ids:
    # ===== baseline PV=====
    req_base = build_pricer_request_no_bump(ts, [sid], max_paths)
    pv0 = float(fpf(req_base)["M2M Value"])
    print(f"{sid}  baseline PV = {pv0:.4f}")

    rows, cols = len(strike_centers), len(tenor_centers_m)
    matrix_i   = [[0.0]*cols for _ in range(rows)]

    with ThreadPoolExecutor(max_workers=20) as exe:
        futs = {}
        for i, (k_lo, k_hi) in enumerate(zip(strike_edges[:-1], strike_edges[1:])):
            for j, (t_lo, t_hi) in enumerate(zip(tenor_edges_m[:-1], tenor_edges_m[1:])):
                fut = exe.submit(
                    compute_vega_cell,
                    ts, k_lo, k_hi,
                    t_lo, t_hi,
                    bump_size, [sid],
                    max_paths,
                    pv0              
                )
                futs[fut] = (i, j)

        for fut in as_completed(futs):
            i, j = futs[fut]
            matrix_i[i][j] = fut.result()

    matrices.append(matrix_i)

    fig_i = make_heatmap(
        strike_centers,
        tenor_centers_m,
        matrix_i,
        avg_life,
        _parse_float(vals["mat_barrier"]),
        sid
    )
    figs.append(fig_i)
    progress_bits.append(f"{sid}: {rows*cols} cells")
