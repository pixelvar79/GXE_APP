
    
# import os
# import tempfile
# import logging
# import numpy as np
# import rasterio
# from rasterio.transform import Affine
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# from PIL import Image
# from datetime import datetime
# from collections import defaultdict
# from flask import Flask, send_from_directory, jsonify, request
# from pyproj import Transformer
# import geopandas as gpd
# import pandas as pd
# import math
# from shapely.geometry import Polygon
# import json


# import os
# import pandas as pd
# import rasterio
# import geopandas as gpd
# import numpy as np
# import rasterio.mask
# from datetime import datetime
# from rasterio.mask import mask

# logging.basicConfig(level=logging.INFO)
# logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
# logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

# BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data"
# IMAGES_DIRECTORY = os.path.join(BASE_DIRECTORY, 'images')

# def normalize_data(data, clip_min, clip_max):
#     data = np.clip(data, clip_min, clip_max)
#     data = ((data - clip_min) / (clip_max - clip_min) * 255).astype(np.uint8)
#     return data

# def process_files(input_folder):
#     results = []

#     # Walk through the directory and find _shifted.tif files
#     for root, dirs, files in os.walk(input_folder):
#         for file in files:
#             if file.endswith('_shifted.tif'):
#                 file_path = os.path.join(root, file)
#                 print(f'file found: {file_path}')
#                 result = process_tif(file_path)
#                 if result:
#                     results.append(result)

#     return results
# def process_tif(tif_path):
#     try:
#         with rasterio.open(tif_path) as src:
#             if src.crs != 'EPSG:4326':
#                 logging.debug(f"Original CRS: {src.crs}")
#                 transform, width, height = calculate_default_transform(
#                     src.crs, 'EPSG:4326', src.width, src.height, *src.bounds)
#                 kwargs = src.meta.copy()
#                 kwargs.update({
#                     'crs': 'EPSG:4326',
#                     'transform': transform,
#                     'width': width,
#                     'height': height
#                 })

#                 reprojected_tif_path = os.path.join(tempfile.gettempdir(), 'reprojected_' + os.path.basename(tif_path))
#                 with rasterio.open(reprojected_tif_path, 'w', **kwargs) as dst:
#                     for i in range(1, src.count + 1):
#                         reproject(
#                             source=rasterio.band(src, i),
#                             destination=rasterio.band(dst, i),
#                             src_transform=src.transform,
#                             src_crs=src.crs,
#                             dst_transform=transform,
#                             dst_crs='EPSG:4326',
#                             resampling=Resampling.nearest)
#                 original_tif_path = tif_path
#                 tif_path = reprojected_tif_path
#                 logging.debug("TIFF file reprojected to EPSG:4326")

#             # Extract bounds for correct overlay
#             with rasterio.open(tif_path) as reprojected_src:
#                 bounds = reprojected_src.bounds  # Ensure we use reprojected bounds
#                 logging.debug(f"Reprojected TIFF bounds: {bounds}")

#                 # Read bands 1, 2, 3 and normalize
#                 data = reprojected_src.read([3, 2, 1])

#                 # Normalize the data to the range 0-255 using dynamic clip_min and clip_max
#                 clip_min, clip_max = np.percentile(data, (2, 98))
#                 data = normalize_data(data, clip_min, clip_max)

#                 logging.debug("Normalized bands to 0-255 with clipping and scaling")

#                 # Create an RGB image with an alpha channel
#                 alpha = np.all(data == 0, axis=0).astype(np.uint8) * 255
#                 img = np.dstack((data[0], data[1], data[2], 255 - alpha))
#                 img = Image.fromarray(img, 'RGBA')
#                 png_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(os.path.basename(tif_path))[0]}.png")
#                 img.save(png_path)
#                 logging.debug(f"Saved PNG image: {png_path}")

#         return {
#             "png_path": f"/temp/{os.path.basename(png_path)}",
#             "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
#             "ortho_path": tif_path,
#             "original_ortho_path": original_tif_path
#         }
#     except Exception as e:
#         logging.error(f"Error processing file {tif_path}: {e}")
#         return {"error": str(e)}
    

# def list_geojson_files():
#     geojson_files = []
#     for root, dirs, files in os.walk(IMAGES_DIRECTORY):
#         for file in files:
#             if file.endswith('_shifted.geojson'):
#                 relative_path = os.path.relpath(os.path.join(root, file), IMAGES_DIRECTORY)
#                 geojson_files.append(relative_path)
#     return jsonify(geojson_files)

# # def reprojected_geojson(filepath):
# #     file_path = os.path.join(IMAGES_DIRECTORY, filepath)
# #     if not os.path.exists(file_path):
# #         return jsonify({"error": "File not found"}), 404

