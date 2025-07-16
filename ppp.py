vmax = max(abs(matrix.min()), abs(matrix.max()))

fig = go.Figure(
    go.Heatmap(
        z=matrix,
        x=tenors,
        y=y_vals,
        colorscale=[
            [0.0, 'red'],    
            [0.5, 'white'],  
            [1.0, 'green']   
        ],
        zmin=-vmax,
        zmax=+vmax,
        zmid=0,
        hovertemplate=hovertemplate
    )
)
