

var map1 = L.map('map1').setView([20, 0], 2);

var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 40,
    attribution: '&copy; OpenStreetMap contributors'
});

osm.addTo(map1);

// Initialize Geoman plugin
map1.pm.addControls({
    position: 'topleft',
    drawPolyline: false,
    drawPolygon: false,
    drawMarker: false,
    drawCircle: false,
    drawCircleMarker: false,
    drawText: false,
    dragMode: true, // Disable default drag mode
    drawRectangle: true, // Add rectangle drawing tool
    editMode: true,
    removalMode: true,
});

// Add custom ruler tool using leaflet-measure plugin
var measureControl = new L.Control.Measure({
    position: 'topleft',
    primaryLengthUnit: 'meters',
    primaryAreaUnit: 'sqmeters',
    activeColor: '#ABE67E',
    completedColor: '#C8F2BE'
});

measureControl.addTo(map1);

const layerControl1 = L.control.layers(null, null, { position: 'topright', collapsed: false }).addTo(map1);

let selectedPolygons = [];
let initialPositions = [];
var geojsonLayer = null; // This will hold the GeoJSON layer
var createdGeoJSON = null; // Variable to store the created GeoJSON



// // Function to load the GeoDataFrame object into the map view
// function loadGdfObject(geojson) {
//     console.log('Received GeoJSON:', geojson);

//     // Clear the existing GeoJSON layer if it exists
//     if (geojsonLayer) {
//         map1.removeLayer(geojsonLayer);
//     }

//     // Load the GeoJSON into the map view
//     geojsonLayer = L.geoJSON(JSON.parse(geojson), {
//         onEachFeature: function (feature, layer) {
//             layer.on('pm:edit', function (e) {
//                 console.log('Feature edited:', e.target.feature);
//                 updateEditedObject(e.target.feature, feature.id);
//             });
//         }
//     }).addTo(map1);

//     // Enable editing on the layer
//     geojsonLayer.eachLayer(function (layer) {
//         layer.pm.enable();
//     });

//     // Store the created GeoJSON
//     createdGeoJSON = geojsonLayer.toGeoJSON();

//     // Log the initial state of the geojsonLayer
//     console.log('Initial geojsonLayer:', geojsonLayer.toGeoJSON());
// }


// function updateEditedObject(editedFeature, originalId) {
//     console.log('Updating GeoJSON for feature:', editedFeature);

//     var geojson = geojsonLayer.toGeoJSON();
//     for (var i = 0; i < geojson.features.length; i++) {
//         if (geojson.features[i].id === originalId) {
//             geojson.features[i].geometry = editedFeature.geometry;
//             geojson.features[i].id = originalId; // Ensure the original ID is retained
//             break;
//         }
//     }

//     createdGeoJSON = geojson;
//     createdGeoJSON.crs = {
//         type: "name",
//         properties: {
//             name: "EPSG:4326"
//         }
//     };

//     console.log('Updated GeoJSON object:', createdGeoJSON);
// }

function loadGdfObject(geojson) {
    console.log('Received GeoJSON:', geojson);

    // Clear the existing GeoJSON layer if it exists
    if (geojsonLayer) {
        map1.removeLayer(geojsonLayer);
    }

    // Load the GeoJSON into the map view
    geojsonLayer = L.geoJSON(JSON.parse(geojson), {
        onEachFeature: function (feature, layer) {
            // Add mouseover event to display attributes
            layer.on('mouseover', function (e) {
                var popupContent = '<b>Attributes:</b><br>';
                for (var key in feature.properties) {
                    popupContent += key + ': ' + feature.properties[key] + '<br>';
                }
                layer.bindPopup(popupContent).openPopup(e.latlng);
            });

            // Add mouseout event to hide the popup
            layer.on('mouseout', function (e) {
                layer.closePopup();
            });

            // Preserve existing pm:edit event
            layer.on('pm:edit', function (e) {
                console.log('Feature edited:', e.target.feature);
                updateEditedObject(e.target.feature, feature.id);
            });
        }
    }).addTo(map1);

    // Enable editing on the layer
    geojsonLayer.eachLayer(function (layer) {
        layer.pm.enable();
    });

    // Store the created GeoJSON
    createdGeoJSON = geojsonLayer.toGeoJSON();

    // Log the initial state of the geojsonLayer
    console.log('Initial geojsonLayer:', geojsonLayer.toGeoJSON());
}