# #     gdf = gpd.read_file(file_path)
# #     gdf = gdf.to_crs("EPSG:4326")
# #     return jsonify(gdf.__geo_interface__)
# def reprojected_geojson(filepath):
#     file_path = os.path.join(IMAGES_DIRECTORY, filepath)
#     if not os.path.exists(file_path):
#         return jsonify({"error": "File not found"}), 404

#     # Read the GeoJSON file
#     gdf = gpd.read_file(file_path)
#     gdf = gdf.to_crs("EPSG:4326")

#     # Extract the second string from the GeoJSON file name
#     geojson_name = os.path.basename(filepath)
#     second_string = geojson_name.split('_')[1]

#     # Look for a CSV file in the same subfolder
#     csv_folder = os.path.dirname(file_path)
#     csv_file = None
#     for file in os.listdir(csv_folder):
#         if file.endswith('.csv') and second_string in file:
#             csv_file = os.path.join(csv_folder, file)
#             break

#     if csv_file:
#         # Read the CSV file
#         df = pd.read_csv(csv_file)

#         # Perform an inner join on the 'order' column
#         gdf = gdf.merge(df, on='order')

#     return jsonify(gdf.__geo_interface__)


# def extract_statistics(tif_file, shp_file, order_ids=None):
#     # # Load the shapefile using GeoPandas
#     # gdf = gpd.read_file(shp_file)
#     # print(f'shpfile is : {shp_file}')
#     # Load the shapefile using GeoPandas
#     gdf = gpd.read_file(shp_file)
#     print(f'shpfile is : {shp_file}')
   
#     # Extract the second string from the GeoJSON file name
#     geojson_name = os.path.basename(shp_file)
#     second_string = geojson_name.split('_')[1]

#     # Look for a CSV file in the same subfolder
#     csv_folder = os.path.dirname(shp_file)
#     csv_file = None
#     for file in os.listdir(csv_folder):
#         if file.endswith('.csv') and second_string in file:
#             csv_file = os.path.join(csv_folder, file)
#             break
    
#     if csv_file:
#         # Read the CSV file
#         df = pd.read_csv(csv_file)

#         # Perform an inner join on the 'order' column
#         gdf = gdf.merge(df, on='order')
    
#     # Filter the GeoJSON data based on the order_ids if provided
#     if order_ids:
#         filtered_gdf = gdf[gdf['order'].isin(order_ids)]
#     else:
#         filtered_gdf = gdf
        
#     print(f'filtered_gdf is : {filtered_gdf.head()}')

#     # Open the TIF file using Rasterio
#     with rasterio.open(tif_file) as src:
#         # Read the first 6 bands (excluding any additional bands)
#         bands = src.read([1, 2, 3, 4, 5, 6])

#         # Define the column names based on the number of bands and statistics descriptors
#         stats_descriptors = ['mean', 'std', 'max', 'min']
#         band_columns = [f'Band_{i}_{stat}' for i in range(1, 7) for stat in stats_descriptors]

#         # Include NDVI and NDRE columns in the column names
#         column_names = ['TIF_Name', 'Date', 'Date_julian', 'plotID', 'identifier','barcode'] + band_columns + ['NDVI_mean', 'NDVI_std', 'NDVI_max', 'NDVI_min'] + ['NDRE_mean', 'NDRE_std', 'NDRE_max', 'NDRE_min'] + ['fcover']

#         # Create an empty DataFrame to store the results
#         result_df = pd.DataFrame(columns=column_names)

#         # Extract the second string from the TIF name as the 'Date'
#         date_string = os.path.splitext(os.path.basename(tif_file))[0].split('_')[2]
        
#         # Format the date as MM-DD-YYYY
#         formatted_date = datetime.strptime(date_string, '%m%d%Y').strftime('%m-%d-%Y')

#         # Convert the formatted date to Julian date
#         julian_date = datetime.strptime(formatted_date, '%m-%d-%Y').timetuple().tm_yday

#         # Iterate over each row in the filtered GeoDataFrame
#         for index, row in filtered_gdf.iterrows():
#             # Get the geometry of the polygon
#             geom = row['geometry']

#             # Get the attributes from the shapefile
#             attributes = [row[field] for field in filtered_gdf.columns if field != 'geometry']

#             # Extract the 'Identifier' field from the shapefile
#             identifier = row['identifier']

#             # Initialize lists to store band statistics for each band
#             band_stats_list = [[] for _ in range(6)]
#             nodata_value = 65535
#             try:
#                 # Iterate over each band within the polygon
#                 for band_index in range(6):
#                     masked_data, _ = mask(src, [geom], nodata=nodata_value, crop=True)

#                     # Calculate statistics for the masked data
#                     band_stats = [getattr(np, stat)(masked_data[band_index][masked_data[band_index] != nodata_value]) for stat in stats_descriptors]
#                     band_stats_list[band_index] = band_stats

