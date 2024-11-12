

# from flask import Flask, send_from_directory, jsonify, request
# import os
# import tempfile
# import logging
# from polycreator import process_files, save_field_trial, save_gdf, save_edited_object
# import json
# import geopandas as gpd
# BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

# app = Flask(__name__)

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
# logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

# @app.route('/')
# def index():
#     return send_from_directory('templates', 'plotvisualizer.html')

# @app.route('/process_images', methods=['POST'])
# def process_images_route():
#     input_folder = request.form['input_folder']
#     full_path = os.path.join(BASE_DIRECTORY, input_folder)
#     results = process_files(full_path)
#     print(results)
#     return jsonify(results)

# @app.route('/temp/<filename>')
# def serve_file(filename):
#     return send_from_directory(tempfile.gettempdir(), filename)

# @app.route('/<path:path>')
# def static_files(path):
#     return send_from_directory('templates', path)

# if __name__ == '__main__':
#     app.run(port=5002, debug=True)

from polycreator import process_files
import json
import geopandas as gpd
import os
from flask import Flask, request, jsonify, send_from_directory
import logging
import tempfile

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

@app.route('/')
def index():
    return send_from_directory('templates', 'plotvisualizer.html')

@app.route('/process_images', methods=['POST'])
def process_images_route():
    input_folder = request.form['input_folder']
    full_path = os.path.join(BASE_DIRECTORY, input_folder)
    results = process_files(full_path)
    print(results)
    return jsonify(results)

@app.route('/temp/<filename>')
def serve_file(filename):
    return send_from_directory(tempfile.gettempdir(), filename)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('templates', path)

# Route to recursively list all .shifted.geojson files in the base directory
@app.route('/list-geojson-files')
def list_geojson_files():
    geojson_files = []
    for root, dirs, files in os.walk(BASE_DIRECTORY):
        for file in files:
            if file.endswith('_shifted.geojson'):
                # Get the relative path from BASE_DIRECTORY
                relative_path = os.path.relpath(os.path.join(root, file), BASE_DIRECTORY)
                geojson_files.append(relative_path)
    return jsonify(geojson_files)

# Route to serve a reprojected GeoJSON file
@app.route('/reprojected-geojson/<path:filepath>')
def reproject_geojson(filepath):
    # Construct absolute path for the file
    file_path = os.path.join(BASE_DIRECTORY, filepath)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # Load and reproject GeoJSON
    gdf = gpd.read_file(file_path)
    gdf = gdf.to_crs("EPSG:4326")  # Reproject to EPSG:4326 (WGS84)
    
    return jsonify(gdf.__geo_interface__)

if __name__ == '__main__':
    app.run(port=5002, debug=True)