function updateEditedObject(editedFeature, originalId) {
    console.log('Updating GeoJSON for feature:', editedFeature);

    var geojson = geojsonLayer.toGeoJSON();
    for (var i = 0; i < geojson.features.length; i++) {
        if (geojson.features[i].id === originalId) {
            geojson.features[i].geometry = editedFeature.geometry;
            geojson.features[i].id = originalId; // Ensure the original ID is retained
            break;
        }
    }

    createdGeoJSON = geojson;
    createdGeoJSON.crs = {
        type: "name",
        properties: {
            name: "EPSG:4326"
        }
    };

    console.log('Updated GeoJSON object:', createdGeoJSON);
}

// Capture selected polygons
map1.on('pm:create', function (e) {
    if (e.shape === 'Rectangle') {
        var bounds = e.layer.getBounds();
        selectedPolygons = []; // Clear previous selection
        initialPositions = []; // Clear previous initial positions

        geojsonLayer.eachLayer(function (layer) {
            if (bounds.intersects(layer.getBounds())) {
                selectedPolygons.push(layer);
                layer.setStyle({ color: 'red' }); // Highlight selected polygons
            }
        });

        console.log('Selected polygons:', selectedPolygons);

        // Capture initial positions of selected polygons
        initialPositions = selectedPolygons.map(layer =>
            layer.getLatLngs().map(ring => ring.map(latlng => ({ ...latlng })))
        );

        console.log('Initial positions:', initialPositions);

        map1.removeLayer(e.layer); // Remove the rectangle after selection
    }
});


// Add custom button to enable dragging and start dragging for selected polygons
map1.pm.Toolbar.createCustomControl({
    name: 'customDrag',
    block: 'custom',
    title: 'Drag Selected Polygons',
    className: 'leaflet-pm-icon-custom-drag', // Use an existing icon class or create your own
    onClick: function () {
        if (selectedPolygons.length > 0) {
            // Enable dragging for selected polygons
            selectedPolygons.forEach(layer => {
                layer.pm.enable({ draggable: true });
                console.log('Enabled dragging for layer:', layer);
            });

            // Capture the initial positions of all selected polygons on the first click
            const initialClickHandler = function (e) {
                // Capture the initial positions
                initialPositions = selectedPolygons.map(layer =>
                    layer.getLatLngs().map(ring => ring.map(latlng => ({ ...latlng })))
                );

                console.log('Initial positions:', initialPositions);

                // Throttle function to limit the frequency of updates
                function throttle(func, limit) {
                    let lastFunc;
                    let lastRan;
                    return function (...args) {
                        if (!lastRan) {
                            func.apply(this, args);
                            lastRan = Date.now();
                        } else {
                            clearTimeout(lastFunc);
                            lastFunc = setTimeout(() => {
                                if (Date.now() - lastRan >= limit) {
                                    func.apply(this, args);
                                    lastRan = Date.now();
                                }
                            }, limit - (Date.now() - lastRan));
                        }
                    };
                }

                // Function to round latitude and longitude values
                function roundLatLng(latlng, decimals) {
                    return {
                        lat: parseFloat(latlng.lat.toFixed(decimals)),
                        lng: parseFloat(latlng.lng.toFixed(decimals))
                    };
                }

                // Function to update polygon positions based on mouse movement
                const mouseMoveHandler = throttle(function (e) {
                    const targetLatLng = roundLatLng(e.latlng, 10); // Round to 6 decimal places
                    console.log('Mouse move location:', targetLatLng);

                    // Calculate the offset based on the first selected polygon
                    const firstLayer = selectedPolygons[0];
                    const firstLatLng = roundLatLng(firstLayer.getLatLngs()[0][0], 6); // Round to 6 decimal places
                    const offset = {
                        lat: targetLatLng.lat - firstLatLng.lat,
                        lng: targetLatLng.lng - firstLatLng.lng,
                    };

                    console.log('Offset:', offset);

                    // Apply offset to all selected polygons
                    selectedPolygons.forEach((layer, index) => {
                        const newLatLngs = initialPositions[index].map(ring =>
                            ring.map(latlng => ({
                                lat: roundLatLng({ lat: latlng.lat + offset.lat, lng: latlng.lng + offset.lng }, 10).lat,
                                lng: roundLatLng({ lat: latlng.lat + offset.lat, lng: latlng.lng + offset.lng }, 10).lng,
                            }))
                        );
                        layer.setLatLngs(newLatLngs);
                    });

                    console.log('Updated positions for group:', selectedPolygons.map(layer => layer.getLatLngs()));
                }, 10); // Adjust the limit value to control the update frequency

                // Function to finalize the new positions on click
                const mapClickHandler = function (e) {
                    console.log('Final location:', e.latlng);

                    // Update the GeoJSON structure with the new positions
                    selectedPolygons.forEach(layer => {
                        updateEditedObject(layer.toGeoJSON(), layer.feature.id);
                    });

                    // Redraw the polygons with the new positions
                    redrawPolygons();

                    // Clear the selected polygons and reset the dragging state
                    selectedPolygons.forEach(layer => {
                        layer.pm.disable();
                    });
                    selectedPolygons = [];
                    initialPositions = [];

                    // Remove the map event listeners
                    map1.off('mousemove', mouseMoveHandler);
                    map1.off('click', mapClickHandler);
                };

                // Add event listeners for mousemove and click
                map1.on('mousemove', mouseMoveHandler);
                map1.on('click', mapClickHandler);

                // Remove the initial click event listener
                map1.off('click', initialClickHandler);
            };

            // Add initial click event listener to capture initial positions
            map1.on('click', initialClickHandler);
        } else {
            console.log('No polygons selected for dragging');
        }
    }
});