#                 # Calculate NDVI and NDRE from masked_data
#                 ndvi_values = (masked_data[4] - masked_data[2]) / (masked_data[4] + masked_data[2])
#                 ndre_values = (masked_data[4] - masked_data[3]) / (masked_data[4] + masked_data[3])

#                 # Calculate NDVI and NDRE statistics for the polygon
#                 ndvi_stats = [getattr(np, stat)(ndvi_values) for stat in stats_descriptors]
#                 ndre_stats = [getattr(np, stat)(ndre_values) for stat in stats_descriptors]

#                 # Calculate fcover for the polygon
#                 green_pixels = np.count_nonzero(ndvi_values > 0.65)
#                 total_pixels = np.count_nonzero(ndvi_values)
#                 fcover = (green_pixels / total_pixels) * 100

#                 # Create a row for the DataFrame
#                 row_data = [os.path.basename(tif_file), formatted_date, julian_date, row['order'], identifier, row['Barcode Labels']] + [stat for band_stats in band_stats_list for stat in band_stats] + ndvi_stats + ndre_stats + [fcover]

#             except Exception as e:
#                 # Handle the case when intersection is empty
#                 print(f"Error processing row {index}: {e}")
#                 row_data = [os.path.basename(tif_file), formatted_date, julian_date, row['order'], identifier, row['Barcode Labels']] + [np.nan] * (len(result_df.columns) - 5)
#                 # Change only the NaN values to a specific numeric value (e.g., -66666)
#                 row_data = pd.Series(row_data).fillna(-66666).tolist()

#             finally:
#                 # Append the row to the result DataFrame
#                 result_df.loc[len(result_df)] = row_data

#         # Print the result DataFrame
#         print(f'dataframe is : {result_df.head()}')

#     return result_df



# def process_selected_polygons():
#     data = request.json
#     print(f'data passed to process_selected_polygons: {data}')
#     selected_plots = data['selectedPlots']
    
#     print('Received selected plots list data in the backend:', selected_plots)
    
#     # Group plots by the second string in their geojsonPath
#     grouped_plots = {}
#     for plot in selected_plots:
#         geojson_path = os.path.join(IMAGES_DIRECTORY, plot['geojsonPath'])
#         order_id = plot['orderID']
        
#         print(f'GeoJSON path for plot {order_id}: {geojson_path}')
        
#         # Extract the subfolder and the second string pattern from the geojsonPath
#         subfolder = os.path.dirname(geojson_path)
#         geojson_filename = os.path.basename(geojson_path)
#         second_string_pattern = geojson_filename.split('_')[1]
        
#         # Group by the second string pattern
#         if second_string_pattern not in grouped_plots:
#             grouped_plots[second_string_pattern] = {'geojson_path': geojson_path, 'order_ids': [], 'tif_paths': []}
#         grouped_plots[second_string_pattern]['order_ids'].append(order_id)
    
#     # Look for _shifted.tif files in the subfolder that share the same second string pattern
#     for group_key, group in grouped_plots.items():
#         subfolder = os.path.dirname(group['geojson_path'])
#         for root, dirs, files in os.walk(subfolder):
#             for file in files:
#                 if file.endswith('_shifted.tif') and group_key in file:
#                     tif_path = os.path.join(root, file)
#                     print(f'TIF path identified for group {group_key}: {tif_path}')
#                     group['tif_paths'].append(tif_path)
                    
#     combined_results_df = pd.DataFrame()
#     combined_all_plots_df = pd.DataFrame()
#     for group_key, group in grouped_plots.items():
#         print(f'Processing group: {group_key}')
#         geojson_path = group['geojson_path']
#         order_ids = group['order_ids']
#         print(f'GeoJSON path for group {group_key}: {geojson_path}')
#         print(f'Order IDs for group {group_key}: {order_ids}')
#         print(f'TIF paths for group {group_key}:')
#         for tif_path in group['tif_paths']:
#             print(f'  {tif_path}')
            
#             if os.path.exists(tif_path):
#                 # Pass the subsetted GeoJSON area and the corresponding TIFs to extract_statistics()
#                 result_df = extract_statistics(tif_path, geojson_path, order_ids)
#                 combined_results_df = pd.concat([combined_results_df, result_df], ignore_index=True)
                
#                 # Extract statistics for all plots
#                 all_plots_df = extract_statistics(tif_path, geojson_path)
#                 combined_all_plots_df = pd.concat([combined_all_plots_df, all_plots_df], ignore_index=True)
    
#     # Print the combined result DataFrame
#     print(f'Combined dataframe for selected plots is : {combined_results_df.head(30)}')
#     print(f'Combined dataframe for all plots is : {combined_all_plots_df.head(30)}')

