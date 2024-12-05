

import os
import logging
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import from_bounds
from pyproj import Transformer
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
from PIL import Image
import tempfile

# Configure logging
#logging.basicConfig(level=logging.DEBUG)

logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

def find_all_pairs(input_folder):
    logging.debug(f"Searching for pairs in folder: {input_folder}")
    try:
        subfolders = [f.path for f in os.scandir(input_folder) if f.is_dir()]
        logging.debug(f"Found subfolders: {subfolders}")
        all_pairs = []

        for subfolder in subfolders:
            files = [f for f in os.listdir(subfolder) if f.endswith('.tif')]
            logging.debug(f"Found files in subfolder {subfolder}: {files}")
            grouped_files = {}

            for file in files:
                parts = file.split('_')
                if len(parts) < 3:
                    logging.debug(f"Skipping file {file} due to insufficient parts")
                    continue
                key = f"{parts[0]}_{parts[1]}"
                if key not in grouped_files:
                    grouped_files[key] = {}
                if 'ortho' in parts[2].lower():
                    grouped_files[key]['ortho'] = os.path.join(subfolder, file)
                elif 'dtm' in parts[2].lower():
                    grouped_files[key]['dtm'] = os.path.join(subfolder, file)

            for key, pair in grouped_files.items():
                if 'ortho' in pair and 'dtm' in pair:
                    logging.debug(f"Found pair: {pair['ortho']} and {pair['dtm']} in {subfolder}")
                    all_pairs.append((pair['ortho'], pair['dtm'], subfolder))

        if not all_pairs:
            logging.debug("No valid pairs found")
            return None
        return all_pairs
    except Exception as e:
        logging.error(f"Error finding pairs: {e}")
        return None



def process_all_pairs(input_folder, clip_min=0, clip_max=4000):
    logging.debug(f"Processing all pairs in folder: {input_folder}")
    pairs = find_all_pairs(input_folder)
    if not pairs:
        logging.error("No valid pairs found")
        return {"error": "No valid pairs found"}

    results = []
    for ortho_path, dtm_path, subfolder in pairs:
        try:
            # Process ortho image
            with rasterio.open(ortho_path) as src:
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

                    reprojected_tif_path = os.path.join(tempfile.gettempdir(), 'reprojected_' + os.path.basename(ortho_path))
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
                    original_ortho_path = ortho_path
                    ortho_path = reprojected_tif_path
                    logging.debug("TIFF file reprojected to EPSG:4326")

                # Extract bounds for correct overlay
                with rasterio.open(ortho_path) as reprojected_src:
                    bounds = reprojected_src.bounds  # Ensure we use reprojected bounds
                    logging.debug(f"Reprojected TIFF bounds: {bounds}")

                    # Read bands 1, 2, 3 and normalize
                    data = reprojected_src.read([3, 2, 1])

                    # Normalize the data to the range 0-255 using dynamic clip_min and clip_max
                    data = normalize_data(data, clip_min, clip_max)

                    logging.debug("Normalized bands to 0-255 with clipping and scaling")

                    # Create an RGB image with an alpha channel
                    alpha = np.all(data == 0, axis=0).astype(np.uint8) * 255
                    img = np.dstack((data[0], data[1], data[2], 255 - alpha))
                    img = Image.fromarray(img, 'RGBA')
                    png_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(os.path.basename(ortho_path))[0]}.png")
                    img.save(png_path)
                    logging.debug(f"Saved PNG image: {png_path}")

            results.append({
                "png_path": f"/temp/{os.path.basename(png_path)}",
                "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
                "ortho_path": ortho_path,
                "dtm_path": dtm_path,
                "original_ortho_path": original_ortho_path
            })
        except Exception as e:
            logging.error(f"Error processing pair {ortho_path} and {dtm_path}: {e}")
            results.append({"error": str(e)})

    return results


def transform_coords(coords):
    transformer = Transformer.from_crs("epsg:4326", "epsg:32616", always_xy=True)
    transformed_coords = [transformer.transform(lon, lat) for lat, lon in coords]
    return transformed_coords

def normalize_data(data, clip_min, clip_max):
    """
    Normalize the data to the range 0-255.

    Parameters:
    - data: The input data to be normalized.
    - clip_min: The minimum value for clipping.
    - clip_max: The maximum value for clipping.

    Returns:
    - Normalized data in the range 0-255.
    """
    data = np.clip(data, clip_min, clip_max)  # Clip values to the specified range
    data = (data - clip_min) / (clip_max - clip_min) * 255  # Scale to 0-255
    data = data.astype(np.uint8)
    return data