// Function to redraw polygons with updated positions
function redrawPolygons() {
    // Clear the existing GeoJSON layer
    if (geojsonLayer) {
        map1.removeLayer(geojsonLayer);
    }

    // Reload the GeoJSON into the map view with updated positions
    geojsonLayer = L.geoJSON(createdGeoJSON, {
        onEachFeature: function (feature, layer) {
            layer.on('pm:edit', function (e) {
                console.log('Feature edited:', e.target.feature);
                updateEditedObject(e.target.feature, feature.id);
            });
        }
    }).addTo(map1);

    // Enable editing on the layer
    geojsonLayer.eachLayer(function (layer) {
        layer.pm.enable();
    });

    console.log('Redrawn polygons with updated positions:', geojsonLayer.toGeoJSON());
}


// Add custom button to enable rotating and start rotating for selected polygons
map1.pm.Toolbar.createCustomControl({
    name: 'customRotate',
    block: 'custom',
    title: 'Rotate Selected Polygons',
    className: 'leaflet-pm-icon-custom-rotate', // Use an existing icon class or create your own
    onClick: function () {
        if (selectedPolygons.length > 0) {
            // Enable rotating for selected polygons
            selectedPolygons.forEach(layer => {
                layer.pm.enable({ draggable: true });
                console.log('Enabled rotating for layer:', layer);
            });

            // Capture the initial positions of all selected polygons on the first click
            const initialClickHandler = function (e) {
                // Capture the initial positions
                initialPositions = selectedPolygons.map(layer =>
                    layer.getLatLngs().map(ring => ring.map(latlng => ({ ...latlng })))
                );

                console.log('Initial positions:', initialPositions);

                // Function to calculate the angle between two points
                function calculateAngle(start, end) {
                    return Math.atan2(end.lat - start.lat, end.lng - start.lng);
                }

                // Function to rotate a point around a center
                function rotatePoint(point, angle, center) {
                    const sin = Math.sin(angle);
                    const cos = Math.cos(angle);
                    const dx = point.lng - center.lng;
                    const dy = point.lat - center.lat;
                    return {
                        lat: center.lat + (dy * cos - dx * sin),
                        lng: center.lng + (dx * cos + dy * sin)
                    };
                }

                // Function to round values to a fixed number of decimal places
                function roundValue(value, decimals) {
                    return parseFloat(value.toFixed(decimals));
                }

                // Function to round angle to the nearest increment (e.g., 1 degree)
                function roundAngleToIncrement(angle, increment) {
                    const degrees = angle * (180 / Math.PI);
                    const roundedDegrees = Math.round(degrees / increment) * increment;
                    return roundedDegrees * (Math.PI / 180);
                }

                // Throttle function to limit the frequency of updates
                function throttle(func, limit) {
                    let lastFunc;
                    let lastRan;
                    return function (...args) {
                        if (!lastRan) {
                            func.apply(this, args);
                            lastRan = Date.now();
                        } else {
                            clearTimeout(lastFunc);
                            lastFunc = setTimeout(() => {
                                if (Date.now() - lastRan >= limit) {
                                    func.apply(this, args);
                                    lastRan = Date.now();
                                }
                            }, limit - (Date.now() - lastRan));
                        }
                    };
                }

                // Function to update polygon positions based on mouse movement
                const mouseMoveHandler = throttle(function (e) {
                    const targetLatLng = e.latlng;
                    console.log('Mouse move location:', targetLatLng);

                    // Calculate the angle based on the first selected polygon
                    const firstLayer = selectedPolygons[0];
                    const firstLatLng = firstLayer.getLatLngs()[0][0];
                    const initialAngle = calculateAngle(firstLatLng, initialPositions[0][0][0]);
                    const currentAngle = calculateAngle(firstLatLng, targetLatLng);
                    const angle = roundAngleToIncrement(currentAngle - initialAngle, 1); // Round to nearest 1 degree

                    console.log('Angle:', angle);

                    // Apply rotation to all selected polygons
                    selectedPolygons.forEach((layer, index) => {
                        const newLatLngs = initialPositions[index].map(ring =>
                            ring.map(latlng => {
                                const rotatedPoint = rotatePoint(latlng, angle, firstLatLng);
                                return {
                                    lat: roundValue(rotatedPoint.lat, 6),
                                    lng: roundValue(rotatedPoint.lng, 6),
                                };
                            })
                        );
                        layer.setLatLngs(newLatLngs);
                    });

                    console.log('Updated positions for group:', selectedPolygons.map(layer => layer.getLatLngs()));
                }, 50); // Adjust the limit value to control the update frequency

                // Function to finalize the new positions on click
                const mapClickHandler = function (e) {
                    console.log('Final location:', e.latlng);

                    // Update the GeoJSON structure with the new positions
                    selectedPolygons.forEach(layer => {
                        updateEditedObject(layer.toGeoJSON(), layer.feature.id);
                    });

                    // Redraw the polygons with the new positions
                    redrawPolygons();

                    // Clear the selected polygons and reset the rotating state
                    selectedPolygons.forEach(layer => {
                        layer.pm.disable();
                    });
                    selectedPolygons = [];
                    initialPositions = [];

                    // Remove the map event listeners
                    map1.off('mousemove', mouseMoveHandler);
                    map1.off('click', mapClickHandler);
                };

                // Add event listeners for mousemove and click
                map1.on('mousemove', mouseMoveHandler);
                map1.on('click', mapClickHandler);

                // Remove the initial click event listener
                map1.off('click', initialClickHandler);
            };

            // Add initial click event listener to capture initial positions
            map1.on('click', initialClickHandler);
        } else {
            console.log('No polygons selected for rotating');
        }
    }
});