#     return {
#         'selected_plots': combined_results_df.to_json(orient='records'),
#         'all_plots': combined_all_plots_df.to_json(orient='records')
#     }



    
import os
import tempfile
import logging
import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image
from datetime import datetime
from collections import defaultdict
from flask import Flask, send_from_directory, jsonify, request
from pyproj import Transformer
import geopandas as gpd
import pandas as pd
import math
from shapely.geometry import Polygon
import json


import os
import pandas as pd
import rasterio
import geopandas as gpd
import numpy as np
import rasterio.mask
from datetime import datetime
from rasterio.mask import mask
import re


logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data"
IMAGES_DIRECTORY = os.path.join(BASE_DIRECTORY, 'images')

def normalize_data(data, clip_min, clip_max):
    data = np.clip(data, clip_min, clip_max)
    data = ((data - clip_min) / (clip_max - clip_min) * 255).astype(np.uint8)
    return data

def process_files(input_folder):
    results = []

    # Walk through the directory and find _shifted.tif files
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('_shifted.tif'):
                file_path = os.path.join(root, file)
                print(f'file found: {file_path}')
                result = process_tif(file_path)
                if result:
                    results.append(result)

    return results
def process_tif(tif_path):
    try:
        with rasterio.open(tif_path) as src:
            if src.crs != 'EPSG:4326':
                logging.debug(f"Original CRS: {src.crs}")
                transform, width, height = calculate_default_transform(
                    src.crs, 'EPSG:4326', src.width, src.height, *src.bounds)
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': 'EPSG:4326',
                    'transform': transform,
                    'width': width,
                    'height': height
                })

                reprojected_tif_path = os.path.join(tempfile.gettempdir(), 'reprojected_' + os.path.basename(tif_path))
                with rasterio.open(reprojected_tif_path, 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs='EPSG:4326',
                            resampling=Resampling.nearest)
                original_tif_path = tif_path
                tif_path = reprojected_tif_path
                logging.debug("TIFF file reprojected to EPSG:4326")

            # Extract bounds for correct overlay
            with rasterio.open(tif_path) as reprojected_src:
                bounds = reprojected_src.bounds  # Ensure we use reprojected bounds
                logging.debug(f"Reprojected TIFF bounds: {bounds}")

                # Read bands 1, 2, 3 and normalize
                data = reprojected_src.read([3, 2, 1])

                # Normalize the data to the range 0-255 using dynamic clip_min and clip_max
                clip_min, clip_max = np.percentile(data, (2, 98))
                data = normalize_data(data, clip_min, clip_max)

                logging.debug("Normalized bands to 0-255 with clipping and scaling")

                # Create an RGB image with an alpha channel
                alpha = np.all(data == 0, axis=0).astype(np.uint8) * 255
                img = np.dstack((data[0], data[1], data[2], 255 - alpha))
                img = Image.fromarray(img, 'RGBA')
                png_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(os.path.basename(tif_path))[0]}.png")
                img.save(png_path)
                logging.debug(f"Saved PNG image: {png_path}")

        return {
            "png_path": f"/temp/{os.path.basename(png_path)}",
            "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
            "ortho_path": tif_path,
            "original_ortho_path": original_tif_path
        }
    except Exception as e:
        logging.error(f"Error processing file {tif_path}: {e}")
        return {"error": str(e)}
    

def list_geojson_files():
    geojson_files = []
    for root, dirs, files in os.walk(IMAGES_DIRECTORY):
        for file in files:
            if file.endswith('_shifted.geojson'):
                relative_path = os.path.relpath(os.path.join(root, file), IMAGES_DIRECTORY)
                geojson_files.append(relative_path)
    return jsonify(geojson_files)


def reprojected_geojson(filepath):
    file_path = os.path.join(IMAGES_DIRECTORY, filepath)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # Read the GeoJSON file
    gdf = gpd.read_file(file_path)
    gdf = gdf.to_crs("EPSG:4326")

    # Extract the second string from the GeoJSON file name
    geojson_name = os.path.basename(filepath)
    second_string = geojson_name.split('_')[1]

    # Look for a CSV file in the same subfolder
    csv_folder = os.path.dirname(file_path)
    csv_file = None
    for file in os.listdir(csv_folder):
        if file.endswith('.csv') and second_string in file:
            csv_file = os.path.join(csv_folder, file)
            break

    if csv_file:
        # Read the CSV file
        df = pd.read_csv(csv_file)

        # Perform an inner join on the 'order' column
        gdf = gdf.merge(df, on='order')

    return jsonify(gdf.__geo_interface__)


