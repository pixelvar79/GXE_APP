import os
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject as rasterio_reproject

progress = 0

def reproject_tiff(input_path, output_path, target_crs="EPSG:4326"):
    try:
        with rasterio.open(input_path) as src:
            if src.crs is None:
                return f"TIFF file '{input_path}' does not have a valid CRS."
            if src.crs.to_string() == target_crs:
                return f"TIFF file '{input_path}' is already in the target CRS '{target_crs}'. No reprojection needed."

            meta = src.meta.copy()
            transform, width, height = calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds
            )
            meta.update({
                'crs': target_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open(output_path, 'w', **meta) as dest:
                for i in range(1, src.count + 1):
                    rasterio_reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dest, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=target_crs,
                        resampling=Resampling.nearest
                    )
            return f"Reprojected '{input_path}' to '{output_path}' with CRS '{target_crs}'"
    except rasterio.errors.RasterioIOError as e:
        return f"Error opening file '{input_path}': {e}"
    except Exception as e:
        return f"An unexpected error occurred while processing '{input_path}': {e}"

def reproject_all_tiffs(input_folder, output_folder, target_crs):
    global progress
    messages = []
    total_files = sum(len(list(files)) for _, _, files in os.walk(input_folder) if any(f.endswith('.tif') for f in files))
    processed_count = 0

    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith(".tif"):
                input_path = os.path.join(root, filename)
                relative_path = os.path.relpath(root, input_folder)
                target_folder = os.path.join(output_folder, relative_path)
                os.makedirs(target_folder, exist_ok=True)
                output_path = os.path.join(target_folder, filename)

                # Normalize paths to ensure consistency
                input_path = os.path.normpath(input_path)
                output_path = os.path.normpath(output_path)

                result = reproject_tiff(input_path, output_path, target_crs)
                messages.append(result)
                
                processed_count += 1
                progress = (processed_count / total_files) * 100
                print(f"Progress: {progress:.2f}% - {result}")

    return messages