// Function to redraw polygons with updated positions
function redrawPolygons() {
    // Clear the existing GeoJSON layer
    if (geojsonLayer) {
        map1.removeLayer(geojsonLayer);
    }

    // Reload the GeoJSON into the map view with updated positions
    geojsonLayer = L.geoJSON(createdGeoJSON, {
        onEachFeature: function (feature, layer) {
            layer.on('pm:edit', function (e) {
                console.log('Feature edited:', e.target.feature);
                updateEditedObject(e.target.feature, feature.id);
            });
        }
    }).addTo(map1);

    // Enable editing on the layer
    geojsonLayer.eachLayer(function (layer) {
        layer.pm.enable();
    });

    console.log('Redrawn polygons with updated positions:', geojsonLayer.toGeoJSON());
}
// Function to redraw polygons with updated positions
function redrawPolygons() {
    // Clear the existing GeoJSON layer
    if (geojsonLayer) {
        map1.removeLayer(geojsonLayer);
    }

    // Reload the GeoJSON into the map view with updated positions
    geojsonLayer = L.geoJSON(createdGeoJSON, {
        onEachFeature: function (feature, layer) {
            layer.on('pm:edit', function (e) {
                console.log('Feature edited:', e.target.feature);
                updateEditedObject(e.target.feature, feature.id);
            });
        }
    }).addTo(map1);

    // Enable editing on the layer
    geojsonLayer.eachLayer(function (layer) {
        layer.pm.enable();
    });

    console.log('Redrawn polygons with updated positions:', geojsonLayer.toGeoJSON());
}