def extract_statistics(tif_file, shp_file, order_ids=None):
    # # Load the shapefile using GeoPandas
    # gdf = gpd.read_file(shp_file)
    # print(f'shpfile is : {shp_file}')
    # Load the shapefile using GeoPandas
    gdf = gpd.read_file(shp_file)
    print(f'shpfile is : {shp_file}')
   
    # Extract the second string from the GeoJSON file name
    geojson_name = os.path.basename(shp_file)
    second_string = geojson_name.split('_')[1]

    # Look for a CSV file in the same subfolder
    csv_folder = os.path.dirname(shp_file)
    csv_file = None
    for file in os.listdir(csv_folder):
        if file.endswith('.csv') and second_string in file:
            csv_file = os.path.join(csv_folder, file)
            break
    
    if csv_file:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        

        # Perform an inner join on the 'order' column
        gdf = gdf.merge(df, on='order')
    
    # Filter the GeoJSON data based on the order_ids if provided
    if order_ids:
        filtered_gdf = gdf[gdf['order'].isin(order_ids)]
    else:
        filtered_gdf = gdf
        
    print(f'filtered_gdf is : {filtered_gdf.head()}')

    # Open the TIF file using Rasterio
    with rasterio.open(tif_file) as src:
        # Read the first 6 bands (excluding any additional bands)
        bands = src.read([1, 2, 3, 4, 5, 6])

        # Define the column names based on the number of bands and statistics descriptors
        stats_descriptors = ['mean', 'std', 'max', 'min']
        band_columns = [f'Band_{i}_{stat}' for i in range(1, 7) for stat in stats_descriptors]

        # Include NDVI and NDRE columns in the column names
        column_names = ['TIF_Name', 'Date', 'Date_julian', 'plotID', 'identifier','barcode', 'Accession'] + band_columns + ['NDVI_mean', 'NDVI_std', 'NDVI_max', 'NDVI_min'] + ['NDRE_mean', 'NDRE_std', 'NDRE_max', 'NDRE_min'] + ['fcover']

        # Create an empty DataFrame to store the results
        result_df = pd.DataFrame(columns=column_names)

        # Extract the second string from the TIF name as the 'Date'
        date_string = os.path.splitext(os.path.basename(tif_file))[0].split('_')[2]
        
        # Format the date as MM-DD-YYYY
        formatted_date = datetime.strptime(date_string, '%m%d%Y').strftime('%m-%d-%Y')

        # Convert the formatted date to Julian date
        julian_date = datetime.strptime(formatted_date, '%m-%d-%Y').timetuple().tm_yday

        # Iterate over each row in the filtered GeoDataFrame
        for index, row in filtered_gdf.iterrows():
            # Get the geometry of the polygon
            geom = row['geometry']

            # Get the attributes from the shapefile
            attributes = [row[field] for field in filtered_gdf.columns if field != 'geometry']

            # Extract the 'Identifier' field from the shapefile
            identifier = row['identifier']

            # Initialize lists to store band statistics for each band
            band_stats_list = [[] for _ in range(6)]
            nodata_value = 65535
            try:
                # Iterate over each band within the polygon
                for band_index in range(6):
                    masked_data, _ = mask(src, [geom], nodata=nodata_value, crop=True)

                    # Calculate statistics for the masked data
                    band_stats = [getattr(np, stat)(masked_data[band_index][masked_data[band_index] != nodata_value]) for stat in stats_descriptors]
                    band_stats_list[band_index] = band_stats

                # Calculate NDVI and NDRE from masked_data
                ndvi_values = (masked_data[4] - masked_data[2]) / (masked_data[4] + masked_data[2])
                ndre_values = (masked_data[4] - masked_data[3]) / (masked_data[4] + masked_data[3])

                # Calculate NDVI and NDRE statistics for the polygon
                ndvi_stats = [getattr(np, stat)(ndvi_values) for stat in stats_descriptors]
                ndre_stats = [getattr(np, stat)(ndre_values) for stat in stats_descriptors]

                # Calculate fcover for the polygon
                green_pixels = np.count_nonzero(ndvi_values > 0.65)
                total_pixels = np.count_nonzero(ndvi_values)
                fcover = (green_pixels / total_pixels) * 100

                # Create a row for the DataFrame
                row_data = [os.path.basename(tif_file), formatted_date, julian_date, row['order'], identifier, row['Barcode Labels'], row['Accession']] + [stat for band_stats in band_stats_list for stat in band_stats] + ndvi_stats + ndre_stats + [fcover]

            except Exception as e:
                # Handle the case when intersection is empty
                print(f"Error processing row {index}: {e}")
                row_data = [os.path.basename(tif_file), formatted_date, julian_date, row['order'], identifier, row['Barcode Labels'], row['Accession']] + [np.nan] * (len(result_df.columns) - 5)
                # Change only the NaN values to a specific numeric value (e.g., -66666)
                row_data = pd.Series(row_data).fillna(-66666).tolist()

            finally:
                # Append the row to the result DataFrame
                result_df.loc[len(result_df)] = row_data

        # Print the result DataFrame
        print(f'dataframe is : {result_df.head()}')

    return result_df

