

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


logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

def normalize_data(data, clip_min, clip_max):
    data = np.clip(data, clip_min, clip_max)
    data = ((data - clip_min) / (clip_max - clip_min) * 255).astype(np.uint8)
    return data

def process_files(input_folder):
    results = {"reference": [], "target": []}
    grouped_files = defaultdict(list)

    # Walk through the directory and find _stack.tif files
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('_stack.tif'):
                parts = file.split('_')
                if len(parts) >= 4:
                    group_name = parts[1]
                    date_str = parts[2]
                    try:
                        date = datetime.strptime(date_str, '%m%d%Y')
                        grouped_files[group_name].append((date, os.path.join(root, file)))
                    except ValueError:
                        logging.error(f"Invalid date format in file: {file}")

    # Process each group
    for group_name, files in grouped_files.items():
        files.sort()  # Sort by date
        reference_file = files[0][1]  # The earliest date
        target_files = [f[1] for f in files[1:]]  # The rest are targets

        # Process reference file
        reference_result = process_tif(reference_file)
        if reference_result:
            results["reference"].append(reference_result)

        # Process target files
        for target_file in target_files:
            target_result = process_tif(target_file)
            if target_result:
                results["target"].append(target_result)

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

def convert_to_epsg32616(marks):
    # Convert lat/lon to EPSG:32616 using Transformer
    transformer = Transformer.from_crs("epsg:4326", "epsg:32616", always_xy=True)
    converted_marks = [transformer.transform(mark['lng'], mark['lat']) for mark in marks]
    return converted_marks

def calculate_shift(marks_map1, marks_map2):
    print(f'calculating shift for: {marks_map1} and {marks_map2}')
    # Calculate the average shift in x and y directions
    x_shifts = [m2[0] - m1[0] for m1, m2 in zip(marks_map1, marks_map2)]
    y_shifts = [m2[1] - m1[1] for m1, m2 in zip(marks_map1, marks_map2)]
    shift_x = np.mean(x_shifts)
    shift_y = np.mean(y_shifts)
    print(f"Average shift: Shift_x = {shift_x}, Shift_y = {shift_y}")
    return shift_x, shift_y


def apply_shift(reference_file, target_file, output_file, shift_x, shift_y):
    with rasterio.open(reference_file) as ref_ds, rasterio.open(target_file) as target_ds:
        # Ensure the CRS is EPSG:32616
        if ref_ds.crs.to_string() != 'EPSG:32616' or target_ds.crs.to_string() != 'EPSG:32616':
            raise ValueError("Both reference and target files must be in EPSG:32616 CRS")
        else:
            print('Both reference and target files are in EPSG:32616 CRS')

        # Extract the pixel size from the affine transformation matrix
        pixel_size_x = target_ds.transform.a
        pixel_size_y = -target_ds.transform.e  # Note: pixel size in y is negative
        print(f'pixel size x: {pixel_size_x}')
        print(f'pixel size y: {pixel_size_y}')
        # Convert shift values from meters to pixels
        shift_x_pixels = shift_x / pixel_size_x
        shift_y_pixels = shift_y / pixel_size_y

        print(f'Pixel size: ({pixel_size_x}, {pixel_size_y})')
        print(f'Shift in pixels: Shift_x = {shift_x_pixels}, Shift_y = {shift_y_pixels}')

        # Calculate the new affine transform for the output dataset with the specified shifts
        #negative to y axis because raster increases in y axis is downward
        #flip signs to ensure accurate shift direction
        output_transform = target_ds.transform * Affine.translation(-shift_x_pixels, shift_y_pixels)

        print(f'Applying shift to: {target_file} using {reference_file}')
        print(f'Shift_x: {shift_x}, Shift_y: {shift_y}')
        print(f'Original transform: {target_ds.transform}')
        print(f'New transform: {output_transform}')

        # Define the profile for the output dataset based on the target dataset
        profile = target_ds.profile

        # Update the transformation in the profile
        profile["transform"] = output_transform

        # Copy the CRS information from the reference dataset
        profile["crs"] = ref_ds.crs

        # Delete the existing output file if it exists
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except PermissionError as e:
                print(f"Error deleting file {output_file}: {e}")
                return

        # Create the output TIF file for the shifted target image
        with rasterio.open(output_file, 'w', **profile) as output_ds:
            # Loop through each band in the target dataset
            for band_idx in range(1, target_ds.count + 1):
                # Read the data from the target band
                target_band = target_ds.read(band_idx)

                # Write the data to the corresponding band in the output dataset
                output_ds.write(target_band, band_idx)

        # Verify the new transform by reopening the output file
        with rasterio.open(output_file) as shifted_ds:
            print(f'Verified new transform: {shifted_ds.transform}')
            
def duplicate_reference_file(reference_file):
    output_file = reference_file.replace('.tif', '_shifted.tif')
    if os.path.exists(output_file):
        print(f"File {output_file} already exists. Skipping duplication.")
        return
    with rasterio.open(reference_file) as src:
        profile = src.profile
        with rasterio.open(output_file, 'w', **profile) as dst:
            for band_idx in range(1, src.count + 1):
                band = src.read(band_idx)
                dst.write(band, band_idx)
    print(f"Duplicated reference file saved as: {output_file}")

def collect_marks():
    data = request.get_json()
    reference_ortho = data['referenceOrtho']
    target_ortho = data['targetOrtho']
    original_reference_ortho_path = data['originalReferenceOrthoPath']
    original_target_ortho_path = data['originalTargetOrthoPath']
    marks_map1 = data['marksMap1']
    marks_map2 = data['marksMap2']

    # Convert marks to EPSG:32616
    marks_map1_32616 = convert_to_epsg32616(marks_map1)
    marks_map2_32616 = convert_to_epsg32616(marks_map2)

    # Calculate shifts
    shift_x, shift_y = calculate_shift(marks_map1_32616, marks_map2_32616)
    
    # Duplicate the reference file with _shifted.tif suffix
    duplicate_reference_file(original_reference_ortho_path)

    # Shift and align the target TIFF
    output_file = original_target_ortho_path.replace('.tif', '_shifted.tif')
    apply_shift(original_reference_ortho_path, original_target_ortho_path, output_file, shift_x, shift_y)

    # Print statement to check if the shifted file is saved
    if os.path.exists(output_file):
        print(f"Shifted file saved successfully: {output_file}")
    else:
        print(f"Failed to save shifted file: {output_file}")

    return jsonify({"message": "Marks collected and target TIFF shifted.", "output_file": output_file})