// Add custom CSS for the custom drag icon and label
const style = document.createElement('style');

function getEditedObject() {
    // Return the actual edited object
    if (geojsonLayer) {
        console.log('GeoJSON Layer:', geojsonLayer.toGeoJSON());
    } else {
        console.log('GeoJSON Layer is not set.');
    }
    return geojsonLayer ? geojsonLayer.toGeoJSON() : {};
}

// Reference to the search polygon layer
var searchPolygonLayer;

// Add search control
L.Control.geocoder({
    position: 'topleft',
    defaultMarkGeocode: false
}).on('markgeocode', function(e) {
    var bbox = e.geocode.bbox;

    // Check if there is an existing polygon and remove it
    if (searchPolygonLayer) {
        map1.removeLayer(searchPolygonLayer);
    }

    // Create a new polygon for the search result
    searchPolygonLayer = L.polygon([
        [bbox.getSouthEast().lat, bbox.getSouthEast().lng],
        [bbox.getNorthEast().lat, bbox.getNorthEast().lng],
        [bbox.getNorthWest().lat, bbox.getNorthWest().lng],
        [bbox.getSouthWest().lat, bbox.getSouthWest().lng]
    ]).addTo(map1);

    // Zoom to the polygon
    map1.fitBounds(searchPolygonLayer.getBounds());
}).addTo(map1);

// Listen to the zoomend event and remove the search polygon layer
map1.on('zoomend', function() {
    if (searchPolygonLayer) {
        map1.removeLayer(searchPolygonLayer);
        searchPolygonLayer = null;
    }
});

// Reset function for selected polygons
window.resetSelectedPolygons = function() {
    selectedPolygons.forEach(layer => {
        layer.setStyle({ color: layer.options.originalColor }); // Reset to original color
        layer.pm.disable(); // Disable dragging
    });
    selectedPolygons = [];
    initialPositions = [];

    // Reload the stored GeoJSON
    if (createdGeoJSON) {
        loadGdfObject(JSON.stringify(createdGeoJSON));
    }
};

// Define a custom icon for the dot markers
const dotIcon = L.divIcon({
    className: 'custom-dot-icon',
    html: '<div style="width: 8px; height: 8px; background-color: red; border-radius: 50%;"></div>',
    iconSize: [8, 8],
    iconAnchor: [4, 4]
});

// Event listeners for buttons
document.getElementById('upload-button').addEventListener('click', function() {
    document.getElementById('folder-input').click();
});