# def process_selected_polygons():
#     data = request.json
#     print(f'data passed to process_selected_polygons: {data}')
#     selected_plots = data.get('selectedPlots', [])
#     selected_accessions = data.get('selectedAccessions', [])
#     shp_file = data.get('shp_file', '')

#     print('Received selected plots list data in the backend:', selected_plots)
#     print('Received selected accessions list data in the backend:', selected_accessions)
#     print('Received shp file in the backend:', shp_file)

#     combined_results_df = pd.DataFrame()
#     combined_all_plots_df = pd.DataFrame()

#     if selected_plots:
#         # Process selected plots
#         grouped_plots = {}
#         for plot in selected_plots:
#             geojson_path = os.path.join(IMAGES_DIRECTORY, plot['geojsonPath'])
#             order_id = plot['orderID']

#             print(f'GeoJSON path for plot {order_id}: {geojson_path}')

#             # Extract the subfolder and the second string pattern from the geojsonPath
#             subfolder = os.path.dirname(geojson_path)
#             geojson_filename = os.path.basename(geojson_path)
#             second_string_pattern = geojson_filename.split('_')[1]

#             # Group by the second string pattern
#             if second_string_pattern not in grouped_plots:
#                 grouped_plots[second_string_pattern] = {'geojson_path': geojson_path, 'order_ids': [], 'tif_paths': []}
#             grouped_plots[second_string_pattern]['order_ids'].append(order_id)

#         # Look for _shifted.tif files in the subfolder that share the same second string pattern
#         for group_key, group in grouped_plots.items():
#             subfolder = os.path.dirname(group['geojson_path'])
#             for root, dirs, files in os.walk(subfolder):
#                 for file in files:
#                     if file.endswith('_shifted.tif') and group_key in file:
#                         tif_path = os.path.join(root, file)
#                         print(f'TIF path identified for group {group_key}: {tif_path}')
#                         group['tif_paths'].append(tif_path)

#         for group_key, group in grouped_plots.items():
#             print(f'Processing group: {group_key}')
#             geojson_path = group['geojson_path']
#             order_ids = group['order_ids']
#             print(f'GeoJSON path for group {group_key}: {geojson_path}')
#             print(f'Order IDs for group {group_key}: {order_ids}')
#             print(f'TIF paths for group {group_key}:')
#             for tif_path in group['tif_paths']:
#                 print(f'  {tif_path}')

#                 if os.path.exists(tif_path):
#                     # Pass the subsetted GeoJSON area and the corresponding TIFs to extract_statistics()
#                     result_df = extract_statistics(tif_path, geojson_path, order_ids)
#                     combined_results_df = pd.concat([combined_results_df, result_df], ignore_index=True)

#                     # Extract statistics for all plots
#                     all_plots_df = extract_statistics(tif_path, geojson_path)
#                     combined_all_plots_df = pd.concat([combined_all_plots_df, all_plots_df], ignore_index=True)

#     elif selected_accessions:
#         # Process selected accessions
#         grouped_accessions = {}
#         for accession in selected_accessions:
#             geojson_path = os.path.join(IMAGES_DIRECTORY, shp_file)
#             accession_id = accession

#             print(f'GeoJSON path for accession {accession_id}: {geojson_path}')

#             # Extract the subfolder and the second string pattern from the geojsonPath
#             subfolder = os.path.dirname(geojson_path)
#             geojson_filename = os.path.basename(geojson_path)
#             second_string_pattern = geojson_filename.split('_')[1]

#             # Group by the second string pattern
#             if second_string_pattern not in grouped_accessions:
#                 grouped_accessions[second_string_pattern] = {'geojson_path': geojson_path, 'accession_ids': [], 'tif_paths': []}
#             grouped_accessions[second_string_pattern]['accession_ids'].append(accession_id)

#         # Look for _shifted.tif files in the subfolder that share the same second string pattern
#         for group_key, group in grouped_accessions.items():
#             subfolder = os.path.dirname(group['geojson_path'])
#             for root, dirs, files in os.walk(subfolder):
#                 for file in files:
#                     if file.endswith('_shifted.tif') and group_key in file:
#                         tif_path = os.path.join(root, file)
#                         print(f'TIF path identified for group {group_key}: {tif_path}')
#                         group['tif_paths'].append(tif_path)

#         for group_key, group in grouped_accessions.items():
#             print(f'Processing group: {group_key}')
#             geojson_path = group['geojson_path']
#             accession_ids = group['accession_ids']
#             print(f'GeoJSON path for group {group_key}: {geojson_path}')
#             print(f'Accession IDs for group {group_key}: {accession_ids}')
#             print(f'TIF paths for group {group_key}:')
#             for tif_path in group['tif_paths']:
#                 print(f'  {tif_path}')

