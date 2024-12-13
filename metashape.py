

# import os
# import Metashape
# import tempfile
# import rasterio

# import tempfile
# import logging
# import numpy as np
# import rasterio
# from rasterio.transform import Affine
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# from PIL import Image



# def process_metashape(input_dir, output_dir, log_messages):
#     def log(message):
#         print(message)
#         log_messages.append(message)

#     # Check license activation status
#     if Metashape.app.activated:
#         log("Metashape license is active.")
#     else:
#         log("Metashape license is not active.")

#     # Base directories
#     base_input_directory = os.path.abspath("../../G_E_PROJECT/data/images")
#     base_output_directory = os.path.abspath("../../G_E_PROJECT/data/images")

#     # Construct full paths
#     root_directory = os.path.join(base_input_directory, input_dir)
#     output_root_directory = os.path.join(base_output_directory, output_dir)

#     log(f"Root directory: {root_directory}")
#     log(f"Output root directory: {output_root_directory}")

#     # # Check if the output directory is writable
#     # if not os.access(output_root_directory, os.W_OK):
#     #     log(f"Output directory is not writable: {output_root_directory}")
#     #     raise PermissionError(f"Output directory is not writable: {output_root_directory}")

#     os.makedirs(output_root_directory, exist_ok=True)

#     # Create a function to process a single project
#     def process_steps(project_folder, tif_files):
#         output_project_directory = os.path.join(output_root_directory, project_folder)
#         os.makedirs(output_project_directory, exist_ok=True)
        
#         log(f'Initializing {project_folder} project')

#         doc = Metashape.Document()
#         doc.save(os.path.join(output_project_directory, f"{project_folder}_project.psx"))
        
#         log(f'Created {project_folder}_project.psx')
        
#         chunk = doc.addChunk()
#         chunk.addPhotos(tif_files, load_xmp_calibration=True, load_xmp_accuracy=True, load_xmp_orientation=True, load_xmp_antenna=True)
#         doc.save()
        
#         log(str(len(chunk.cameras)) + " images loaded")
#         chunk.matchPhotos(keypoint_limit=40000, tiepoint_limit=10000, reference_preselection=True)
#         doc.save()
        
#         log(f'Aligning photos in {project_folder} project')
#         chunk.alignCameras()
#         doc.save()

#         log(f'Optimize alignment of photos in {project_folder} project')
#         chunk.optimizeCameras(fit_corrections=True)
#         doc.save()

#         log(f'Calibrating reflectance in {project_folder} project')
#         chunk.calibrateReflectance(use_sun_sensor=True)
#         doc.save()

#         log(f'Building depth Maps in {project_folder} project')
#         chunk.buildDepthMaps(downscale=2, filter_mode=Metashape.MildFiltering)
#         doc.save()

#         log(f'Building model in {project_folder} project')
#         chunk.buildModel(source_data=Metashape.DepthMapsData)
#         doc.save()

#         has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

#         if has_transform:
#             log(f'Building Point Cloud in {project_folder} project')
#             chunk.buildPointCloud()
#             doc.save()
            
#             log(f'Building DEM in {project_folder} project')
#             chunk.buildDem(source_data=Metashape.PointCloudData)
#             doc.save()
            
#             log(f'Building ORTHO in {project_folder} project')
#             chunk.buildOrthomosaic(surface_data=Metashape.ElevationData)
#             doc.save()

#         # export results
#         output_report = os.path.join(output_project_directory, f"{project_folder}_report.pdf")
#         chunk.exportReport(output_report)

#         if chunk.elevation:
#             log(f'Exporting DEM in {project_folder} project')
#             output_dtm = os.path.join(output_project_directory, f"{project_folder}_dtm.tif")
#             chunk.exportRaster(output_dtm, source_data=Metashape.ElevationData)

#         if chunk.orthomosaic:
#             log(f'Exporting ORTHO in {project_folder} project')
#             output_orthomosaic = os.path.join(output_project_directory, f"{project_folder}_ortho.tif")
#             chunk.exportRaster(output_orthomosaic, source_data=Metashape.OrthomosaicData, save_alpha=False)
#             doc.save()

