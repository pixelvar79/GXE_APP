var map = L.map('map').setView([0, 0], 2);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 40,
}).addTo(map);
var layers = {};
var pngLayers = {};
var coords = [];
var corners = [];
var markers = [];  // Array to keep track of markers
var csmPath = '';
var orthoPath = '';  // Variable to store ortho path
var dtmPath = '';  // Variable to store dtm path
var originalOrthoPath = '';  // Variable to store original ortho path
var layerControl = L.control.layers(null, null, { position: 'topright', collapsed: false }).addTo(map);
var allowAddingMarkers = true;  // Flag to control adding markers
var pairs = [];  // Array to store pairs of ortho and dtm paths

document.getElementById('upload-button').addEventListener('click', function() {
    document.getElementById('folder-input').click();
});

document.getElementById('folder-input').addEventListener('change', function(event) {
    var files = event.target.files;
    var folderPath = files[0].webkitRelativePath.split('/')[0];  // Get the folder path
    console.log("Selected folder path:", folderPath);  // Log the folder path

    // Show loading message
    document.getElementById('loading-message').style.display = 'block';

    fetch('http://127.0.0.1:5000/api/process_folder', {  // Ensure the URL is correct
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ input_folder: folderPath })
    })
    .then(response => {
        console.log("Response status:", response.status);  // Log the response status
        return response.json();
    })
    .then(data => {
        console.log("Response data:", data);  // Log the response data
        if (data.error) {
            alert('Error processing folder: ' + data.error);
        } else {
            if (data.messages) {
                document.getElementById('message').innerText = data.messages.join('\n');
            } else {
                document.getElementById('message').innerText = "Folder processed successfully.";
            }
            handlePairs(data);
        }
    })
    .catch(error => {
        console.error("Error:", error);  // Log any errors
    })
    .finally(() => {
        // Hide loading message
        document.getElementById('loading-message').style.display = 'none';
    });
});

// Add event listener for map clicks to capture coordinates
map.on('click', function(e) {
    if (allowAddingMarkers) {
        var lat = e.latlng.lat;
        var lon = e.latlng.lng;
        coords.push([lat, lon]);
        console.log("Captured coordinates:", coords);  // Log the captured coordinates

        // Add marker to the map and keep track of it
        var marker = L.marker([lat, lon]).addTo(map).bindPopup('Coordinate: ' + lat + ', ' + lon).openPopup();
        markers.push(marker);

        // Add event listener for right-click to remove the marker
        marker.on('contextmenu', function() {
            map.removeLayer(marker);
            // Remove the marker from the markers array
            markers = markers.filter(m => m !== marker);
            // Remove the coordinates from the coords array
            coords = coords.filter(c => c[0] !== lat || c[1] !== lon);
            console.log("Updated coordinates after removal:", coords);  // Log the updated coordinates
        });
    }
});

document.getElementById('corner-button').addEventListener('click', function() {
    if (corners.length < 4) {
        map.once('click', function(e) {
            var lat = e.latlng.lat;
            var lon = e.latlng.lng;
            corners.push([lat, lon]);
            console.log("Captured corner coordinates:", corners);  // Log the captured corner coordinates

            // Add marker to the map and keep track of it
            var marker = L.marker([lat, lon], {icon: L.icon({iconUrl: 'corner-icon.png'})}).addTo(map).bindPopup('Corner: ' + lat + ', ' + lon).openPopup();
            markers.push(marker);

            // Add event listener for right-click to remove the marker
            marker.on('contextmenu', function() {
                map.removeLayer(marker);
                // Remove the marker from the markers array
                markers = markers.filter(m => m !== marker);
                // Remove the coordinates from the corners array
                corners = corners.filter(c => c[0] !== lat || c[1] !== lon);
                console.log("Updated corner coordinates after removal:", corners);  // Log the updated corner coordinates
            });
        });
    } else {
        alert("You have already added 4 corners.");
    }
});