def process_to_stack(ortho_path, dtm_path, coords, corners, output_folder, original_ortho_path):
    logging.debug(f"Interpolating coordinates for ortho_path: {ortho_path}, dtm_path: {dtm_path}")
    try:
        transformed_coords = transform_coords(coords)
        transformed_corners = transform_coords(corners)
        logging.debug(f"Transformed coordinates: {transformed_coords}")
        logging.debug(f"Transformed corners: {transformed_corners}")

        with rasterio.open(dtm_path) as src:
            dtm_data = src.read(1)
            dtm_transform = src.transform
            src_crs = src.crs
            src_bounds = src.bounds
            src_height, src_width = src.height, src.width

            points = [(x, y, dtm_data[src.index(x, y)]) for x, y in transformed_coords]
            x, y, values = zip(*points)  # Extract coordinates and values

            # Define a coarser spatial resolution (e.g., 1 meter)
            resolution = 0.2  # in meters

            # Calculate the number of rows and columns based on the coarser resolution
            rows = int(src_height * src.res[0] / resolution)
            cols = int(src_width * src.res[1] / resolution)

            # Create a grid with the coarser spatial resolution
            xi, yi = np.meshgrid(np.linspace(src_bounds.left, src_bounds.right, cols),
                                 np.linspace(src_bounds.top, src_bounds.bottom, rows))
            logging.debug("kNN interpolation being carried out")

            # Fit a k-NN regressor
            knn = KNeighborsRegressor(n_neighbors=12)  # Adjust n_neighbors as needed
            knn.fit(list(zip(x, y)), values)

            # Predict values at grid locations
            zi = knn.predict(np.c_[xi.ravel(), yi.ravel()])
            zi = zi.reshape(xi.shape)

            # Save the interpolated raster to the specified output directory with '_baresoil.tif' appended
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ortho_basename = os.path.splitext(os.path.basename(ortho_path))[0]
            dtm_basename = os.path.splitext(os.path.basename(dtm_path))[0]
            new_stem = f"{dtm_basename}_baresoil"
            interpolated_path = os.path.join(output_folder, f"{new_stem}.tif")

            new_transform = from_bounds(src_bounds.left, src_bounds.bottom, src_bounds.right, src_bounds.top, zi.shape[1], zi.shape[0])
            with rasterio.open(interpolated_path, 'w', driver='GTiff', height=zi.shape[0], width=zi.shape[1], count=1, dtype=zi.dtype, crs=src_crs, transform=new_transform) as dst:
                dst.write(zi, 1)
            logging.debug(f"Saved interpolated raster: {interpolated_path}")

            # Mask and resample the ortho, DTM, and baresoil rasters
            def mask_and_resample(input_path, output_path, reference_file, selected_corners):
                logging.debug(f"Masking and resampling {input_path}")
                with rasterio.open(reference_file) as reference:
                    resample_transform = reference.transform
                    reference_width = reference.width
                    reference_height = reference.height

                with rasterio.open(input_path) as src:
                    if src.count > 1:
                        with rasterio.open(reference_file) as reference:
                            
                            transform = reference.transform
                            
                            lon, lat = zip(*selected_corners)  # Unzip the transformed corners
                            
                            print(lon)
                            print(lat)
                            masked = gpd.GeoDataFrame({'geometry': [Point(lon, lat) for lon, lat in zip(lon, lat)]}, crs=src.crs)
                            print(f'mask coordinates for multiband tif are: {masked}')
                            mask_bounds = masked.total_bounds
                            print(f'mask bounds: {mask_bounds}')  

                            # Ensure mask bounds intersect with dataset bounds
                            dataset_bounds = src.bounds
                            print(f'dataset bounds: {dataset_bounds}')  # Debug statement to print dataset bounds
                            if not (mask_bounds[0] < dataset_bounds.right and mask_bounds[2] > dataset_bounds.left and
                                    mask_bounds[1] < dataset_bounds.top and mask_bounds[3] > dataset_bounds.bottom):
                                raise ValueError("Mask bounds do not intersect with dataset bounds")

                            mask_window = src.window(*mask_bounds)
                            print(f'mask window: {mask_window}')  # Debug statement to print mask window

                            # Ensure the window is valid
                            if mask_window.width <= 0 or mask_window.height <= 0:
                                raise ValueError("Invalid window dimensions")

                            input_data = src.read(window=mask_window)

                            resampled_data = np.zeros(
                                (src.count, reference_height, reference_width),
                                dtype=np.float32
                            )
                            for band in range(src.count):
                                reproject(
                                    input_data[band].astype(np.float32),
                                    resampled_data[band],
                                    src_transform=src.window_transform(mask_window),
                                    src_crs=src.crs,
                                    dst_transform=resample_transform,
                                    dst_crs=src.crs,
                                    resampling=Resampling.bilinear
                                )
                    else:
                        with rasterio.open(reference_file) as reference:
                        
                            transform = reference.transform
                            
                            lon, lat = zip(*selected_corners)  # Unzip the transformed corners
                        
                            masked = gpd.GeoDataFrame({'geometry': [Point(lon, lat) for lon, lat in zip(lon, lat)]}, crs=src.crs)
                            #print(f'mask coordinates for multiband tif are: {masked}')
                            mask_bounds = masked.total_bounds
                            
                            # Ensure mask bounds intersect with dataset bounds
                            dataset_bounds = src.bounds
                            print(f'dataset bounds: {dataset_bounds}')  # Debug statement to print dataset bounds
                            if not (mask_bounds[0] < dataset_bounds.right and mask_bounds[2] > dataset_bounds.left and
                                    mask_bounds[1] < dataset_bounds.top and mask_bounds[3] > dataset_bounds.bottom):
                                raise ValueError("Mask bounds do not intersect with dataset bounds")

                            mask_window = src.window(*mask_bounds)
                            print(f'mask window: {mask_window}')  # Debug statement to print mask window
                            
                    
                            input_data = src.read(1, window=mask_window)

                            resampled_data = np.zeros(
                                (1, reference_height, reference_width),
                                dtype=np.float32
                            )
                            reproject(
                                input_data.astype(np.float32),
                                resampled_data[0],
                                src_transform=src.window_transform(mask_window),
                                src_crs=src.crs,
                                dst_transform=resample_transform,
                                dst_crs=src.crs,
                                resampling=Resampling.bilinear
                            )

                num_output_bands = src.count
                with rasterio.open(output_path, 'w', driver='GTiff',
                                   width=reference_width,
                                   height=reference_height,
                                   count=num_output_bands,
                                   dtype=resampled_data.dtype,
                                   crs=src.crs, transform=resample_transform) as dst:
                    if src.count == 1:
                        dst.write(resampled_data[0], 1)
                    else:
                        for band in range(num_output_bands):
                            dst.write(resampled_data[band], band + 1)
                logging.debug(f"Saved masked and resampled raster: {output_path}")

            ortho_resampled_path = os.path.join(output_folder, f"{ortho_basename}_ortho_resampled.tif")
            dtm_resampled_path = os.path.join(output_folder, f"{dtm_basename}_dtm_resampled.tif")
            baresoil_resampled_path = os.path.join(output_folder, f"{new_stem}_baresoil_resampled.tif")

            mask_and_resample(original_ortho_path, ortho_resampled_path, original_ortho_path, transformed_corners)
            mask_and_resample(dtm_path, dtm_resampled_path, original_ortho_path, transformed_corners)
            mask_and_resample(interpolated_path, baresoil_resampled_path, original_ortho_path, transformed_corners)

            # Subtract DTM and baresoil to generate abscsm.tif
            logging.debug("Subtracting DTM and baresoil to generate abscsm.tif")
            with rasterio.open(dtm_resampled_path) as dtm_resampled, rasterio.open(baresoil_resampled_path) as baresoil_resampled:
                dtm_resampled_data = dtm_resampled.read(1)
                baresoil_resampled_data = baresoil_resampled.read(1)
                abscsm_data = dtm_resampled_data - baresoil_resampled_data

                abscsm_path = os.path.join(output_folder, f"{dtm_basename}_abscsm.tif")
                with rasterio.open(abscsm_path, 'w', driver='GTiff', height=dtm_resampled.height, width=dtm_resampled.width, count=1, dtype=abscsm_data.dtype, crs=dtm_resampled.crs, transform=dtm_resampled.transform) as dst:
                    dst.write(abscsm_data, 1)
                logging.debug(f"Saved abscsm raster: {abscsm_path}")

            # Read ortho data for stacking
            logging.debug("Reading ortho data for stacking")
            with rasterio.open(ortho_resampled_path) as ortho_src:
                ortho_data = ortho_src.read()

            # Stack the resampled ortho and abscsm and save as _stack.tif
            logging.debug("Stacking resampled ortho and abscsm")
            stack_path = os.path.join(output_folder, f"{ortho_basename}_stack.tif")
            with rasterio.open(stack_path, 'w', driver='GTiff', height=ortho_src.height, width=ortho_src.width, count=ortho_data.shape[0] + 1, dtype=ortho_data.dtype, crs=ortho_src.crs, transform=ortho_src.transform) as dst:
                for i in range(ortho_data.shape[0]):
                    dst.write(ortho_data[i], i + 1)
                dst.write(abscsm_data, ortho_data.shape[0] + 1)
            logging.debug(f"Saved stacked raster: {stack_path}")

            # Delete intermediate files
            logging.debug("Deleting intermediate files")
            os.remove(interpolated_path)
            os.remove(dtm_resampled_path)
            os.remove(ortho_resampled_path)
            os.remove(baresoil_resampled_path)
            os.remove(abscsm_path)

            logging.debug(f"Saved stacked raster: {stack_path}")

        return {"interpolated_path": stack_path}
    except Exception as e:
        logging.error(f"Error interpolating coordinates: {e}")
        return {"error": str(e)}