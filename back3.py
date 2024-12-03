
from plotvisualizer import process_images, list_geojson_files, reprojected_geojson, process_selected_polygons, extract_statistics

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

@app.route('/list-geojson-files', methods=['GET'])
def list_geojson_files_route():
    return list_geojson_files()

@app.route('/reprojected-geojson/<path:filepath>', methods=['GET'])
def reprojected_geojson_route(filepath):
    return reprojected_geojson(filepath)

@app.route('/process_images', methods=['POST'])
def process_images_route():
    return process_images()

@app.route('/process-selected-polygons', methods=['POST'])
def process_selected_polygons_route():
    return process_selected_polygons()

@app.route('/extract-statistics', methods=['POST'])
def extract_statistics_route():
    data = request.get_json()
    tif_file = data['tif_file']
    shp_file = data['shp_file']
    order_ids = data['order_ids']
    statistics = extract_statistics(tif_file, shp_file, order_ids)
    return jsonify(statistics)

@app.route('/temp/<filename>')
def serve_file(filename):
    return send_from_directory(tempfile.gettempdir(), filename)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('templates', path)

if __name__ == '__main__':
    app.run(port=5002, debug=True)