document.getElementById('end-collection-button').addEventListener('click', function() {
    if (corners.length !== 4) {
        alert('Please add exactly 4 corners before ending the collection.');
        return;
    }

    // Send the collected coordinates and corners to the backend
    fetch('/api/save_coords', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coords: coords, corners: corners })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Save coordinates response data:", data);  // Log the response data
        if (data.error) {
            alert('Error saving coordinates: ' + data.error);
        } else {
            alert('Coordinates and corners saved successfully');
            allowAddingMarkers = false;  // Disable adding markers after saving
        }
    })
    .catch(error => {
        console.error("Error:", error);  // Log any errors
    });
});

document.getElementById('reset-button').addEventListener('click', function() {
    // Clear all markers from the map
    markers.forEach(function(marker) {
        map.removeLayer(marker);
    });
    markers = [];  // Reset the markers array
    coords = [];   // Reset the coordinates array
    corners = [];  // Reset the corners array
    allowAddingMarkers = true;  // Allow adding new markers
    console.log("Markers and coordinates reset");  // Log the reset action
});

document.getElementById('interpolate-button').addEventListener('click', function() {
    if (corners.length !== 4) {
        alert('Please add exactly 4 corners before interpolating.');
        return;
    }
    // Show processing message
    document.getElementById('message').innerText = 'Processing data...';
    // Show loading message
    document.getElementById('loading-message').style.display = 'block';

    // Get selected ortho and dtm paths
    var selectedOrthoPath = document.getElementById('ortho-select').value;
    var selectedDtmPath = document.getElementById('dtm-select').value;

    // Find the original ortho path that matches the selected ortho path
    var selectedPair = pairs.find(pair => pair.ortho_path === selectedOrthoPath);
    if (selectedPair) {
        originalOrthoPath = selectedPair.original_ortho_path;
    }

    fetch('/api/interpolate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coords: coords, corners: corners, ortho_path: selectedOrthoPath, dtm_path: selectedDtmPath, original_ortho_path: originalOrthoPath })
    })
    .then(response => response.blob())
    .then(blob => {
        var url = URL.createObjectURL(blob);
        console.log("Interpolated layer URL:", url);  // Log the URL of the interpolated layer
        // Prevent adding the interpolated layer to the map
        // var interpolatedLayer = L.imageOverlay(url, [[min_lat, min_lon], [max_lat, max_lon]]).addTo(map);
        // console.log("Interpolated layer added to map");  // Log the addition of the interpolated layer
    })
    .catch(error => {
        console.error("Error:", error);  // Log any errors
    })
    .finally(() => {
        // Hide loading message
        document.getElementById('loading-message').style.display = 'none';
    });
});

document.getElementById('zoom-button').addEventListener('click', function() {
    // Get selected ortho path
    var selectedOrthoPath = document.getElementById('ortho-select').value;

    // Find the corresponding layer and zoom to its bounds
    var layer = pngLayers[selectedOrthoPath];
    if (layer) {
        map.fitBounds(layer.getBounds());
        console.log("Zoomed to active layer:", selectedOrthoPath);  // Log the zoom action
    } else {
        console.error("Layer not found for path:", selectedOrthoPath);  // Log the error
    }
});

function handlePairs(data) {
    var orthoSelect = document.getElementById('ortho-select');
    var dtmSelect = document.getElementById('dtm-select');
    orthoSelect.innerHTML = '';
    dtmSelect.innerHTML = '';

    pairs = data;  // Store the pairs data

    data.forEach(pair => {
        var orthoOption = document.createElement('option');
        orthoOption.value = pair.ortho_path;
        orthoOption.text = pair.ortho_path.split(/[\\/]/).pop();  // Display only the file name
        orthoSelect.appendChild(orthoOption);

        var dtmOption = document.createElement('option');
        dtmOption.value = pair.dtm_path;
        dtmOption.text = pair.dtm_path.split(/[\\/]/).pop();  // Display only the file name
        dtmSelect.appendChild(dtmOption);

        handlePNGFiles(pair);
    });
}

