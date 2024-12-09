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

logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

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
    

def calculate_geometry(width, length, horizontal_gap, vertical_gap, num_polygons, num_horizontal_polygons, x1, y1, x2, y2, tiff_crs, reverse_row_order, num_blocks=None, alley_width=None, multiblock=False):
    # Calculate the number of rows and columns based on user input
    
    # Print the reverse_row_order value for debugging
    print(f"reverse_row_order: {reverse_row_order}")
    num_vertical_polygons = math.ceil(num_polygons / num_horizontal_polygons)

    # Calculate the angle between the original line (x1, y1) - (x2, y2) and the horizontal axis
    angle_radians = math.atan2(y2 - y1, x2 - x1)

    # Create an empty list to store polygons
    polygons = []

    for col in range(num_horizontal_polygons):
        for row in range(num_vertical_polygons):
            if col % 2 == 0:  # Even columns (0-based index)
                # Even columns go from south to north
                x_offset = col * (width + horizontal_gap)
            else:  # Odd columns
                # Odd columns go from north to south
                x_offset = col * (width + horizontal_gap)
                if reverse_row_order:
                    row = num_vertical_polygons - row - 1  # Reverse the row order for odd columns

            y_offset = row * (length + vertical_gap)

            # Calculate the coordinates based on the orientation angle, offsets, and gaps
            lon1 = x1 + x_offset
            lat1 = y1 + y_offset
            lon2 = lon1 + width
            lat2 = lat1
            lon3 = lon2
            lat3 = lat2 + length
            lon4 = lon1
            lat4 = lat3

            # Create a rectangle based on the coordinates
            rectangle = Polygon([(lon1, lat1), (lon2, lat2), (lon3, lat3), (lon4, lat4)])

            polygons.append(rectangle)

    # Create a GeoDataFrame from the list of individual polygons
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=tiff_crs)

    # Calculate the rotation angle needed to align with the line between points 1 and 2
    tilt_angle = math.degrees(angle_radians) - 90.0

    # Rotate the entire GeoDataFrame to align with the line between points 1 and 2
    gdf['geometry'] = gdf['geometry'].rotate(tilt_angle, origin=(x1, y1))

    # Add 'order' and 'identifier' columns
    gdf['order'] = range(1, 1 + num_polygons)
    gdf['identifier'] = range(101, 101 + num_polygons)
    
    return gdf

def calculate_horizontal_geometry(width, length, horizontal_gap, vertical_gap, num_polygons, num_horizontal_polygons, x1, y1, x2, y2, tiff_crs, reverse_row_order, num_blocks=None, alley_width=None, multiblock=False):
    # Calculate the number of rows and columns based on user input
        num_vertical_polygons = math.ceil(num_polygons / num_horizontal_polygons)

        # Calculate the angle between the original line (x1, y1) - (x2, y2) and the horizontal axis
        angle_radians = math.atan2(y2 - y1, x2 - x1)

        # Calculate the new initial corner coordinates to align the left edge with the line
        new_x1 = x1 + (width/2)
        new_y1 = y1 #+ (width / 2)
        
        # Calculate the angle for tilting the MultiPolygon to align with the line
        tilt_angle = math.degrees(math.atan2(y2 - new_y1, x2 - new_x1))

        # Create an empty list to store polygons
        polygons = []

        for row in range(num_vertical_polygons):
            for col in range(num_horizontal_polygons):
                x_offset = col * (width + horizontal_gap)
                y_offset = row * (length + vertical_gap)
                
                # Calculate the coordinates skipping orientation angle spec, but offsets, and gaps
                lon1 = new_x1 + x_offset
                lat1 = new_y1 + y_offset
                lon2 = lon1 + width
                lat2 = lat1 
                lon3 = lon2 
                lat3 = lat2 + length
                lon4 = lon1  
                lat4 = lat3 
                
                # Create a rectangle based on the coordinates
                rectangle = Polygon([(lon1, lat1), (lon2, lat2), (lon3, lat3), (lon4, lat4)])

                polygons.append(rectangle)

        # Create a GeoDataFrame from the list of individual polygons
        gdf = gpd.GeoDataFrame(geometry=polygons, crs=tiff_crs)
    
        # Calculate the rotation angle needed to align with the line between points 1 and 2
        #rotation_angle = math.degrees(angle_radians)
        # Calculate the tilt angle based on the difference between the original line angle and the horizontal axis
        tilt_angle = math.degrees(angle_radians) - 90.0

        # Rotate the entire GeoDataFrame to align with the line between points 1 and 2
        gdf['geometry'] = gdf['geometry'].rotate(tilt_angle, origin=(x1, y1))

        # Add 'order' and 'identifier' columns
        gdf['order'] = range(1, num_polygons + 1)
        #gdf['order'] = range(1351, 1351 + num_polygons )
        gdf['identifier'] = range(101, 101 + num_polygons)
        #gdf['identifier'] = range(1451, 1451 + num_polygons)

        return gdf
    


