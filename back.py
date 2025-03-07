import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
import tempfile
import logging

from metashape import process_metashape, process_tif
from reproject import reproject_all_tiffs
from interpolate import process_to_stack, process_all_pairs
from shiftcorrector import process_files, collect_marks
from polycreator import process_files, save_field_trial, save_gdf, save_edited_object
from plotvisualizer import list_geojson_files, reprojected_geojson, process_selected_polygons, extract_statistics, get_accessions

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'outputs'  # Define a temporary folder within the project subdirectory

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)  # Create the temporary folder if it doesn't exist

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

BASE_DIRECTORY_DATA = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data"

progress = 0

logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

log_messages = []

@app.route('/')
def index():
    return render_template('intro.html')

###################################
# Metashape

@app.route('/metashape.html')
def metashape_page():
    return render_template('metashape.html')

@app.route('/api/metashape', methods=['POST'])
def metashape_api():
    data = request.json
    input_dir = data.get('inputDir')
    output_dir = data.get('outputDir')
    output_types = data.get('outputTypes', [])

    if not input_dir or not output_dir:
        return jsonify({'success': False, 'message': 'Input and output directories are required.'}), 400

    try:
        results = process_metashape(input_dir, output_dir, output_types, log_messages)
        #results = process_metashape(input_dir, output_dir, log_messages)
        processed_results = []
        for result in results:
            processed_result = process_tif(result["path"])
            processed_results.append(processed_result)
        return jsonify({'success': True, 'message': 'Metashape project setup successful!', 'results': processed_results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

####################################### 
# Reprojection

@app.route('/reprojecttif.html')
def reproject_page():
    return render_template('reprojecttif.html')

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

#######################################
# Interpolation
@app.route('/norm_stack.html')
def knn_interpolation_page():
    return render_template('norm_stack.html')

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

#############################
# Shift Corrector

@app.route('/shiftcorrector.html')

def shift_page():
    return render_template('shiftcorrector.html')

@app.route('/process_images', methods=['POST'])
def process_images_route():
    input_folder = request.form['input_folder']
    full_path = os.path.join(BASE_DIRECTORY, input_folder)
    results = process_files(full_path)
    print(results)
    return jsonify(results)

@app.route('/collect_marks', methods=['POST'])
def collect_marks_route():
    return collect_marks()

################
# Field Trial Creator

@app.route('/polycreator.html')

def create_page():
    return render_template('polycreator.html')

@app.route('/create_field_trial', methods=['POST'])
def create_field_trial():
    return save_field_trial()

@app.route('/save-gdf', methods=['POST'])
def save_gdf_route():
    return save_gdf()

@app.route('/save-edited-object', methods=['POST'])
def save_edited_object_route():
    return save_edited_object()

####################
# Trial analyzer

@app.route('/plotvisualizer.html')

def analyze_page():
    return render_template('plotvisualizer.html')

@app.route('/list-geojson-files', methods=['GET'])
def list_geojson_files_route():
    return list_geojson_files()

@app.route('/reprojected-geojson/<path:filepath>', methods=['GET'])
def reprojected_geojson_route(filepath):
    return reprojected_geojson(filepath)

@app.route('/process_images1', methods=['POST'])
def process_images_route1():
    input_folder = request.form['input_folder']
    full_path = os.path.join(BASE_DIRECTORY_DATA, 'images',input_folder)
    results = process_files(full_path)
    print(results)
    return jsonify(results)

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

@app.route('/get-accessions', methods=['POST'])
def get_accessions_route():
    data = request.get_json()
    shp_file = data['shp_file']
    accessions = get_accessions(shp_file)
    return jsonify({
        "accessions": accessions,
        "shp_file": shp_file  # Pass the shp_file to the frontend
    })
    
@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': log_messages})

@app.route('/temp/<filename>')
def serve_file(filename):
    return send_from_directory(tempfile.gettempdir(), filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)