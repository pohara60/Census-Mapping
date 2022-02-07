import census_read_data as crd
import census_read_geojson as crg
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from dash import html
from dash import dcc
import dash
import dash_bootstrap_components as dbc
from turfpy.measurement import bbox
from functools import reduce

# Get Census Merged Ward and Local Authority Data
geography = crd.read_geography()
locationcol = "GeographyCode"
namecol = "Name"

# Get London GeoJSON
london_wards = crg.read_london_ward_geojson()

# Get LAD GeoJSON
london_lads = crg.read_london_lad_geojson()

# Get Census data index and its table_names
index = crd.read_index()
table_names = crd.get_table_names(index)

# Get first data table and its categories
table_name = table_names[0][0]
tdf = crd.read_table(table_name)

# Get first row data item (all categories All)
datacol = table_name + tdf.iloc[0, -1]

# Read the data table (all data items) and merge with the geography names
df = crd.read_data(table_name)
df = pd.merge(df, geography, on=locationcol)

# Filter London Data
london_ward_ids = list(map(lambda f: f['properties']
                           ['cmwd11cd'], london_wards["features"]))
london_flags = df[locationcol].isin(london_ward_ids)
ldf = df[london_flags]

london_lad_ids = list(map(lambda f: f['properties']
                          ['lad11cd'], london_lads["features"]))
london_flags = df[locationcol].isin(london_lad_ids)
london_lad_df = df[london_flags]

ward_max_value = ldf[datacol].max()
lad_max_value = london_lad_df[datacol].max()

# Dash


def blank_fig():
    # Blank figure for initial Dash display
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)
    return fig


def compute_bbox(gj):
    # Compute bounding box for GeoJSON
    gj_bbox_list = list(
        map(lambda f: bbox(f['geometry']), gj['features']))
    gj_bbox = reduce(
        lambda b1, b2: [min(b1[0], b2[0]), min(b1[1], b2[1]),
                        max(b1[2], b2[2]), max(b1[3], b2[3])],
        gj_bbox_list)
    return gj_bbox


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

local_authorities = london_lad_ids
all_local_authorities = ['All'] + local_authorities

map_controls = dbc.Card(
    [
        dbc.Row([
            dbc.Label("Granularity", html_for="granularity", width=2),
            dbc.Col(
                [
                    dbc.RadioItems(
                        id='granularity',
                        options=[{'label': i, 'value': i}
                                 for i in ['Local Authorities', 'Wards']],
                        value='Local Authorities',
                        inline=True
                    ),
                ],
                width=8
            )
        ]),

        dbc.Row([
            dbc.Label('Wards for Local Authority',
                      html_for="local-authority", width=2),
            dbc.Col(
                [
                    dbc.Select(
                        id='local-authority',
                        options=[
                            #{'label': i, 'value': i}
                            {'label': 'All' if i == 'All'
                                else geography[geography[locationcol] == i][namecol].iat[0],
                                'value': i}
                            for i in all_local_authorities],
                        value='All'
                    )
                ],
                width=8
            )

        ]),
    ]
)

app.layout = dbc.Container(
    [
        html.H1("Census Data"),
        html.Hr(),
        dbc.Col(
            [
                dbc.Row(map_controls),
                dbc.Row(dcc.Graph(id='map', figure=blank_fig()),
                        class_name='mt-3'),
            ],
            align="center",
        ),
    ],
    fluid=True,
)


@app.callback(
    Output('map', 'figure'),
    Input('local-authority', 'value'),
    Input('granularity', 'value'),
)
def update_graph(local_authority, granularity):

    if granularity == 'Local Authorities':
        fdf = london_lad_df
        gj = london_lads
        key = "properties.lad11cd"
        max_value = lad_max_value
        title = datacol + " by Local Authority"
    else:
        key = "properties.cmwd11cd"
        max_value = ward_max_value
        if local_authority == 'All':
            fdf = ldf
            gj = london_wards
            title = datacol + " by Ward"
        else:
            fdf = ldf[ldf['LAD11CD'].str.match(local_authority)]
            gj = {
                'features': list(filter(lambda f: f['properties']['lad11cd'] == local_authority,
                                        london_wards["features"])),
                'type': london_wards['type'],
                'crs': london_wards['crs']
            }
            title = datacol + " by Ward for Local Authority"

    gj_bbox = compute_bbox(gj)

    fig = px.choropleth(fdf,
                        geojson=gj,
                        locations=locationcol,
                        color=datacol,
                        color_continuous_scale="Viridis",
                        range_color=(0, max_value),
                        featureidkey=key,
                        scope='europe',
                        hover_data=[namecol, 'LAD11NM'],
                        title=title
                        )
    fig.update_geos(
        center_lon=(gj_bbox[0]+gj_bbox[2])/2.0,
        center_lat=(gj_bbox[1]+gj_bbox[3])/2.0,
        lonaxis_range=[gj_bbox[0], gj_bbox[2]],
        lataxis_range=[gj_bbox[1], gj_bbox[3]],
        visible=False,
    )
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=30),
                      title_x=0.5,
                      width=1200, height=600)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
