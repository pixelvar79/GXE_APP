let marksMap1 = [];
let marksMap2 = [];
let activeReferenceOrtho = null;
let activeTargetOrtho = null;
let originalReferenceOrthoPath = null;
let originalTargetOrthoPath = null;

document.getElementById('upload-button').addEventListener('click', function() {
    document.getElementById('folder-input').click();
});

document.getElementById('folder-input').addEventListener('change', function(event) {
    const folderPath = event.target.files[0].webkitRelativePath.split('/')[0];
    document.getElementById('loading-message1').style.display = 'block';
    document.getElementById('loading-message2').style.display = 'block';
    $.post('/process_images', { input_folder: folderPath }, function(data) {
        // Process the returned data to update the maps and controls
        data.reference.forEach(item => {
            if (item.png_path && item.bounds) {
                const bounds = item.bounds;
                const imageUrl = item.png_path;
                const layer = L.imageOverlay(imageUrl, bounds).addTo(map1);
                map1.fitBounds(bounds);
                const option = new Option(item.ortho_path, item.ortho_path);
                $(option).data('original-ortho-path', item.original_ortho_path);
                $('#ortho-select').append(option);
                layerControl1.addOverlay(layer, item.ortho_path);
            }
        });
        data.target.forEach(item => {
            if (item.png_path && item.bounds) {
                const bounds = item.bounds;
                const imageUrl = item.png_path;
                const layer = L.imageOverlay(imageUrl, bounds).addTo(map2);
                map2.fitBounds(bounds);
                const option = new Option(item.ortho_path, item.ortho_path);
                $(option).data('original-ortho-path', item.original_ortho_path);
                $('#dtm-select').append(option);
                layerControl2.addOverlay(layer, item.ortho_path);
            }
        });
        document.getElementById('loading-message1').style.display = 'none';
        document.getElementById('loading-message2').style.display = 'none';
    });
});

document.getElementById('ortho-select').addEventListener('change', function() {
    activeReferenceOrtho = this.value;
    const selectedOption = $('#ortho-select option:selected');
    originalReferenceOrthoPath = selectedOption.data('original-ortho-path');
});

document.getElementById('dtm-select').addEventListener('change', function() {
    activeTargetOrtho = this.value;
    const selectedOption = $('#dtm-select option:selected');
    originalTargetOrthoPath = selectedOption.data('original-ortho-path');
});

function addMarker(map, marksMap, latlng) {
    const marker = L.marker(latlng).addTo(map);
    marker.on('contextmenu', function() {
        map.removeLayer(marker);
        const index = marksMap.findIndex(m => m.lat === latlng.lat && m.lng === latlng.lng);
        if (index > -1) {
            marksMap.splice(index, 1);
        }
    });
    marksMap.push(latlng);
}

document.getElementById('add-mark1').addEventListener('click', function() {
    map1.once('click', function(e) {
        if (marksMap1.length < 4) {
            addMarker(map1, marksMap1, e.latlng);
        } else {
            alert('You can only add up to 4 marks.');
        }
    });
});

document.getElementById('add-mark2').addEventListener('click', function() {
    map2.once('click', function(e) {
        if (marksMap2.length < 4) {
            addMarker(map2, marksMap2, e.latlng);
        } else {
            alert('You can only add up to 4 marks.');
        }
    });
});

document.getElementById('reset-button').addEventListener('click', function() {
    marksMap1.forEach(function(latlng) {
        map1.eachLayer(function(layer) {
            if (layer instanceof L.Marker && layer.getLatLng().equals(latlng)) {
                map1.removeLayer(layer);
            }
        });
    });
    marksMap2.forEach(function(latlng) {
        map2.eachLayer(function(layer) {
            if (layer instanceof L.Marker && layer.getLatLng().equals(latlng)) {
                map2.removeLayer(layer);
            }
        });
    });
    marksMap1 = [];
    marksMap2 = [];
});

function addFlashingMarker(map, latlng, colorClass) {
    const marker = L.circleMarker(latlng, {
        radius: 8,
        className: colorClass
    }).addTo(map);
    return marker;
}

function addMarkersToMap(map, marks, colorClass) {
    marks.forEach(function(latlng) {
        addFlashingMarker(map, latlng, colorClass);
    });
}

document.getElementById('collect-marks').addEventListener('click', function() {
    // Log the lengths of marksMap1 and marksMap2
    console.log("marksMap1 length:", marksMap1.length);
    console.log("marksMap2 length:", marksMap2.length);

    // Log the active ortho values
    console.log("activeReferenceOrtho:", activeReferenceOrtho);
    console.log("activeTargetOrtho:", activeTargetOrtho);

    if (marksMap1.length === marksMap2.length && marksMap1.length > 0) {
        if (!activeReferenceOrtho || !activeTargetOrtho) {
            alert('Please select both reference and target orthos.');
            return;
        }

        const data = {
            referenceOrtho: activeReferenceOrtho,
            targetOrtho: activeTargetOrtho,
            originalReferenceOrthoPath: originalReferenceOrthoPath,
            originalTargetOrthoPath: originalTargetOrthoPath,
            marksMap1: marksMap1,
            marksMap2: marksMap2
        };

        // Add flashing markers to the map
        addMarkersToMap(map1, marksMap1, 'flash-red');
        addMarkersToMap(map2, marksMap2, 'flash-green');

        // Print the JSON data to the console
        console.log("Sending the following data to the backend:", JSON.stringify(data, null, 2));

        $.ajax({
            url: '/collect_marks',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                alert('Marks collected and sent to backend.');
            },
            error: function(xhr, status, error) {
                alert('Error: ' + error);
            }
        });
    } else {
        alert('Please ensure both maps have the same number of marks.');
    }
});

const map1 = L.map('map1').setView([20, 0], 2); // Initialize with a global view
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 40,
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map1);

const map2 = L.map('map2').setView([20, 0], 2); // Initialize with a global view
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 40,
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map2);

const layerControl1 = L.control.layers(null, null, { position: 'topright', collapsed: false }).addTo(map1);
const layerControl2 = L.control.layers(null, null, { position: 'topright', collapsed: false }).addTo(map2);