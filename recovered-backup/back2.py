

from flask import Flask, send_from_directory, jsonify, request
import os
import tempfile
import logging
from polycreator import process_files, save_field_trial, save_gdf

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('rasterio').setLevel(logging.WARNING)  # Suppress rasterio debug messages
logging.getLogger('flask_cors').setLevel(logging.WARNING)  # Suppress flask_cors debug messages

@app.route('/')
def index():
    return send_from_directory('templates', 'polycreator.html')

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


@app.route('/create_field_trial', methods=['POST'])
def create_field_trial():
    return save_field_trial()

@app.route('/save-gdf', methods=['POST'])
def save_gdf_route():
    return save_gdf()

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('templates', path)

if __name__ == '__main__':
    app.run(port=5002, debug=True)