#     first_level_folders = [folder for folder in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, folder))]

#     for first_level_folder in first_level_folders:
#         first_level_path = os.path.join(root_directory, first_level_folder)
#         # log(f'first level folders: {first_level_path}')
        
#         second_level_folders = [folder for folder in os.listdir(first_level_path) if os.path.isdir(os.path.join(first_level_path, folder))]
#         log(f'Second level folders: {second_level_folders}')
#         log(f'Count of second level folders: {len(second_level_folders)}')
        
#         for second_level_folder in second_level_folders:
#             second_level_path = os.path.join(first_level_path, second_level_folder)
            
#             tif_files = []
#             for root, _, files in os.walk(second_level_path):
#                 # log(f'root: {root}')
#                 # log(f'files: {files}')
#                 tif_files.extend([os.path.join(root, file) for file in files if file.endswith('.TIF')])
#             # log(f'list of files is {tif_files}')
            
#             process_steps(second_level_folder, tif_files)

#     log("Processing completed for all projects.")
    
    
# def normalize_data(data, clip_min, clip_max):
#     data = np.clip(data, clip_min, clip_max)
#     data = ((data - clip_min) / (clip_max - clip_min) * 255).astype(np.uint8)
#     return data



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

# import os
# import Metashape
# import tempfile
# import rasterio
# import logging
# import numpy as np
# from rasterio.transform import Affine
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# from PIL import Image

# def process_metashape(input_dir, output_dir, log_messages):
#     def log(message):
#         print(message)
#         log_messages.append(message)

#     # Check license activation status
#     if Metashape.app.activated:
#         log("Metashape license is active.")
#     else:
#         log("Metashape license is not active.")

#     # Base directories
#     base_input_directory = os.path.abspath("../../G_E_PROJECT/data/images")
#     base_output_directory = os.path.abspath("../../G_E_PROJECT/data/images")

#     # Construct full paths
#     root_directory = os.path.join(base_input_directory, input_dir)
#     output_root_directory = os.path.join(base_output_directory, output_dir)

#     log(f"Root directory: {root_directory}")
#     log(f"Output root directory: {output_root_directory}")

#     os.makedirs(output_root_directory, exist_ok=True)

#     def process_steps(project_folder, tif_files):
#         output_project_directory = os.path.join(output_root_directory, project_folder)
#         os.makedirs(output_project_directory, exist_ok=True)
        
#         log(f'Initializing {project_folder} project')

#         doc = Metashape.Document()
#         doc.save(os.path.join(output_project_directory, f"{project_folder}_project.psx"))
        
#         log(f'Created {project_folder}_project.psx')
        
#         chunk = doc.addChunk()
#         chunk.addPhotos(tif_files, load_xmp_calibration=True, load_xmp_accuracy=True, load_xmp_orientation=True, load_xmp_antenna=True)
#         doc.save()
        
#         log(str(len(chunk.cameras)) + " images loaded")
#         chunk.matchPhotos(keypoint_limit=40000, tiepoint_limit=10000, reference_preselection=True)
#         doc.save()
        
#         log(f'Aligning photos in {project_folder} project')
#         chunk.alignCameras()
#         doc.save()

#         log(f'Optimize alignment of photos in {project_folder} project')
#         chunk.optimizeCameras(fit_corrections=True)
#         doc.save()

#         log(f'Calibrating reflectance in {project_folder} project')
#         chunk.calibrateReflectance(use_sun_sensor=True)
#         doc.save()

#         log(f'Building depth Maps in {project_folder} project')
#         chunk.buildDepthMaps(downscale=2, filter_mode=Metashape.MildFiltering)
#         doc.save()

#         log(f'Building model in {project_folder} project')
#         chunk.buildModel(source_data=Metashape.DepthMapsData)
#         doc.save()

#         has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

#         results = []

#         if has_transform:
#             log(f'Building Point Cloud in {project_folder} project')
#             chunk.buildPointCloud()
#             doc.save()
            
#             log(f'Building DEM in {project_folder} project')
#             chunk.buildDem(source_data=Metashape.PointCloudData)
#             doc.save()
            