#                 if os.path.exists(tif_path):
#                     # Extract statistics for all plots
#                     all_plots_df = extract_statistics(tif_path, geojson_path)
#                     combined_all_plots_df = pd.concat([combined_all_plots_df, all_plots_df], ignore_index=True)
#         print(f'combined_all_plots_df column names: {combined_all_plots_df.columns}')

#         #Filter the combined results by selected accessions
#         combined_results_df = combined_all_plots_df[combined_all_plots_df['Accession'].isin(selected_accessions)]
        
#                 # if os.path.exists(tif_path):
#                 #     # Pass the subsetted GeoJSON area and the corresponding TIFs to extract_statistics()
#                 #     result_df = extract_statistics(tif_path, geojson_path, order_ids)
#                 #     combined_results_df = pd.concat([combined_results_df, result_df], ignore_index=True)

#                 #     # Extract statistics for all plots
#                 #     all_plots_df = extract_statistics(tif_path, geojson_path)
#                 #     combined_all_plots_df = pd.concat([combined_all_plots_df, all_plots_df], ignore_index=True)


#     # Print the combined result DataFrame
#     print(f'Combined dataframe for selected plots is : {combined_results_df.head(30)}')
#     print(f'Combined dataframe for all plots is : {combined_all_plots_df.head(30)}')

#     return {
#         'selected_plots': combined_results_df.to_json(orient='records'),
#         'all_plots': combined_all_plots_df.to_json(orient='records')
#     }