def calculate_multiblock_geometry(width, length, horizontal_gap, num_polygons, vertical_gap, num_horizontal_polygons,
                                  x1, y1, x2, y2, tiff_crs, reverse_row_order, num_blocks=None, alley_width=None):
    # Calculate the number of rows and columns based on user input
    num_vertical_polygons = math.ceil(num_polygons / num_horizontal_polygons)

    # Create an empty list to store GeoDataFrames for each block
    gdf_list = []
    order_offset = 0  # Initial order offset for the entire multiblock geometry
    order = 1  # Initial order value for the entire multiblock geometry
    cumulative_block_x_offset = 0
    cumulative_block_y_offset = 0

    for block in range(num_blocks):
        # Calculate the total length of the previous blocks
        total_previous_length = block * (num_vertical_polygons * (length + vertical_gap) + alley_width)

        # Calculate the offsets for the current block
        if block == 0:
            block_x_offset = 0
            block_y_offset = 0
        else:
            block_x_offset = cumulative_block_x_offset
            block_y_offset = total_previous_length  # Use total_previous_length directly

        # Create an empty list to store polygons for the current block
        block_polygons = []

        for col in range(num_horizontal_polygons):
            for row in range(num_vertical_polygons):
                if col % 2 == 0:  # Even columns (0-based index)
                    # Even columns go from south to north
                    x_offset = col * (width + horizontal_gap)
                else:  # Odd columns
                    # Odd columns go from north to south
                    x_offset = col * (width + horizontal_gap)
                    if reverse_row_order:
                        row = num_vertical_polygons - row - 1  # Reverse the row order for odd columns

                y_offset = row * (length + vertical_gap)

                # Calculate the coordinates based on the orientation angle, offsets, and gaps
                lon1 = x1 + x_offset + block_x_offset
                lat1 = y1 + y_offset + block_y_offset
                lon2 = lon1 + width
                lat2 = lat1
                lon3 = lon2
                lat3 = lat2 + length
                lon4 = lon1
                lat4 = lat3

                # Create a rectangle based on the coordinates
                rectangle = Polygon([(lon1, lat1), (lon2, lat2), (lon3, lat3), (lon4, lat4)])

                block_polygons.append(rectangle)
                order += 1

        # Create a GeoDataFrame for the current block
        block_gdf = gpd.GeoDataFrame(geometry=block_polygons, crs=tiff_crs)

        # Calculate the rotation angle needed to align with the line between points 1 and 2
        tilt_angle = math.degrees(math.atan2(y2 - y1, x2 - x1)) - 90.0

        # Rotate the entire GeoDataFrame to align with the line between points 1 and 2
        block_gdf['geometry'] = block_gdf['geometry'].rotate(tilt_angle, origin=(x1, y1))

        # Translate the entire GeoDataFrame to adjust the position based on the block offset
        # block_gdf['geometry'] = block_gdf['geometry'].translate(0, 0)

        # Add 'order' and 'identifier' columns with adjusted values
        block_gdf['order'] = range(order_offset + 1, order_offset + 1 + len(block_polygons))
        block_gdf['identifier'] = range(order_offset + 101, order_offset + 101 + len(block_polygons))

        # Append the GeoDataFrame for the current block to the list
        gdf_list.append(block_gdf)

        # Update the cumulative block offsets for the next block
       
        cumulative_block_x_offset = 0 #+ alley_width

        # Update the cumulative block offset for the next block (except for the first block)
        if block > 0:
            cumulative_block_y_offset += num_vertical_polygons * (length + vertical_gap) + alley_width

        # Update the 'order' value for the next block
        order += len(block_polygons)

        # Update the 'order_offset' value for the next block
        order_offset += len(block_polygons)

    # Concatenate all GeoDataFrames for individual blocks into a single GeoDataFrame
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs=tiff_crs)

    return merged_gdf