#             log(f'Building ORTHO in {project_folder} project')
#             chunk.buildOrthomosaic(surface_data=Metashape.ElevationData)
#             doc.save()

#         # export results
#         output_report = os.path.join(output_project_directory, f"{project_folder}_report.pdf")
#         chunk.exportReport(output_report)

#         if chunk.elevation:
#             log(f'Exporting DEM in {project_folder} project')
#             output_dtm = os.path.join(output_project_directory, f"{project_folder}_dtm.tif")
#             chunk.exportRaster(output_dtm, source_data=Metashape.ElevationData)
#             results.append(process_tif(output_dtm))

#         if chunk.orthomosaic:
#             log(f'Exporting ORTHO in {project_folder} project')
#             output_orthomosaic = os.path.join(output_project_directory, f"{project_folder}_ortho.tif")
#             chunk.exportRaster(output_orthomosaic, source_data=Metashape.OrthomosaicData, save_alpha=False)
#             results.append(process_tif(output_orthomosaic))
#             doc.save()

#         return results

#     first_level_folders = [folder for folder in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, folder))]

#     all_results = []

#     for first_level_folder in first_level_folders:
#         first_level_path = os.path.join(root_directory, first_level_folder)
        
#         second_level_folders = [folder for folder in os.listdir(first_level_path) if os.path.isdir(os.path.join(first_level_path, folder))]
#         log(f'Second level folders: {second_level_folders}')
#         log(f'Count of second level folders: {len(second_level_folders)}')
        
#         for second_level_folder in second_level_folders:
#             second_level_path = os.path.join(first_level_path, second_level_folder)
            
#             tif_files = []
#             for root, _, files in os.walk(second_level_path):
#                 tif_files.extend([os.path.join(root, file) for file in files if file.endswith('.TIF')])
            
#             results = process_steps(second_level_folder, tif_files)
#             all_results.extend(results)

#     log("Processing completed for all projects.")
#     return all_results

# def normalize_data(data, clip_min, clip_max):
#     data = np.clip(data, clip_min, clip_max)
#     data = ((data - clip_min) / (clip_max - clip_min) * 255).astype(np.uint8)
#     return data

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

#                 # Read bands and normalize
#                 if reprojected_src.count == 1:
#                     data = reprojected_src.read(1)
#                     clip_min, clip_max = np.percentile(data, (2, 98))
#                     data = normalize_data(data, clip_min, clip_max)
#                     img = Image.fromarray(data, 'L')
#                 else:
#                     data = reprojected_src.read([3, 2, 1])
#                     clip_min, clip_max = np.percentile(data, (2, 98))
#                     data = normalize_data(data, clip_min, clip_max)
#                     alpha = np.all(data == 0, axis=0).astype(np.uint8) * 255
#                     img = np.dstack((data[0], data[1], data[2], 255 - alpha))
#                     img = Image.fromarray(img, 'RGBA')

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


import os
import Metashape
import tempfile
import rasterio
import logging
import numpy as np
from rasterio.transform import Affine
from rasterio.warp import calculate_default_transform, reproject, Resampling
from PIL import Image

