import census_read_data as crd
import census_read_geojson as crg
import pandas as pd
import plotly.express as px

# Get Census Merged Ward and Local Authority Data
geography = crd.read_geography()
locationcol = "GeographyCode"
namecol = "Name"

# Get LAD GeoJSON
london_lads = crg.read_london_lad_geojson()

# Get Census data index and its table_names
index = crd.read_index()
table_names = crd.get_table_names(index)

# Get first data table
table_name = table_names[0][0]
tdf = crd.read_table(table_name)

# Get first row data item (all categories All)
datacol = table_name + tdf.iloc[0, -1]

# Read the data table (all data items) and merge with the geography names
df = crd.read_data(table_name)
df = pd.merge(df, geography, on=locationcol)

# Filter London Data
london_lad_ids = list(map(lambda f: f['properties']
                          ['lad11cd'], london_lads["features"]))
london_flags = df[locationcol].isin(london_lad_ids)
london_lad_df = df[london_flags]

# Map data by LAD
key = "properties.lad11cd"
max_value = london_lad_df[datacol].max()
title = datacol + " by Local Authority"

fig = px.choropleth(london_lad_df,
                    geojson=london_lads,
                    locations=locationcol,
                    color=datacol,
                    color_continuous_scale="Viridis",
                    range_color=(0, max_value),
                    featureidkey=key,
                    scope='europe',
                    hover_data=[namecol],
                    title=title
                    )
fig.update_geos(
    fitbounds="locations",
    visible=False,
)
fig.update_layout(margin=dict(l=0, r=0, b=0, t=30),
                  title_x=0.5,
                  width=1200, height=600)
fig.show()
