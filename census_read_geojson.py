import geopandas as gpd
import json
import os


def read_london_ward_geojson():

    # Get London GeoJSON
    london_jsonfile = "data/json_files/London_Ward_Boundaries.json"
    if not os.path.exists(london_jsonfile):

        # Census Ward Boundaries as GeoJSON
        census_jsonfile = "data/json_files/Census_Merged_Wards_(December_2011)_Boundaries.json"
        if not os.path.exists(census_jsonfile):

            # Get Census Boundaries as GeoPandas
            shapefile = 'data/Census_Merged_Wards_(December_2011)_Boundaries/Census_Merged_Wards_(December_2011)_Boundaries.shp'
            gdf = gpd.read_file(shapefile)
            # Convert coordinates
            gdf.to_crs(epsg=4326, inplace=True)
            # Write GeoJSON
            gdf.to_file(
                "data/json_files/Census_Merged_Wards_(December_2011)_Boundaries.json", driver='GeoJSON')

        with open(census_jsonfile) as f:
            census_wards = json.load(f)

        london_wards = census_wards
        london_wards['features'] = list(filter(
            lambda f: f['properties']['lad11cd'].startswith('E090000'), london_wards['features']))
        with open(london_jsonfile, 'w') as f:
            json.dump(london_wards, f)
    else:
        with open(london_jsonfile) as f:
            london_wards = json.load(f)
    return london_wards


def read_london_lad_geojson():

    # Get LAD GeoJSON
    london_jsonfile = "data/json_files/London_LAD_Boundaries.json"
    if not os.path.exists(london_jsonfile):

        lad_jsonfile = "data/json_files/Local_Authority_Districts_(December_2011)_Boundaries_EW_BFC.json"
        if not os.path.exists(lad_jsonfile):

            # Get Census LAD Boundaries as GeoPandas
            shapefile = 'data/Local_Authority_Districts_(December_2011)_Boundaries_EW_BFC/Local_Authority_Districts_(December_2011)_Boundaries_EW_BFC.shp'
            ladgdf = gpd.read_file(shapefile)
            # Convert coordinates
            ladgdf.to_crs(epsg=4326, inplace=True)
            # Write GeoJSON
            ladgdf.to_file(lad_jsonfile, driver='GeoJSON')

        with open(lad_jsonfile) as f:
            census_lads = json.load(f)

        london_lads = census_lads
        london_lads['features'] = list(filter(
            lambda f: f['properties']['lad11cd'].startswith('E090000'), london_lads['features']))
        with open(london_jsonfile, 'w') as f:
            json.dump(london_lads, f)
    else:
        with open(london_jsonfile) as f:
            london_lads = json.load(f)
    return london_lads


if __name__ == '__main__':
    london_wards = read_london_ward_geojson()
    london_lads = read_london_lad_geojson()
