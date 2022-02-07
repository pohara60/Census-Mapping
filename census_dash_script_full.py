from dash.exceptions import PreventUpdate
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
london_ward_ids = list(map(lambda f: f['properties']
                           ['cmwd11cd'], london_wards["features"]))

# Get LAD GeoJSON
london_lads = crg.read_london_lad_geojson()
london_lad_ids = list(map(lambda f: f['properties']
                          ['lad11cd'], london_lads["features"]))


index = crd.read_index()
table_names = crd.get_table_names(index)


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

table_controls = dbc.Card(
    [
        dbc.Row([
            dbc.Label('Table Name',
                      html_for="table-name", width=2),
            dbc.Col([
                    dbc.Select(
                        id='table-name',
                        options=[
                            {'label': table[1], 'value': table[0]}
                            for table in table_names]
                    )
                    ], width=8
                    )
        ])
    ])

category_controls = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Label('Category1',
                          id='category-1-label',
                          html_for="category-1-values", width=2),
                dbc.Col([dbc.Select(id='category-1-values')], width=8)
            ],
            style={'display': 'none'},
            id='category-1-container'
        ),
        dbc.Row(
            [
                dbc.Label('Category2',
                          id='category-2-label',
                          html_for="category-2-values", width=2),
                dbc.Col([dbc.Select(id='category-2-values')], width=8)
            ],
            style={'display': 'none'},
            id='category-2-container'
        ),
        dbc.Row(
            [
                dbc.Label('Category3',
                          id='category-3-label',
                          html_for="category-3-values", width=2),
                dbc.Col([dbc.Select(id='category-3-values')], width=8)
            ],
            style={'display': 'none'},
            id='category-3-container'
        ),
        dbc.Row(
            [
                dbc.Label('Category4',
                          id='category-4-label',
                          html_for="category-4-values", width=2),
                dbc.Col([dbc.Select(id='category-4-values')], width=8)
            ],
            style={'display': 'none'},
            id='category-4-container'
        ),
    ]
)

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
                dbc.Row(table_controls),
                dbc.Row(category_controls),
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
    Output('category-1-label', 'children'),
    Output('category-1-values', 'options'),
    Output('category-1-container', 'style'),
    Output('category-2-label', 'children'),
    Output('category-2-values', 'options'),
    Output('category-2-container', 'style'),
    Output('category-3-label', 'children'),
    Output('category-3-values', 'options'),
    Output('category-3-container', 'style'),
    Output('category-4-label', 'children'),
    Output('category-4-values', 'options'),
    Output('category-4-container', 'style'),
    Input('table-name', 'value'),
    Input('category-1-values', 'value'),
    Input('category-2-values', 'value'),
    Input('category-3-values', 'value'),
    Input('category-4-values', 'value'),
    Input('local-authority', 'value'),
    Input('granularity', 'value'),
)
def update_graph(table_name,
                 category1, category2, category3, category4,
                 local_authority, granularity):

    if table_name is None:
        raise PreventUpdate

    tdf = crd.read_table(table_name)
    categories = crd.get_table_column_names_and_values(tdf)

    # Update categories
    all_categories = True
    category1label = ''
    category1values = []
    category1style = {'display': 'none'}
    if len(categories) >= 1:
        category1label = categories[0][0]
        category1values = [{'label': cat, 'value': cat}
                           for cat in categories[0][1]]
        category1style = {'display': 'flex'}
        if category1 is None:
            all_categories = False
        else:
            query_string = f'`{category1label}` == "{category1}"'
    category2label = ''
    category2values = []
    category2style = {'display': 'none'}
    if len(categories) >= 2:
        category2label = categories[1][0]
        category2values = [{'label': cat, 'value': cat}
                           for cat in categories[1][1]]
        category2style = {'display': 'flex'}
        if category2 is None:
            all_categories = False
        else:
            query_string += f' & `{category2label}` == "{category2}"'
    category3label = ''
    category3values = []
    category3style = {'display': 'none'}
    if len(categories) >= 3:
        category3label = categories[2][0]
        category3values = [{'label': cat, 'value': cat}
                           for cat in categories[2][1]]
        category3style = {'display': 'flex'}
        if category3 is None:
            all_categories = False
        else:
            query_string += f' & `{category3label}` == "{category3}"'
    category4label = ''
    category4values = []
    category4style = {'display': 'none'}
    if len(categories) >= 4:
        category4label = categories[3][0]
        category4values = [{'label': cat, 'value': cat}
                           for cat in categories[3][1]]
        category4style = {'display': 'flex'}
        if category4 is None:
            all_categories = False
        else:
            query_string += f' & `{category4label}` == "{category4}"'

    # If all categories are specified then get data
    print(f"all_categories={all_categories}")
    if not all_categories:
        fig = blank_fig()
        return fig, category1label, category1values, category1style, category2label, category2values, category2style, category3label, category3values, category3style, category4label, category4values, category4style

    df = crd.read_data(table_name)
    # Add names to data
    df = pd.merge(df, geography, on=locationcol)

    # Filter London Data
    london_flags = df[locationcol].isin(london_ward_ids)
    london_ward_df = df[london_flags]

    london_flags = df[locationcol].isin(london_lad_ids)
    london_lad_df = df[london_flags]

    trow = tdf.query(query_string)
    datacol = table_name + trow.iloc[0, -1]
    ward_max_value = london_ward_df[datacol].max()
    lad_max_value = london_lad_df[datacol].max()

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
            fdf = london_ward_df
            gj = london_wards
            title = datacol + " by Ward"
        else:
            fdf = london_ward_df[london_ward_df['LAD11CD'].str.match(
                local_authority)]
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
    return fig, category1label, category1values, category1style, category2label, category2values, category2style, category3label, category3values, category3style, category4label, category4values, category4style


if __name__ == '__main__':
    app.run_server(debug=True)