def process_metashape(input_dir, output_dir, log_messages):
    def log(message):
        print(message)
        log_messages.append(message)

    # Check license activation status
    if Metashape.app.activated:
        log("Metashape license is active.")
    else:
        log("Metashape license is not active.")

    # Base directories
    base_input_directory = os.path.abspath("../../G_E_PROJECT/data/images")
    base_output_directory = os.path.abspath("../../G_E_PROJECT/data/images")

    # Construct full paths
    root_directory = os.path.join(base_input_directory, input_dir)
    output_root_directory = os.path.join(base_output_directory, output_dir)

    # log(f"Root directory: {root_directory}")
    # log(f"Output root directory: {output_root_directory}")

    os.makedirs(output_root_directory, exist_ok=True)

    def process_steps(project_folder, tif_files):
        output_project_directory = os.path.join(output_root_directory, project_folder)
        os.makedirs(output_project_directory, exist_ok=True)
        
        # log(f'Initializing {project_folder} project')

        doc = Metashape.Document()
        doc.save(os.path.join(output_project_directory, f"{project_folder}_project.psx"))
        
        log(f'<b>Created</b> {project_folder}_project.psx')
        
        chunk = doc.addChunk()
        chunk.addPhotos(tif_files, load_xmp_calibration=True, load_xmp_accuracy=True, load_xmp_orientation=True, load_xmp_antenna=True)
        
        
        log(f"<b>Loading..</b> {len(chunk.cameras)} cameras")
        chunk.matchPhotos(keypoint_limit=40000, tiepoint_limit=20000, reference_preselection=True)
        
        
        #log(f'<b>Aligning photos</b> in {project_folder} project')
        log(f'<b>Aligning photos..</b>')
        chunk.alignCameras()
        

        #log(f'<b>Optimize alignment of photos</b> in {project_folder} project')
        log(f'<b>Optimize alignment of photos..</b>')
        chunk.optimizeCameras(fit_corrections=True)
        

        #log(f'<b>Calibrating reflectance..</b> in {project_folder} project')
        log(f'<b>Calibrating reflectance..</b>')

        chunk.calibrateReflectance(use_sun_sensor=True)
        
        #log(f'<b>Building depth Maps</b> in {project_folder} project')
        log(f'<b>Building depth Maps..</b>')
        chunk.buildDepthMaps(downscale=2, filter_mode=Metashape.MildFiltering)
        

        #log(f'<b>Building model<b/> in {project_folder} project')
        log(f'<b>Building model..<b/>')

        chunk.buildModel(source_data=Metashape.DepthMapsData)
        

        has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

        results = []

        if has_transform:
            #log(f'<b>Building Point Cloud</b> in {project_folder} project')
            log(f'<b>Building Point Cloud..</b>')
            chunk.buildPointCloud()
            
            
            #log(f'<b>Building DEM</b> in {project_folder} project')
            log(f'<b>Building DEM..</b>')
            chunk.buildDem(source_data=Metashape.PointCloudData)
            doc.save()
            
            #log(f'<b>Building ORTHO</b> in {project_folder} project')
            log(f'<b>Building ORTHO..</b>')
            chunk.buildOrthomosaic(surface_data=Metashape.ElevationData)
            doc.save()

        # export results
        output_report = os.path.join(output_project_directory, f"{project_folder}_report.pdf")
        chunk.exportReport(output_report)

        if chunk.elevation:
            #log(f'<b>Exporting DEM</b> in {project_folder} project')
            log(f'<b>Exporting DEM..</b>')
            output_dtm = os.path.join(output_project_directory, f"{project_folder}_dtm.tif")
            nodata_value = 0  # Specify your desired nodata value here
            chunk.exportRaster(output_dtm, source_data=Metashape.ElevationData, nodata_value=nodata_value)
            results.append({"type": "dtm", "path": output_dtm})

        if chunk.orthomosaic:
            #log(f'<b>Exporting ORTHO</b> in {project_folder} project')
            log(f'<b>Exporting ORTHO..</b>')
            output_orthomosaic = os.path.join(output_project_directory, f"{project_folder}_ortho.tif")
            chunk.exportRaster(output_orthomosaic, source_data=Metashape.OrthomosaicData, save_alpha=False)
            results.append({"type": "ortho", "path": output_orthomosaic})
            doc.save()

        return results

    first_level_folders = [folder for folder in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, folder))]

    all_results = []

    for first_level_folder in first_level_folders:
        first_level_path = os.path.join(root_directory, first_level_folder)
        
        second_level_folders = [folder for folder in os.listdir(first_level_path) if os.path.isdir(os.path.join(first_level_path, folder))]
        log(f'<b>Projects for processing:</b> {second_level_folders}')
        log(f'<b>Number of projects:</b> {len(second_level_folders)}')
        
        for second_level_folder in second_level_folders:
            second_level_path = os.path.join(first_level_path, second_level_folder)
            
            tif_files = []
            for root, _, files in os.walk(second_level_path):
                tif_files.extend([os.path.join(root, file) for file in files if file.endswith('.TIF')])
            
            results = process_steps(second_level_folder, tif_files)
            
            all_results.extend(results)
            
    print(f'All results object is: {all_results}')

    log("Processing completed for all projects.")
    return all_results

