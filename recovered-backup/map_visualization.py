# import os
# import tempfile
# import geopandas as gpd
# import logging
# import rasterio
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# from PIL import Image
# import numpy as np

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)

# def process_files(files):
#     try:
#         geojson_data = {}
#         png_files = []
#         geotiff_files = []

#         for file in files:
#             temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
#             file.save(temp_file_path)
#             logging.debug(f"Saved file: {file.filename} to temporary directory: {tempfile.gettempdir()}")

#         for file in files:
#             if file.filename.endswith('.shp'):
#                 shp_path = os.path.join(tempfile.gettempdir(), file.filename)
#                 logging.debug(f"Shapefile path: {shp_path}")

#                 # Load and reproject to WGS84
#                 shp_data = gpd.read_file(shp_path)
#                 logging.debug("Shapefile loaded successfully")

#                 if shp_data.crs is not None and shp_data.crs.to_string() != 'EPSG:4326':
#                     logging.debug(f"Original CRS: {shp_data.crs}")
#                     shp_data = shp_data.to_crs(epsg=4326)
#                     logging.debug("Shapefile reprojected to EPSG:4326")

#                 layer_name = os.path.splitext(file.filename)[0]
#                 geojson_data[layer_name] = shp_data.__geo_interface__

#             elif file.filename.endswith('.tif'):
#                 tif_path = os.path.join(tempfile.gettempdir(), file.filename)
#                 logging.debug(f"TIFF file path: {tif_path}")

#                 with rasterio.open(tif_path) as src:
#                     if src.crs != 'EPSG:4326':
#                         logging.debug(f"Original CRS: {src.crs}")
#                         transform, width, height = calculate_default_transform(
#                             src.crs, 'EPSG:4326', src.width, src.height, *src.bounds)
#                         kwargs = src.meta.copy()
#                         kwargs.update({
#                             'crs': 'EPSG:4326',
#                             'transform': transform,
#                             'width': width,
#                             'height': height
#                         })

#                         reprojected_tif_path = os.path.join(tempfile.gettempdir(), 'reprojected_' + file.filename)
#                         with rasterio.open(reprojected_tif_path, 'w', **kwargs) as dst:
#                             for i in range(1, src.count + 1):
#                                 reproject(
#                                     source=rasterio.band(src, i),
#                                     destination=rasterio.band(dst, i),
#                                     src_transform=src.transform,
#                                     src_crs=src.crs,
#                                     dst_transform=transform,
#                                     dst_crs='EPSG:4326',
#                                     resampling=Resampling.nearest)
#                         tif_path = reprojected_tif_path
#                         logging.debug("TIFF file reprojected to EPSG:4326")

#                     geotiff_files.append(tif_path)

#                     # Extract bounds for correct overlay
#                     with rasterio.open(tif_path) as reprojected_src:
#                         bounds = reprojected_src.bounds  # Ensure we use reprojected bounds
#                         logging.debug(f"Reprojected TIFF bounds: {bounds}")

#                         # Read bands 2, 3, 4 and normalize
#                         data = reprojected_src.read([2, 3, 4])

#                         # Get the minimum and maximum values for each band
#                         min_val = np.percentile(data, 2, axis=(1, 2), keepdims=True)
#                         max_val = np.percentile(data, 98, axis=(1, 2), keepdims=True)

#                         # Normalize the data to the range 0-255
#                         data = (data - min_val) / (max_val - min_val) * 255
#                         data = np.clip(data, 0, 255)  # Ensure values are within 0-255
#                         data = data.astype(np.uint8)

#                         logging.debug("Normalized bands to 0-255 with contrast stretching")

#                         # Create an RGB image with an alpha channel
#                         alpha = np.all(data == 0, axis=0).astype(np.uint8) * 255
#                         img = np.dstack((data[0], data[1], data[2], 255 - alpha))
#                         img = Image.fromarray(img, 'RGBA')
#                         png_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(file.filename)[0]}.png")
#                         img.save(png_path)
#                         logging.debug(f"Saved PNG image: {png_path}")

