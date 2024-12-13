

# from flask import Flask, request, jsonify, render_template,send_from_directory
# from metashape import process_metashape, process_files
# import os
# import tempfile


# app = Flask(__name__)

# BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"


# log_messages = []

# @app.route('/')
# def index():
#     return render_template('metashape.html')

# @app.route('/api/metashape', methods=['POST'])
# def metashape_api():
#     data = request.json
#     input_dir = data.get('inputDir')
#     output_dir = data.get('outputDir')

#     if not input_dir or not output_dir:
#         return jsonify({'success': False, 'message': 'Input and output directories are required.'}), 400

#     try:
#         process_metashape(input_dir, output_dir, log_messages)
#         return jsonify({'success': True, 'message': 'Metashape project setup successful!'})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# @app.route('/api/logs', methods=['GET'])
# def get_logs():
#     return jsonify({'logs': log_messages})

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


# if __name__ == '__main__':
#     app.run(port=5004, debug=True)


# from flask import Flask, request, jsonify, render_template, send_from_directory
# from metashape import process_metashape, process_tif
# import os
# import tempfile

# app = Flask(__name__)

# BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

# log_messages = []

# @app.route('/')
# def index():
#     return render_template('metashape.html')

# @app.route('/api/metashape', methods=['POST'])
# def metashape_api():
#     data = request.json
#     input_dir = data.get('inputDir')
#     output_dir = data.get('outputDir')

#     if not input_dir or not output_dir:
#         return jsonify({'success': False, 'message': 'Input and output directories are required.'}), 400

#     try:
#         results = process_metashape(input_dir, output_dir, log_messages)
#         return jsonify({'success': True, 'message': 'Metashape project setup successful!', 'results': results})
#     except Exception as e:
#         return jsonify({'success': False, 'message': str(e)}), 500

# @app.route('/api/logs', methods=['GET'])
# def get_logs():
#     return jsonify({'logs': log_messages})

# @app.route('/process_images', methods=['POST'])
# def process_images_route():
#     input_folder = request.form['input_folder']
#     full_path = os.path.join(BASE_DIRECTORY, input_folder)
#     results = process_tif(full_path)
#     print(results)
#     return jsonify(results)

# @app.route('/temp/<filename>')
# def serve_file(filename):
#     return send_from_directory(tempfile.gettempdir(), filename)

# if __name__ == '__main__':
#     app.run(port=5004, debug=True)

from flask import Flask, request, jsonify, render_template, send_from_directory
from metashape import process_metashape, process_tif
import os
import tempfile

app = Flask(__name__)

BASE_DIRECTORY = "D:/OneDrive - University of Illinois - Urbana/TF/PYTHON_CODE/G_E_PROJECT/data/images"

log_messages = []

@app.route('/')
def index():
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
        #results = process_metashape(input_dir, output_dir, output_types, log_messages)
        results = process_metashape(input_dir, output_dir, log_messages)
        processed_results = []
        for result in results:
            processed_result = process_tif(result["path"])
            processed_results.append(processed_result)
        return jsonify({'success': True, 'message': 'Metashape project setup successful!', 'results': processed_results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': log_messages})

@app.route('/temp/<filename>')
def serve_file(filename):
    return send_from_directory(tempfile.gettempdir(), filename)

if __name__ == '__main__':
    app.run(port=5004, debug=True)