def normalize_data(data, clip_min, clip_max):
    data = np.clip(data, clip_min, clip_max)
    data = ((data - clip_min) / (clip_max - clip_min) * 255).astype(np.uint8)
    return data

def process_tif(tif_path):
    try:
        original_tif_path = tif_path  # Initialize original_tif_path
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

                # # Read bands and normalize
                # if reprojected_src.count == 1:
                #     data = reprojected_src.read(1)
                #     clip_min, clip_max = np.percentile(data, (2, 98))
                #     data = normalize_data(data, clip_min, clip_max)
    
                #     img = Image.fromarray(data, 'L')
                
                if reprojected_src.count == 1:
                    data = reprojected_src.read(1)
                    clip_min, clip_max = np.percentile(data, (4, 90))
                    data = normalize_data(data, clip_min, clip_max)
                    
                    # Create an alpha channel where data is zero
                    alpha = (data == 0).astype(np.uint8) * 255
                    
                    # Create the grayscale image
                    img = Image.fromarray(data, 'L')
                    
                    # Create the alpha image
                    alpha_img = Image.fromarray(255 - alpha, 'L')
                    
                    # Combine the grayscale image with the alpha channel
                    img.putalpha(alpha_img)
                
                # # Read bands and normalize
                # if reprojected_src.count == 1:
                #     data = reprojected_src.read(1)
                #     clip_min, clip_max = np.percentile(data, (2, 98))
                #     #data = normalize_data(data, clip_min, clip_max)
                    
                #     # Create an alpha channel where data is zero
                #     alpha = (data == 0).astype(np.uint8) * 255
                    
                #     # Stack the data and alpha channel to create an RGBA image
                #     img = np.dstack((data, data, data, 255 - alpha))
                #     img = Image.fromarray(img, 'RGBA')
                else:
                    data = reprojected_src.read([3, 2, 1])
                    clip_min, clip_max = np.percentile(data, (2, 98))
                    data = normalize_data(data, clip_min, clip_max)
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



# import os
# import Metashape
# import tempfile
# import rasterio
# import logging
# import numpy as np
# from rasterio.transform import Affine
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# from PIL import Image

# def process_metashape(input_dir, output_dir, output_types, log_messages):
#     def log(message):
#         print(message)
#         log_messages.append(message)

#     # Check license activation status
#     if Metashape.app.activated:
#         log("Metashape license is active.")
#     else:
#         log("Metashape license is not active.")

#     # Base directories
#     base_input_directory = os.path.abspath("../../G_E_PROJECT/data/images")
#     base_output_directory = os.path.abspath("../../G_E_PROJECT/data/images")

#     # Construct full paths
#     root_directory = os.path.join(base_input_directory, input_dir)
#     output_root_directory = os.path.join(base_output_directory, output_dir)

#     os.makedirs(output_root_directory, exist_ok=True)

#     def process_steps(project_folder, tif_files):
#         output_project_directory = os.path.join(output_root_directory, project_folder)
#         os.makedirs(output_project_directory, exist_ok=True)

#         doc = Metashape.Document()
#         doc.save(os.path.join(output_project_directory, f"{project_folder}_project.psx"))

#         log(f'<b>Created</b> {project_folder}_project.psx')

#         chunk = doc.addChunk()
#         chunk.addPhotos(tif_files, load_xmp_calibration=True, load_xmp_accuracy=True, load_xmp_orientation=True, load_xmp_antenna=True)

#         log(f"<b>Loading..</b> {len(chunk.cameras)} cameras")
#         chunk.matchPhotos(keypoint_limit=40000, tiepoint_limit=20000, reference_preselection=True)

#         log(f'<b>Aligning photos..</b>')
#         chunk.alignCameras()

#         log(f'<b>Optimize alignment of photos..</b>')
#         chunk.optimizeCameras(fit_corrections=True)

#         log(f'<b>Calibrating reflectance..</b>')
#         chunk.calibrateReflectance(use_sun_sensor=True)