document.getElementById('folder-input').addEventListener('change', function(event) {
    const folderPath = event.target.files[0].webkitRelativePath.split('/')[0];
    document.getElementById('loading-message1').style.display = 'block';
    $.post('/process_images', { input_folder: folderPath }, function(data) {
        let imagesLoaded = 0;
        const totalImages = data.length;

        data.forEach(item => {
            if (item.png_path && item.bounds) {
                const bounds = item.bounds;
                const imageUrl = item.png_path;
                const layer = L.imageOverlay(imageUrl, bounds);

                layer.on('load', function() {
                    imagesLoaded++;
                    if (imagesLoaded === totalImages) {
                        document.getElementById('loading-message1').style.display = 'none';
                    }
                });

                layer.addTo(map1);

                // Extract the base name of the ortho_path
                const baseName = item.ortho_path.split('/').pop();
                // Split the base name by underscores and extract the second and third strings
                const parts = baseName.split('_');
                const displayName = parts[2] + '_' + parts[3];

                const option = new Option(displayName, item.ortho_path);
                $(option).data('original-ortho-path', item.original_ortho_path);
                $('#ortho-select').append(option);
                
                // Set the name property for the layer to the displayName
                layer.name = displayName;
                // Store the full path as a custom property
                layer.fullPath = item.ortho_path;
                layerControl1.addOverlay(layer, displayName);

                // Debugging: Log the layer name and displayName
                console.log('Added layer:', layer.fullPath, displayName);
            }
        });

        // Debugging: Log the layers in layerControl1
        console.log('Layers in layerControl1:', layerControl1._layers);
    });
});


// Dropdown selectors for ortho images
document.getElementById('ortho-select').addEventListener('change', function() {
    activeReferenceOrtho = this.value;
    const selectedOption = $('#ortho-select option:selected');
    originalReferenceOrthoPath = selectedOption.data('original-ortho-path');

    // Debugging: Log the activeReferenceOrtho
    console.log('Selected ortho:', activeReferenceOrtho);

    // Zoom to the selected reference ortho
    const selectedLayer = Object.values(layerControl1._layers).find(layer => layer.layer.fullPath === activeReferenceOrtho);
    if (selectedLayer) {
        map1.fitBounds(selectedLayer.layer.getBounds());
    } else {
        // Debugging: Log if the layer is not found
        console.log('Layer not found for:', activeReferenceOrtho);
    }
});

// var initialCorner = null;
// var directionPoint = null;

// document.getElementById('capture-coords-button').addEventListener('click', function() {
//     map1.on('click', function(e) {
//         if (!initialCorner) {
//             initialCorner = e.latlng;
//             L.marker(initialCorner, { icon: dotIcon }).addTo(map1).bindPopup('Initial Corner').openPopup();
//             alert('Initial corner set. Now click to set the direction point.');
//         } else if (!directionPoint) {
//             directionPoint = e.latlng;
//             L.marker(directionPoint, { icon: dotIcon }).addTo(map1).bindPopup('Direction Point').openPopup();
//             alert('Direction point set. Coordinates captured successfully.');
//             map1.off('click'); // Remove the click event listener after capturing both points
//         }
//     });
// });

// // Function to reset markers
// function resetMarkers() {
//     initialCorner = null;
//     directionPoint = null;
//     console.log('Markers reset');
//     // Additional code to remove markers from the map if needed
// }

var initialCornerMarker = null;
var directionPointMarker = null;

document.getElementById('capture-coords-button').addEventListener('click', function() {
    map1.on('click', function(e) {
        if (!initialCorner) {
            initialCorner = e.latlng;
            initialCornerMarker = L.marker(initialCorner, { icon: dotIcon }).addTo(map1).bindPopup('Initial Corner').openPopup();
            alert('Initial corner set. Now click to set the direction point.');
        } else if (!directionPoint) {
            directionPoint = e.latlng;
            directionPointMarker = L.marker(directionPoint, { icon: dotIcon }).addTo(map1).bindPopup('Direction Point').openPopup();
            alert('Direction point set. Coordinates captured successfully.');
            map1.off('click'); // Remove the click event listener after capturing both points
        }
    });
});

// Function to reset markers
function resetMarkers() {
    initialCorner = null;
    directionPoint = null;
    if (initialCornerMarker) {
        map1.removeLayer(initialCornerMarker);
        initialCornerMarker = null;
    }
    if (directionPointMarker) {
        map1.removeLayer(directionPointMarker);
        directionPointMarker = null;
    }
    console.log('Markers reset');
}

// Reset markers
document.getElementById('reset-button').addEventListener('click', function() {
    resetMarkers();
});

