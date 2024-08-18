import streamlit as st
import leafmap.foliumap as leafmap
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, inspect
from shapely import wkb
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform
from pyproj import CRS, Transformer
import folium

from streamlit_folium import st_folium
import openrouteservice
from openrouteservice import convert

import os


##Creating Layout View
st.set_page_config(page_title="Georefferencing",page_icon="",layout="wide")


##SETING LOGO SIDE BAR
st.sidebar.title("DEEDZONE FAMILY")
logo = "https://cdn.vectorstock.com/i/500p/58/22/geodesic-device-and-wind-rose-vector-14905822.jpg"
st.sidebar.image(logo)


# Add the services list to the sidebar
st.sidebar.header("Our Services")
services = """
- Title Deed and Lease Processing
- Topographical Surveying
- Beacons Identification
- Land Consultancy
- Area Confirmation
- Subdivisions
"""
st.sidebar.markdown(services)


##SET CONNECTION TO DATABASE
host = "localhost"
database = "SDB"
user = os.getenv('postgres')
password = os.getenv('39208072')



# Create a connection string for SQLAlchemy
connection_string = f"postgresql+psycopg2://{'postgres'}:{'39208072'}@{'localhost'}/{'SDB'}"

# Create the SQLAlchemy engine
engine = create_engine(connection_string)

# Example: Connect to the database and print the table names
with engine.connect() as connection:


###SELECTION FROM ALL TABLES ALLOCATED

    # inspector = inspect(engine)
    # tables = inspector.get_table_names()
    # st.write("Available tables:", tables)

    # # Example: Fetch and display data from a table
    # if tables:
    #     query = f"SELECT * FROM {tables[0]} LIMIT 5"
    #     df = pd.read_sql(query, connection)
    #     st.write(df)




###SELECTION FROM A SPECIFIC TABLE NAME
    query = "SELECT * FROM kwale"  # Adjust the query as needed
    df = pd.read_sql(query, connection)
    st.write("Data from 'kwale' table:")
    st.write(df)


    # Create dropdowns for 'source' and 'plot number'
    source_options = df['source'].unique()
    selected_source = st.selectbox('Select Source', source_options)

    # Filter the dataframe based on the selected source
    filtered_df = df[df['source'] == selected_source]

    plot_number_options = filtered_df['plot_no'].unique()
    selected_plot_number = st.selectbox('Select Plot Number', plot_number_options)

    # Filter the dataframe based on the selected plot number
    plot_df = filtered_df[filtered_df['plot_no'] == selected_plot_number]

m = leafmap.Map(minimap_control=True,center = [-4, 39], zoom = 9)
m.add_basemap("HYBRID")



# Check if plot_df is not empty
if not plot_df.empty:
        # Parse the geometry using shapely
        geom = plot_df.iloc[0]['geom']
        polygon = wkb.loads(geom, hex=True)

        # Define the source and destination CRS
        src_crs = CRS.from_epsg(21037)  # Example EPSG:32737 (UTM Zone 37S)
        dst_crs = CRS.from_epsg(4326)   # WGS84

        # Transformer to reproject the geometry
        transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)

        # Reproject the geometry to WGS84
        reprojected_polygon = transform(transformer.transform, polygon)

        # Get the bounding box of the reprojected polygon
        if isinstance(reprojected_polygon, Polygon):
            bounds = reprojected_polygon.bounds
        elif isinstance(reprojected_polygon, MultiPolygon):
            bounds = reprojected_polygon.envelope.bounds

        # Calculate the center of the bounding box
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        # Fit the map to the bounds of the reprojected polygon
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        # Add the reprojected polygon to the map
        folium.GeoJson(
            data=reprojected_polygon.__geo_interface__,
            name='Selected Plot',
            tooltip=f"Plot Number: {selected_plot_number}\nSource: {selected_source}"
        ).add_to(m)


        # Extract and display the coordinates of each corner
        # st.write("Coordinates of each corner:")
        # coordinates = []
        # if isinstance(reprojected_polygon, Polygon):
        #     coordinates = list(reprojected_polygon.exterior.coords)
        # elif isinstance(reprojected_polygon, MultiPolygon):
        #     for poly in reprojected_polygon.geoms:
        #         coordinates.extend(list(poly.exterior.coords))

        # for idx, coord in enumerate(coordinates):
        #     lon, lat = coord[:2]  # Ignore any additional values (e.g., elevation)
        #     st.write(f"Corner {idx + 1}: Latitude: {lat}, Longitude: {lon}")

        # Transformer to reproject the coordinates back to UTM Zone 37S for display in Streamlit
        transformer_to_utm = Transformer.from_crs(dst_crs, src_crs, always_xy=True)

        
        # Extract and display the coordinates of each corner
        st.write("Coordinates of each corner (UTM Zone 37S):")
        coordinates = []
        if isinstance(reprojected_polygon, Polygon):
            coordinates = list(reprojected_polygon.exterior.coords)
        elif isinstance(reprojected_polygon, MultiPolygon):
            for poly in reprojected_polygon.geoms:
                coordinates.extend(list(poly.exterior.coords))

        for idx, coord in enumerate(coordinates):
            lon, lat = coord[:2]  # Ignore any additional values (e.g., elevation)
            utm_x, utm_y = transformer_to_utm.transform(lon, lat)
            st.write(f"Corner {idx + 1}: UTM X: {utm_x}, UTM Y: {utm_y}")


m.to_streamlit(height=500)


#     # Display the map in Streamlit
# st_folium(m, height=500)

#     # JavaScript to get the user's current location
# st.markdown(
#         """
#         <script>
#         function getLocation() {
#             navigator.geolocation.getCurrentPosition(success, error);
#         }

#         function success(position) {
#             const latitude = position.coords.latitude;
#             const longitude = position.coords.longitude;
#             const coordinates = {lat: latitude, lon: longitude};
#             Streamlit.setComponentValue(coordinates);
#         }

#         function error() {
#             console.warn('ERROR(${err.code}): ${err.message}');
#         }

#         getLocation();
#         </script>
#         """, unsafe_allow_html=True
#     )

#     # Get the user's current location
# current_location = st.experimental_get_query_params().get("latlon", None)
# if current_location:
#     current_lat = current_location[0]
#     current_lon = current_location[1]

#     # Display the current location
#     st.write(f"Your current location: Latitude {current_lat}, Longitude {current_lon}")

#     # Get the route from the current location to the plot center using OpenRouteService API
#     ors_api_key = '5b3ce3597851110001cf62480f41c5a94cbe45dbbf27ee6744af76b9'
#     client = openrouteservice.Client(key=ors_api_key)

#     # Define the start and end points
#     start = (float(current_lon), float(current_lat))
#     end = (center_lon, center_lat)

#     # Request the route
#     route = client.directions(coordinates=[start, end], profile='driving-car', format='geojson')

#     # Extract the route coordinates
#     route_coords = route['features'][0]['geometry']['coordinates']
#     folium.PolyLine(locations=[(coord[1], coord[0]) for coord in route_coords], color='blue').add_to(m)

#     # Display the updated map with the route
#     st_folium(m, height=500)

#     # Display route details
#     distance = route['features'][0]['properties']['segments'][0]['distance']
#     duration = route['features'][0]['properties']['segments'][0]['duration']
#     st.write(f"Route to the plot: {distance} meters, {duration} seconds")
