def make_heatmap(strikes, spot, matrix, tenors, avg_life, barrier, stock):
    x_vals = [int(t.rstrip("m")) for t in tenors]   
    y_vals = [s/spot for s in strikes]

    fig = go.Figure(
       go.Heatmap(
         x=x_vals,
         y=y_vals,
         z=matrix,
         colorscale="RdYlGn",
         zmid=0,
         hovertemplate="Strike: %{y:.2f}<br>Tenor: %{x}m<br>Vega: %{z:.4f}<extra></extra>"
       )
    )

    fig.update_xaxes(
      tickmode="array",
      tickvals=x_vals,
      ticktext=tenors,        
      title="Tenor"
    )
    fig.update_yaxes(title="Strike / Spot")

    avg_m = int(round(avg_life*12))
    fig.add_vline(x=avg_m,
                  line=dict(color="red", dash="dash"),
                  annotation_text=f"Avg Life: {avg_m}m",
                  annotation_position="top right")

    fig.add_hline(y=barrier,
                  line=dict(color="red", dash="dash"),
                  annotation_text=f"Barrier: {barrier:.2f}",
                  annotation_position="bottom left")

    fig.add_trace(go.Scatter(x=[avg_m], y=[barrier],
                             mode="markers",
                             marker=dict(color="red", size=8),
                             name="Intersection"))

    fig.update_layout(title=f"{stock} Vega Map")
    return fig