def process_selected_polygons():
    data = request.json
    print(f'data passed to process_selected_polygons: {data}')
    selected_plots = data.get('selectedPlots', [])
    selected_accessions = data.get('selectedAccessions', [])
    shp_file = data.get('shp_file', '')

    print('Received selected plots list data in the backend:', selected_plots)
    print('Received selected accessions list data in the backend:', selected_accessions)
    print('Received shp file in the backend:', shp_file)

    combined_results_df = pd.DataFrame()
    combined_all_plots_df = pd.DataFrame()
    filepath = os.path.join(IMAGES_DIRECTORY, shp_file)
    gdf = gpd.read_file(filepath)
    gdf = gdf.to_crs("EPSG:4326")
    
    # Extract the second string from the GeoJSON file name
    geojson_name = os.path.basename(filepath)
    second_string = geojson_name.split('_')[1]

    # Look for a CSV file in the same subfolder
    csv_folder = os.path.dirname(filepath)
    csv_file = None
    for file in os.listdir(csv_folder):
        if file.endswith('.csv') and second_string in file:
            csv_file = os.path.join(csv_folder, file)
            break

    if csv_file:
        # Read the CSV file
        df = pd.read_csv(csv_file)

        # Perform an inner join on the 'order' column
        gdf = gdf.merge(df, on='order')
    
    
    

    if selected_plots:
        # Process selected plots
        grouped_plots = {}
        for plot in selected_plots:
            geojson_path = os.path.join(IMAGES_DIRECTORY, plot['geojsonPath'])
            order_id = plot['orderID']

            print(f'GeoJSON path for plot {order_id}: {geojson_path}')

            # Extract the subfolder and the second string pattern from the geojsonPath
            subfolder = os.path.dirname(geojson_path)
            geojson_filename = os.path.basename(geojson_path)
            second_string_pattern = geojson_filename.split('_')[1]

            # Group by the second string pattern
            if second_string_pattern not in grouped_plots:
                grouped_plots[second_string_pattern] = {'geojson_path': geojson_path, 'order_ids': [], 'tif_paths': []}
            grouped_plots[second_string_pattern]['order_ids'].append(order_id)

        # Look for _shifted.tif files in the subfolder that share the same second string pattern
        for group_key, group in grouped_plots.items():
            subfolder = os.path.dirname(group['geojson_path'])
            for root, dirs, files in os.walk(subfolder):
                for file in files:
                    if file.endswith('_shifted.tif') and group_key in file:
                        tif_path = os.path.join(root, file)
                        print(f'TIF path identified for group {group_key}: {tif_path}')
                        group['tif_paths'].append(tif_path)

        for group_key, group in grouped_plots.items():
            print(f'Processing group: {group_key}')
            geojson_path = group['geojson_path']
            order_ids = group['order_ids']
            print(f'GeoJSON path for group {group_key}: {geojson_path}')
            print(f'Order IDs for group {group_key}: {order_ids}')
            print(f'TIF paths for group {group_key}:')
            for tif_path in group['tif_paths']:
                print(f'  {tif_path}')

                if os.path.exists(tif_path):
                    # Pass the subsetted GeoJSON area and the corresponding TIFs to extract_statistics()
                    result_df = extract_statistics(tif_path, geojson_path, order_ids)
                    combined_results_df = pd.concat([combined_results_df, result_df], ignore_index=True)

                    # Extract statistics for all plots
                    all_plots_df = extract_statistics(tif_path, geojson_path)
                    combined_all_plots_df = pd.concat([combined_all_plots_df, all_plots_df], ignore_index=True)

    elif selected_accessions:
        # Process selected accessions
        grouped_accessions = {}
        for accession in selected_accessions:
            geojson_path = os.path.join(IMAGES_DIRECTORY, shp_file)
            accession_id = accession

            print(f'GeoJSON path for accession {accession_id}: {geojson_path}')

            # Extract the subfolder and the second string pattern from the geojsonPath
            subfolder = os.path.dirname(geojson_path)
            geojson_filename = os.path.basename(geojson_path)
            second_string_pattern = geojson_filename.split('_')[1]

            # Group by the second string pattern
            if second_string_pattern not in grouped_accessions:
                grouped_accessions[second_string_pattern] = {'geojson_path': geojson_path, 'accession_ids': [], 'tif_paths': []}
            grouped_accessions[second_string_pattern]['accession_ids'].append(accession_id)

        # Look for _shifted.tif files in the subfolder that share the same second string pattern
        for group_key, group in grouped_accessions.items():
            subfolder = os.path.dirname(group['geojson_path'])
            for root, dirs, files in os.walk(subfolder):
                for file in files:
                    if file.endswith('_shifted.tif') and group_key in file:
                        tif_path = os.path.join(root, file)
                        print(f'TIF path identified for group {group_key}: {tif_path}')
                        group['tif_paths'].append(tif_path)

        for group_key, group in grouped_accessions.items():
            print(f'Processing group: {group_key}')
            geojson_path = group['geojson_path']
            accession_ids = group['accession_ids']
            print(f'GeoJSON path for group {group_key}: {geojson_path}')
            print(f'Accession IDs for group {group_key}: {accession_ids}')
            print(f'TIF paths for group {group_key}:')
            for tif_path in group['tif_paths']:
                print(f'  {tif_path}')

                if os.path.exists(tif_path):
                    # Extract statistics for all plots
                    all_plots_df = extract_statistics(tif_path, geojson_path)
                    combined_all_plots_df = pd.concat([combined_all_plots_df, all_plots_df], ignore_index=True)
        print(f'combined_all_plots_df column names: {combined_all_plots_df.columns}')

        #Filter the combined results by selected accessions
        combined_results_df = combined_all_plots_df[combined_all_plots_df['Accession'].isin(selected_accessions)]
        
                # if os.path.exists(tif_path):
                #     # Pass the subsetted GeoJSON area and the corresponding TIFs to extract_statistics()
                #     result_df = extract_statistics(tif_path, geojson_path, order_ids)
                #     combined_results_df = pd.concat([combined_results_df, result_df], ignore_index=True)

                #     # Extract statistics for all plots
                #     all_plots_df = extract_statistics(tif_path, geojson_path)
                #     combined_all_plots_df = pd.concat([combined_all_plots_df, all_plots_df], ignore_index=True)

    # Mark the selected plots in the GeoDataFrame
    gdf['selected'] = gdf['order'].isin(combined_results_df['plotID'])
    
    # Print the combined result DataFrame
    print(f'Combined dataframe for selected plots is : {combined_results_df.head(30)}')
    print(f'Combined dataframe for all plots is : {combined_all_plots_df.head(30)}')

    response = {
        'selected_plots': combined_results_df.to_json(orient='records'),
        'all_plots': combined_all_plots_df.to_json(orient='records'),
        'filtered_geojson': gdf.to_json()
    }
    return jsonify(response)


def natural_sort_key(s):
    """Sort function that handles alphanumeric strings."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def get_accessions(shp_file):
    # Load the shapefile using GeoPandas
    shp_path = os.path.join(IMAGES_DIRECTORY, shp_file)
    gdf = gpd.read_file(shp_path)
    print(f'shpfile is : {shp_path}')
   
    # Extract the second string from the GeoJSON file name
    geojson_name = os.path.basename(shp_path)
    second_string = geojson_name.split('_')[1]

    # Look for a CSV file in the same subfolder
    csv_folder = os.path.dirname(shp_path)
    csv_file = None
    for file in os.listdir(csv_folder):
        if file.endswith('.csv') and second_string in file:
            csv_file = os.path.join(csv_folder, file)
            break

    accessions = []
    if csv_file:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        accessions = sorted(df['Accession'].unique().tolist(), key=natural_sort_key)  # Sort the accessions list

        # Perform an inner join on the 'order' column
        gdf = gdf.merge(df, on='order')
        
    return accessions