#         log(f'<b>Building depth Maps..</b>')
#         chunk.buildDepthMaps(downscale=2, filter_mode=Metashape.MildFiltering)

#         log(f'<b>Building model..<b/>')
#         chunk.buildModel(source_data=Metashape.DepthMapsData)

#         has_transform = chunk.transform.scale and chunk.transform.rotation and chunk.transform.translation

#         results = []

#         if has_transform:
#             log(f'<b>Building Point Cloud..</b>')
#             chunk.buildPointCloud()

#             if "dem" in output_types:
#                 log(f'<b>Building DEM..</b>')
#                 chunk.buildDem(source_data=Metashape.PointCloudData)
#                 output_dtm = os.path.join(output_project_directory, f"{project_folder}_dtm.tif")
#                 nodata_value = 0  # Specify your desired nodata value here
                
#                 log(f'<b>Exporting DEM..</b>')
#                 chunk.exportRaster(output_dtm, source_data=Metashape.ElevationData, nodata_value=nodata_value)
#                 results.append({"type": "dtm", "path": output_dtm})

#             if "orthomosaic" in output_types:
#                 log(f'<b>Building ORTHO..</b>')
#                 chunk.buildOrthomosaic(surface_data=Metashape.ElevationData)
#                 doc.save()
#                 if chunk.orthomosaic:
#                     log(f'<b>Exporting ORTHO..</b>')
#                     output_orthomosaic = os.path.join(output_project_directory, f"{project_folder}_ortho.tif")
#                     chunk.exportRaster(output_orthomosaic, source_data=Metashape.OrthomosaicData, save_alpha=False)
#                     results.append({"type": "ortho", "path": output_orthomosaic})
#                     doc.save()

#             if "report" in output_types:
#                 output_report = os.path.join(output_project_directory, f"{project_folder}_report.pdf")
#                 chunk.exportReport(output_report)
#                 results.append({"type": "report", "path": output_report})

#         return results

#     first_level_folders = [folder for folder in os.listdir(root_directory) if os.path.isdir(os.path.join(root_directory, folder))]

#     all_results = []

#     for first_level_folder in first_level_folders:
#         first_level_path = os.path.join(root_directory, first_level_folder)

#         second_level_folders = [folder for folder in os.listdir(first_level_path) if os.path.isdir(os.path.join(first_level_path, folder))]
#         log(f'<b>Projects for processing:</b> {second_level_folders}')
#         log(f'<b>Number of projects:</b> {len(second_level_folders)}')

#         for second_level_folder in second_level_folders:
#             second_level_path = os.path.join(first_level_path, second_level_folder)

#             tif_files = []
#             for root, _, files in os.walk(second_level_path):
#                 tif_files.extend([os.path.join(root, file) for file in files if file.endswith('.TIF')])

#             results = process_steps(second_level_folder, tif_files)

#             all_results.extend(results)

#     print(f'All results object is: {all_results}')

#     log("Processing completed for all projects.")
#     return all_results

def normalize_data(data, clip_min, clip_max):
    data = np.clip(data, clip_min, clip_max)
    data = ((data - clip_min) / (clip_max - clip_max) * 255).astype(np.uint8)
    return data

def process_tif(tif_path):
    try:
        original_tif_path = tif_path  # Initialize original_tif_path
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

                if reprojected_src.count == 1:
                    data = reprojected_src.read(1)
                    clip_min, clip_max = np.percentile(data, (4, 90))
                    data = normalize_data(data, clip_min, clip_max)
                    
                    # Create an alpha channel where data is zero
                    alpha = (data == 0).astype(np.uint8) * 255
                    
                    # Create the grayscale image
                    img = Image.fromarray(data, 'L')
                    
                    # Create the alpha image
                    alpha_img = Image.fromarray(255 - alpha, 'L')
                    
                    # Combine the grayscale image with the alpha channel
                    img.putalpha(alpha_img)
                
                else:
                    data = reprojected_src.read([3, 2, 1])
                    clip_min, clip_max = np.percentile(data, (2, 98))
                    data = normalize_data(data, clip_min, clip_max)
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