#                         # Add path and spatial bounds to PNG metadata in the correct format for Leaflet
#                         png_files.append({
#                             "path": png_path,
#                             "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
#                         })

#         return {
#             "geojson_data": geojson_data,
#             "png_files": [{"path": f"/temp/{os.path.basename(png['path'])}", "bounds": png["bounds"]} for png in png_files],
#             "geotiff_files": [f"/temp/{os.path.basename(tif)}" for tif in geotiff_files]
#         }
#     except Exception as e:
#         logging.error(f"Error processing files: {e}")
#         return {"error": str(e)}


import os
import tempfile
import geopandas as gpd
import logging
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def process_files(files):
    try:
        geojson_data = {}
        png_files = []
        geotiff_files = []

        for file in files:
            temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
            file.save(temp_file_path)
            logging.debug(f"Saved file: {file.filename} to temporary directory: {tempfile.gettempdir()}")

        for file in files:
            if file.filename.endswith('.shp'):
                shp_path = os.path.join(tempfile.gettempdir(), file.filename)
                logging.debug(f"Shapefile path: {shp_path}")

                # Load and reproject to WGS84
                shp_data = gpd.read_file(shp_path)
                logging.debug("Shapefile loaded successfully")

                if shp_data.crs is not None and shp_data.crs.to_string() != 'EPSG:4326':
                    logging.debug(f"Original CRS: {shp_data.crs}")
                    shp_data = shp_data.to_crs(epsg=4326)
                    logging.debug("Shapefile reprojected to EPSG:4326")

                layer_name = os.path.splitext(file.filename)[0]
                geojson_data[layer_name] = shp_data.__geo_interface__

            elif file.filename.endswith('.tif'):
                tif_path = os.path.join(tempfile.gettempdir(), file.filename)
                logging.debug(f"TIFF file path: {tif_path}")

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

                        reprojected_tif_path = os.path.join(tempfile.gettempdir(), 'reprojected_' + file.filename)
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
                        tif_path = reprojected_tif_path
                        logging.debug("TIFF file reprojected to EPSG:4326")

                    geotiff_files.append(tif_path)

                    # Extract bounds for correct overlay
                    with rasterio.open(tif_path) as reprojected_src:
                        bounds = reprojected_src.bounds  # Ensure we use reprojected bounds
                        logging.debug(f"Reprojected TIFF bounds: {bounds}")

                        # Read bands 1, 2, 3 and normalize
                        data = reprojected_src.read([3, 2, 1])

                        # Normalize the data to the range 0-255
                        data = np.clip(data, 0, 4000)  # Clip values to the 0-4000 range
                        data = (data / 4000) * 255  # Scale to 0-255
                        data = data.astype(np.uint8)

                        logging.debug("Normalized bands to 0-255 with clipping and scaling")

                        # Create an RGB image with an alpha channel
                        alpha = np.all(data == 0, axis=0).astype(np.uint8) * 255
                        img = np.dstack((data[0], data[1], data[2], 255 - alpha))
                        img = Image.fromarray(img, 'RGBA')
                        png_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(file.filename)[0]}.png")
                        img.save(png_path)
                        logging.debug(f"Saved PNG image: {png_path}")

                        # Add path and spatial bounds to PNG metadata in the correct format for Leaflet
                        png_files.append({
                            "path": png_path,
                            "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
                        })

        return {
            "geojson_data": geojson_data,
            "png_files": [{"path": f"/temp/{os.path.basename(png['path'])}", "bounds": png["bounds"]} for png in png_files],
            "geotiff_files": [f"/temp/{os.path.basename(tif)}" for tif in geotiff_files]
        }
    except Exception as e:
        logging.error(f"Error processing files: {e}")
        return {"error": str(e)}