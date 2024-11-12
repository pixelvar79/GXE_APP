

import os
import shutil
import json
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
import tempfile
import logging
import numpy as np

from reproject import reproject_all_tiffs
from map_visualization import process_files
from interpolate import process_to_stack, process_all_pairs

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'outputs'  # Define a temporary folder within the project subdirectory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)  # Create the temporary folder if it doesn't exist

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"
progress = 0

# Configure logging
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

@app.route('/')
def index():
    return render_template('intro.html')

@app.route('/reprojecttif.html')
def reproject_page():
    return render_template('reprojecttif.html')

@app.route('/mapvisualization.html')
def map_visualization_page():
    return render_template('map_visualization.html')

@app.route('/preprocessing1.html')
def knn_interpolation_page():
    return render_template('preprocessing1.html')

@app.route('/api/reproject', methods=['POST'])
def reproject():
    global progress
    progress = 0  # Reset progress at the start of the task
    data = request.json
    logging.debug(f"Received JSON Data: {data}")  # Log the JSON received

    input_dir = os.path.join(BASE_DIRECTORY, data['inputDir'])
    output_dir = os.path.join(BASE_DIRECTORY, data['outputDir'])
    target_crs = f"EPSG:{data['targetCRS']}"

    if not os.path.exists(input_dir):
        logging.error(f"Input directory '{input_dir}' does not exist.")
        return jsonify({"messages": [f"Input directory '{input_dir}' does not exist."]})

    os.makedirs(output_dir, exist_ok=True)
    results = reproject_all_tiffs(input_dir, output_dir, target_crs)
    progress = 100  # Ensure progress is set to 100% when done
    return jsonify({"messages": results})

@app.route('/api/map_visualization', methods=['POST'])
def map_visualization():
    try:
        if 'file' not in request.files:
            logging.error("No file part in the request")
            return jsonify({"error": "No file part in the request"}), 400

        files = request.files.getlist('file')
        logging.debug(f"Received files: {[file.filename for file in files]}")

        result = process_files(files)
        if "error" in result:
            return jsonify({"error": result["error"]}), 500

        return jsonify(result)
    except Exception as e:
        logging.error(f"Error processing files: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/process_folder', methods=['POST'])
def process_folder():
    data = request.json
    logging.debug(f"Received JSON Data: {data}")  # Log the JSON received
    input_folder = data.get('input_folder')
    coords = data.get('coords', [])
    corners = data.get('corners', [])
    clip_min = data.get('clip_min', 0)  # Get clip_min from the request, default to 0
    clip_max = data.get('clip_max', 4000)  # Get clip_max from the request, default to 4000
    full_path = os.path.join(BASE_DIRECTORY, input_folder)
    logging.debug(f"Full path: {full_path}")  # Log the full path

    if not os.path.isdir(full_path):
        logging.error(f"Invalid input folder: {full_path}")
        return jsonify({"error": "Invalid input folder"}), 400

    results = process_all_pairs(full_path, clip_min, clip_max)
    if "error" in results:
        logging.error(f"Error processing pairs: {results['error']}")
        return jsonify(results), 500

    logging.debug(f"Process all pairs result: {results}")  # Log the result
    return jsonify(results)

@app.route('/api/save_coords', methods=['POST'])
def save_coords():
    data = request.json
    coords = data.get('coords', [])
    corners = data.get('corners', [])
    logging.debug(f"Received coordinates: {coords}")  # Log the coordinates
    logging.debug(f"Received corners: {corners}")  # Log the corners
    # Save the coordinates and corners to a file, database, or process them as needed
    # For example, save to a JSON file
    with open('coords.json', 'w') as f:
        json.dump({"coords": coords, "corners": corners}, f)
    return jsonify({"message": "Coordinates and corners saved successfully"})

@app.route('/api/interpolate', methods=['POST'])
def interpolate_endpoint():
    data = request.json
    logging.debug(f"Received JSON Data: {data}")  # Log the JSON received
    coords = data.get('coords', [])
    corners = data.get('corners', [])
    ortho_path = data.get('ortho_path')
    original_ortho_path = data.get('original_ortho_path')
    dtm_path = data.get('dtm_path')
    output_folder = os.path.dirname(dtm_path)  # Set output_folder to the directory of dtm_path

    if not coords or not corners or not ortho_path or not dtm_path or not original_ortho_path:
        logging.error("Missing required data")
        return jsonify({"error": "Missing required data"}), 400

    result = process_to_stack(ortho_path, dtm_path, coords, corners, output_folder, original_ortho_path)
    if "error" in result:
        logging.error(f"Error interpolating coordinates: {result['error']}")
        return jsonify(result), 500

    logging.debug(f"Interpolate result: {result}")  # Log the result
    return send_file(result["interpolated_path"], as_attachment=True)

@app.route('/temp/<path:filename>')
def serve_temp_file(filename):
    return send_from_directory(tempfile.gettempdir(), filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)