// Submit form data
document.getElementById('submit-button').addEventListener('click', function() {
    // Retrieve form data
    const plotWidth = document.getElementById('plot-width').value;
    const plotLength = document.getElementById('plot-length').value;
    const plotsHorizontalGap = document.getElementById('plots-horizontal-gap').value;
    const plotsVerticalGap = document.getElementById('plots-vertical-gap').value;
    const numPolygons = document.getElementById('num-polygons').value;
    const numHorizontalPolygons = document.getElementById('num-horizontal-polygons').value;
    const plotDirection = document.getElementById('plot-direction').value;
    const numBlocks = document.getElementById('num-blocks').value;
    const alleyWidth = document.getElementById('alley-width').value;
    const reversePlotDirection = document.getElementById('reverse_plot_direction').checked;
    const multiBlockTrial = document.getElementById('multiblock_trial_design').checked;


    // Validate required fields
    if (!plotWidth || !plotLength || !plotsHorizontalGap || !plotsVerticalGap || !numPolygons || !numHorizontalPolygons || !plotDirection) {
        alert('Please fill in all required fields.');
        return;
    }

    // Validate optional fields if block design is selected
    if (plotDirection === 'block' && (!numBlocks || !alleyWidth)) {
        alert('Please provide number of blocks and alley width for block design.');
        return;
    }

    // Prepare form data
    const formData = {
        plot_width: plotWidth,
        plot_length: plotLength,
        plots_horizontal_gap: plotsHorizontalGap,
        plots_vertical_gap: plotsVerticalGap,
        num_polygons: numPolygons,
        num_horizontal_polygons: numHorizontalPolygons,
        plot_direction: plotDirection,
        num_blocks: numBlocks,
        alley_width: alleyWidth,
        initial_corner: initialCorner ? `${initialCorner.lat},${initialCorner.lng}` : null,
        direction_point: directionPoint ? `${directionPoint.lat},${directionPoint.lng}` : null,
        reverse_plot_direction: reversePlotDirection,
        multiblock_trial_design: multiBlockTrial 
    };

    // Print form data for pre-check
    const formDataString = JSON.stringify(formData, null, 2);
    console.log(`Please confirm the form data:\n\n${formDataString}`);
    const userConfirmed = confirm(`Please confirm the form data:\n\n${formDataString}`);

    if (userConfirmed) {
        // Send form data to the backend
        $.ajax({
            url: '/create_field_trial',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                console.log('Field trial created successfully.');

                // Add the GeoJSON data to the map using loadGdfObject
                loadGdfObject(response.geojson);

                // Reset the markers
                // resetMarkers();
            },
            error: function() {
                alert('Failed to create field trial.');
            }
        });
    } else {
        alert('Form submission canceled.');
    }
});

// Event listener for the reset mark button

// Event listener for the zoom to active layer extent button
document.getElementById('zoom-active').addEventListener('click', function() {
    const activeReferenceOrtho = document.getElementById('ortho-select').value;
    const selectedLayer = Object.values(layerControl1._layers).find(layer => layer.layer.fullPath === activeReferenceOrtho);
    if (selectedLayer) {
        map1.fitBounds(selectedLayer.layer.getBounds());
    } else {
        alert('Active layer not found.');
    }
});

// Save edited object
document.getElementById('save-edited-object-button').addEventListener('click', function() {
    // Retrieve the edited object
    var editedObject = getEditedObject();

    // Check if originalReferenceOrthoPath is null
    if (!originalReferenceOrthoPath) {
        alert('Original ortho path is not set.');
        return;
    }

    // Prepare the data to be sent to the backend
    var data = {
        ortho: activeReferenceOrtho,
        original_ortho_path: originalReferenceOrthoPath,
        object: editedObject
    };

    // Log the data to be sent
    console.log('Data to be sent:', data);

    // Send the data to the backend using an AJAX request
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/save-edited-object', true);
    xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            console.log('Response status:', xhr.status);
            console.log('Response text:', xhr.responseText);
            if (xhr.status === 200) {
                alert('Object saved successfully!');
            } else {
                alert('Error saving object.');
            }
        }
    };
    xhr.send(JSON.stringify(data));
});

// // Reset markers
// document.getElementById('reset-button').addEventListener('click', function() {
//     resetMarkers();
// });

// Reset selected polygons
document.getElementById('reset-selected-button').addEventListener('click', function() {
    resetSelectedPolygons();
});