def save_field_trial():
    data = request.get_json()
    
    # Print the received data for debugging
    print(f"Received data: {data}")

    # Extract the field trial data from the request
    plot_width = float(data['plot_width'])
    plot_length = float(data['plot_length'])
    plots_horizontal_gap = float(data['plots_horizontal_gap'])
    plots_vertical_gap = float(data['plots_vertical_gap'])
    num_polygons = int(data['num_polygons'])
    num_horizontal_polygons = int(data['num_horizontal_polygons'])
    plot_direction = data['plot_direction']
    num_blocks = int(data['num_blocks']) if data['num_blocks'] else None
    alley_width = float(data['alley_width']) if data['alley_width'] else None
    initial_corner = [float(coord) for coord in data['initial_corner'].split(',')]
    direction_point = [float(coord) for coord in data['direction_point'].split(',')]
    tiff_crs = 'EPSG:32616'  # Assuming the CRS is EPSG:32616
    reverse_row_order = data.get('reverse_plot_direction', False)
    multiblock_trial_design = data.get('multiblock_trial_design', False)# Extract reverse_plot_direction from data, default to False
    print(f'reverse_row_order: {reverse_row_order}')
    print(f'multiblock_trial_design: {multiblock_trial_design}')

    # Convert coordinates to EPSG:32616
    transformer = Transformer.from_crs("epsg:4326", "epsg:32616", always_xy=True)
    x1, y1 = transformer.transform(initial_corner[1], initial_corner[0])
    x2, y2 = transformer.transform(direction_point[1], direction_point[0])
    
    if multiblock_trial_design: 
        # Calculate the geometry based on plot direction
        if plot_direction == 'horizontal':
            gdf = calculate_horizontal_geometry(
                plot_width, plot_length, plots_horizontal_gap, plots_vertical_gap,
                num_polygons, num_horizontal_polygons, x1, y1, x2, y2, tiff_crs, reverse_row_order,
                num_blocks, alley_width
            )
        else: 
            
            gdf = calculate_multiblock_geometry(
                plot_width, plot_length, plots_horizontal_gap, num_polygons, plots_vertical_gap, num_horizontal_polygons,
                x1, y1, x2, y2, tiff_crs, reverse_row_order, num_blocks, alley_width
            )
    else: 
        if plot_direction == 'horizontal':
            gdf = calculate_horizontal_geometry(
                plot_width, plot_length, plots_horizontal_gap, plots_vertical_gap,
                num_polygons, num_horizontal_polygons, x1, y1, x2, y2, tiff_crs, reverse_row_order,
                num_blocks, alley_width
            )
        
        else:
            gdf = calculate_geometry(
                plot_width, plot_length, plots_horizontal_gap, plots_vertical_gap,
                num_polygons, num_horizontal_polygons, x1, y1, x2, y2, tiff_crs, reverse_row_order,
                num_blocks, alley_width
            )

    # Print the GeoDataFrame to the terminal
    print(gdf)
    
    # Convert the GeoDataFrame to EPSG:4326 for frontend visualization
    gdf = gdf.to_crs("EPSG:4326")

    # Convert the GeoDataFrame to GeoJSON
    geojson = gdf.to_json()

    # Log a message indicating that the GeoDataFrame has been created successfully
    logging.info("GeoDataFrame has been created successfully.")

    return jsonify({"message": "Field trial data received and printed to terminal.", "geojson": geojson})



def save_edited_object():
    try:
        data = request.get_json()
        print('Received data:', data)
        
        ortho = data['ortho']
        original_ortho_path = data['original_ortho_path']
        edited_object = data['object']

        # Check if original_ortho_path is None
        if original_ortho_path is None:
            raise ValueError("original_ortho_path is None")

        # Convert the edited object to a GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(edited_object['features'])

        # Ensure the GeoDataFrame has a CRS set
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)

        # Reproject the GeoDataFrame to EPSG:32616
        gdf = gdf.to_crs("EPSG:32616")

        # Extract the base name from original_ortho_path (excluding the .tif end)
        base_name = os.path.splitext(original_ortho_path)[0]

        # Save the GeoDataFrame as GeoJSON
        geojson_path = f"{base_name}.geojson"
        gdf.to_file(geojson_path, driver='GeoJSON')

        # Save the GeoDataFrame as Shapefile
        shp_path = f"{base_name}.shp"
        gdf.to_file(shp_path, driver='ESRI Shapefile')

        return jsonify({"message": "Edited object saved successfully.", "geojson_path": geojson_path, "shp_path": shp_path})

    except Exception as e:
        print('Error:', str(e))
        return jsonify({"error": str(e)}), 500
    



def save_gdf():
    try:
        gdf_data = request.get_json()
        file_path = os.path.join('localinput', 'edited_gdf.geojson')
        with open(file_path, 'w') as f:
            json.dump(gdf_data, f)
        return jsonify({'message': 'GDF saved successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500