// Handle PNG files
function handlePNGFiles(data) {
    if (data.png_path && data.bounds) {
        var imageUrl = 'http://127.0.0.1:5000' + data.png_path;
        var imageBounds = data.bounds;
        console.log("Adding PNG to map:", imageUrl, imageBounds);  // Log the PNG details
        var pngLayer = L.imageOverlay(imageUrl, imageBounds, {
            opacity: 1,
            interactive: true,
            errorOverlayUrl: '',
            zIndex: 1,
            className: '',
            pane: 'overlayPane',
            attribution: null,
            crossOrigin: false,
            alt: '',
            onError: null,
            onLoad: function() {
                var img = this.getElement();
                img.style.opacity = 1;
                img.onload = function() {
                    var canvas = document.createElement('canvas');
                    var context = canvas.getContext('2d');
                    canvas.width = img.width;
                    canvas.height = img.height;
                };
            }
        });
        pngLayers[data.png_path] = pngLayer;
        layerControl.addOverlay(pngLayer, "TIFF: " + data.png_path);
        pngLayer.addTo(map);

        // Fit the map to the bounds of the new layer
        map.fitBounds(imageBounds);
    } else {
        console.error("PNG path or bounds are missing in the response data");
    }
}

// Update the displayed value of the sliders
document.getElementById('clip-min-red').addEventListener('input', function() {
    document.getElementById('clip-min-red-value').innerText = this.value;
});
document.getElementById('clip-max-red').addEventListener('input', function() {
    document.getElementById('clip-max-red-value').innerText = this.value;
});
document.getElementById('clip-min-green').addEventListener('input', function() {
    document.getElementById('clip-min-green-value').innerText = this.value;
});
document.getElementById('clip-max-green').addEventListener('input', function() {
    document.getElementById('clip-max-green-value').innerText = this.value;
});
document.getElementById('clip-min-blue').addEventListener('input', function() {
    document.getElementById('clip-min-blue-value').innerText = this.value;
});
document.getElementById('clip-max-blue').addEventListener('input', function() {
    document.getElementById('clip-max-blue-value').innerText = this.value;
});

// Function to normalize data for each channel
function normalizeData(data, clipMin, clipMax) {
    data = np.clip(data, clipMin, clipMax);  // Clip values to the specified range
    data = (data - clipMin) / (clipMax - clipMin) * 255;  // Scale to 0-255
    data = data.astype(np.uint8);
    return data;
}

// Function to update the image based on slider values
function updateImage() {
    var clipMinRed = parseInt(document.getElementById('clip-min-red').value);
    var clipMaxRed = parseInt(document.getElementById('clip-max-red').value);
    var clipMinGreen = parseInt(document.getElementById('clip-min-green').value);
    var clipMaxGreen = parseInt(document.getElementById('clip-max-green').value);
    var clipMinBlue = parseInt(document.getElementById('clip-min-blue').value);
    var clipMaxBlue = parseInt(document.getElementById('clip-max-blue').value);

    // Fetch the image data and normalize it
    fetch('/api/get_image_data')
        .then(response => response.json())
        .then(data => {
            var redChannel = normalizeData(data.red, clipMinRed, clipMaxRed);
            var greenChannel = normalizeData(data.green, clipMinGreen, clipMaxGreen);
            var blueChannel = normalizeData(data.blue, clipMinBlue, clipMaxBlue);
            // Combine the channels and update the image on the map
            // (This part depends on how the image data is being handled and displayed)
        })
        .catch(error => {
            console.error("Error fetching image data:", error);
        });
}

// Add event listeners to update the image when the sliders change
document.getElementById('clip-min-red').addEventListener('change', updateImage);
document.getElementById('clip-max-red').addEventListener('change', updateImage);
document.getElementById('clip-min-green').addEventListener('change', updateImage);
document.getElementById('clip-max-green').addEventListener('change', updateImage);
document.getElementById('clip-min-blue').addEventListener('change', updateImage);
document.getElementById('clip-max-blue').addEventListener('change', updateImage);