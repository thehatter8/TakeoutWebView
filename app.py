# backend/app.py
from flask import Flask, render_template, request, jsonify
import os
import csv
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'json'}

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_csv_file(file_path):
    latlong_data = []  # To store latitude and longitude data
    
    # Open and read the CSV file
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Read the first row (headers)
        head_lower = [header.lower() for header in headers]
        # Validate headers
        if head_lower != ["latitude", "longitude"]:
            return {"status": "Invalid CSV format - incorrect headers", "latlong_data": []}
        
        # Process the remaining rows
        for row in reader:
            if len(row) != 2:
                continue  # Skip rows that don't have exactly two columns
                
            try:
                latitude = float(row[0])
                longitude = float(row[1])
                latlong_data.append([latitude, longitude])
            except ValueError:
                continue  # Skip rows where latitude/longitude are not valid numbers

    # Return processed data
    return {
        "status": "CSV processed",
        "latlong_data": latlong_data
    }

def handle_json_file(file_path):
    try:
        # Read the raw content and print the first few characters for debugging
        with open(file_path, 'r', encoding='utf-8') as infile:
            raw_content = infile.read()
            print(f"First 100 characters of file: {repr(raw_content[:100])}")
            
            # Try to parse the JSON
            data = json.loads(raw_content)
            
            latlong_data = []
            specific_locations_data = []
            
            # Validate the basic structure
            if not isinstance(data, list):
                return {
                    "status": "Invalid JSON format - expected a list at root level",
                    "error": "JSON must be a list of timeline objects"
                }
            
            # Process each item in the data
            for item in data:
                if "timelineObjects" in item:
                    for obj in item["timelineObjects"]:
                        if "placeVisit" in obj:
                            location = obj["placeVisit"].get("location", {})
                            
                            # Extract latitude, longitude, placeId, and address
                            latitudeE7 = location.get("latitudeE7")
                            longitudeE7 = location.get("longitudeE7")
                            placeId = location.get("placeId")
                            address = location.get("address")
                            
                            # Append latitude/longitude data
                            if latitudeE7 is not None and longitudeE7 is not None:
                                latlong_data.append([latitudeE7 / 1e7, longitudeE7 / 1e7])
                            
                            # Append placeId/address data
                            if placeId and address:
                                specific_locations_data.append([placeId, address])

                       

            return {
                "status": "JSON processed",
                "latlong_data": latlong_data,
                "specific_locations_data": specific_locations_data
            }
            
    except json.JSONDecodeError as e:
        return {
            "status": "JSON parsing error",
            "error": str(e),
            "position": f"Line {e.lineno}, Column {e.colno}"
        }
    except Exception as e:
        return {
            "status": "Error processing JSON",
            "error": str(e)
        }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Process based on file type
        file_extension = filename.rsplit('.', 1)[1].lower()
        if file_extension == 'csv':
            result = handle_csv_file(file_path)
        else:  # json
            result = handle_json_file(file_path)
            
        return jsonify(result)
    
    return jsonify({'error': 'File type not allowed'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
