let selectedResults = {};
let plotColors = {}; // Global object to store plot colors
let dateColors = {}; // Global object to store colors for each Date_julian

let allResults = null; // Global variable to store all plots data
let selectedPlots = []; // Array to store selected plots' order ID and GeoJSON path


function getSelectedDataset(result, trait) {
    const datasets = [];

    // Extract unique Date_julian values for labels
    const labels = [...new Set(result.map(item => String(item.Date_julian)))];

    // Group data by Date_julian and barcode
    const barCodes = [...new Set(result.map(item => item.barcode))];
    barCodes.forEach(barCode => {
        const data = labels.map(date => {
            const entry = result.find(item => String(item.Date_julian) === date && item.barcode === barCode);
            return entry ? entry[trait] : 0;
        });
        if (!plotColors[barCode]) {
            plotColors[barCode] = getRandomColor();
        }
        datasets.push({
            label: `Plot ${barCode}`,
            data: data,
            backgroundColor: plotColors[barCode] + '80', // Add transparency
            borderColor: plotColors[barCode],
            borderWidth: 1,
            fill: false // Do not fill the area under the line
        });
    });

    return { labels, datasets };
}

function updateChart(result, yVariable = 'Band_6_max') {
    const ctx = document.getElementById('resultChart').getContext('2d');
    
    // Get the dataset using the selected y variable
    const { labels, datasets } = getSelectedDataset(result, yVariable);

    // Calculate the min and max values for the x-axis
    const minDateJulian = Math.min(...labels.map(Number));
    const maxDateJulian = Math.max(...labels.map(Number));

    console.log('minimum and maximum values are: ', minDateJulian, maxDateJulian);

    // Check if window.resultChart is already initialized
    if (window.resultChart) {
        if (typeof window.resultChart.destroy === 'function') {
            window.resultChart.destroy();
        } else {
            console.error('window.resultChart.destroy is not a function');
        }
    }

    // Mapping of Y variable names to display names
    const yVariableDisplayNames = {
        'Band_6_max': 'Canopy height (m)',
        'NDVI_max': 'NDVI',
        'NDRE_max': 'NDRE',
        'fcover': 'Fraction cover (%)'
    };

    // Get the display name for the selected Y variable
    const yVariableDisplayName = yVariableDisplayNames[yVariable] || yVariable;

    // Create the new chart instance with grouped data by plotID
    window.resultChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels, // X-axis: unique `Date_julian` as strings
            datasets: datasets
        },
        options: {
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    suggestedMin: minDateJulian - 5,
                    suggestedMax: maxDateJulian + 5,
                    title: {
                        display: true,
                        text: 'Julian Date (day)',
                        font: {
                            size: 16 // Increase font size of x-axis label
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: yVariableDisplayName,
                        font: {
                            size: 16 // Increase font size of y-axis label
                        }
                    }
                }
            },
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14 // Increase font size of legend
                        }
                    }
                }
            }
        }
    });

        // Store the result data for later use
        window.resultChart.data.result = result;

        // Update the histogram chart with all plots data
        if (allResults) {
            updateHistogramChart(allResults, yVariable);
        }
    }


function updateHistogramChart(result, yVariable) {
        const ctx = document.getElementById('histogramChart').getContext('2d');
    
        // Group data by Julian date
        const groupedData = result.reduce((acc, item) => {
            const date = item.Date_julian;
            if (!acc[date]) {
                acc[date] = [];
            }
            acc[date].push(item);
            return acc;
        }, {});
    
        // Define the number of bins for the histogram
        const numBins = 10;
    
        // Calculate the min and max values of the data
        const minValue = Math.min(...result.map(item => item[yVariable]));
        const maxValue = Math.max(...result.map(item => item[yVariable]));
    
        // Calculate the bin width
        const binWidth = (maxValue - minValue) / numBins;
    
        // Initialize the datasets for the histogram
        const datasets = [];
    
        // Generate a color palette for the datasets if not already generated
        if (Object.keys(dateColors).length === 0) {
            const uniqueDates = Object.keys(groupedData);
            uniqueDates.forEach(date => {
                dateColors[date] = getRandomColor();
            });
        }
            // Create a dataset for each Julian date
            Object.keys(groupedData).forEach((date, index) => {
                const data = groupedData[date].map(item => item[yVariable]);
        
                // Initialize the bins for this date
                const bins = Array(numBins).fill(0);
        
                // Populate the bins with frequency counts
                data.forEach(value => {
                    const binIndex = Math.min(Math.floor((value - minValue) / binWidth), numBins - 1);
                    bins[binIndex]++;
                });
        
                // Add the dataset for this date
                datasets.push({
                    label: `Julian Date: ${date}`,
                    data: bins,
                    backgroundColor: dateColors[date] + '80', // Add transparency
                    borderColor: dateColors[date],
                    borderWidth: 1
                });
            });
        
            // Highlight bins containing selected plots
            const selectedBins = new Map();
            selectedPlots.forEach(plot => {
                const plotData = result.filter(item => item.plotID === plot.orderID);
                plotData.forEach(item => {
                    const binIndex = Math.min(Math.floor((item[yVariable] - minValue) / binWidth), numBins - 1);
                    if (!selectedBins.has(binIndex)) {
                        selectedBins.set(binIndex, []);
                    }
                    selectedBins.get(binIndex).push(`Plot ${item.plotID} (Date: ${item.Date_julian})`);
                });
            });
            
        // Check if window.histogramChart is already initialized
        if (window.histogramChart) {
            if (typeof window.histogramChart.destroy === 'function') {
                window.histogramChart.destroy();
            } else {
                console.error('window.histogramChart.destroy is not a function');
            }
        }
    
        // Mapping of Y variable names to display names
        const yVariableDisplayNames = {
            'Band_6_max': 'Canopy height (m)',
            'NDVI_max': 'NDVI',
            'NDRE_max': 'NDRE',
            'fcover': 'Fraction cover (%)'
        };
    
        // Get the display name for the selected Y variable
        const yVariableDisplayName = yVariableDisplayNames[yVariable] || yVariable;
    
        // Create the new histogram chart instance
        window.histogramChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: datasets[0].data.map((_, index) => {
                    const rangeStart = minValue + index * binWidth;
                    const rangeEnd = rangeStart + binWidth;
                    return `${rangeStart.toFixed(2)} - ${rangeEnd.toFixed(2)}`;
                }),
                datasets: datasets
            },
            options: {
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: yVariableDisplayName,
                            font: {
                                size: 16 // Increase font size of x-axis label
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Frequency Count',
                            font: {
                                size: 16 // Increase font size of y-axis label
                            }
                        }
                    }
                },
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 14 // Increase font size of legend
                            }
                        }
                    },
                    annotation: {
                        annotations: selectedBins.size > 0 ? Array.from(selectedBins.entries()).map(([binIndex, plotIDs]) => ({
                            type: 'label',
                            xValue: binIndex,
                            yValue: datasets[0].data[binIndex],
                            backgroundColor: 'rgba(255, 99, 132, 0.25)',
                            borderColor: 'rgba(255, 99, 132, 1)',
                            borderWidth: 2,
                            content: plotIDs.join(', '),
                            position: 'center',
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        })) : []
                    }
                }
            }
        });
    }
    

// Function to generate a color palette
function generateColorPalette(numColors) {
    const colors = [];
    for (let i = 0; i < numColors; i++) {
        colors.push(getRandomColor());
    }
    return colors;
}

// Function to generate a random color
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

document.addEventListener('DOMContentLoaded', function() {
    var map1 = L.map('map1').setView([20, 0], 2);

    var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 40,
        attribution: '&copy; OpenStreetMap contributors'
    });
    
    osm.addTo(map1);

    // Initialize Geoman plugin
    map1.pm.addControls({
        position: 'topleft',
        drawMarker: true,
        drawPolygon: true,
        drawPolyline: true,
        editMode: true,
        removalMode: true,
    });

    // Add custom ruler tool using leaflet-measure plugin
    var measureControl = new L.Control.Measure({
        position: 'topleft',
        primaryLengthUnit: 'meters',
        secondaryLengthUnit: 'kilometers',
        primaryAreaUnit: 'sqmeters',
        secondaryAreaUnit: 'hectares',
        activeColor: '#ABE67E',
        completedColor: '#C8F2BE'
    });
    measureControl.addTo(map1);

    // Create layer groups for PNG and GeoJSON layers
    const pngLayerGroup = L.layerGroup().addTo(map1);
    const geojsonLayerGroup = L.layerGroup().addTo(map1);

    const layerControl1 = L.control.layers(null, null, { position: 'topright', collapsed: false }).addTo(map1);
    L.DomUtil.addClass(layerControl1.getContainer(), 'custom-layer-control');

    // // Add custom group names to the layer control
    // addGroupNameToLayerControl(layerControl1, 'PNG Layers');
    // addGroupNameToLayerControl(layerControl1, 'GeoJSON Layers');

    // // Function to add group name to layer control
    // function addGroupNameToLayerControl(layerControl, groupName) {
    //     const container = layerControl.getContainer();
    //     const groupLabel = document.createElement('div');
    //     groupLabel.className = 'group-label';
    //     groupLabel.innerText = groupName;
    //     container.appendChild(groupLabel);
    // }

    window.onload = function() {
        // Initialize empty charts
        initializeEmptyCharts();
    };


    // Function to initialize empty charts
    function initializeEmptyCharts() {
        const ctxResult = document.getElementById('resultChart').getContext('2d');
        const ctxHistogram = document.getElementById('histogramChart').getContext('2d');
    
    
        const emptyMessagePlugin = {
            id: 'emptyMessage',
            beforeDraw: function(chart) {
                const ctx = chart.ctx;
                const width = chart.width;
                const height = chart.height;
                ctx.save();
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.font = '16px Arial';
                ctx.fillStyle = 'gray';
                ctx.fillText('Load data for plotting', width / 2, height / 2);
                ctx.restore();
            }
        };
    
        window.resultChart = new Chart(ctxResult, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: {
                            display: true,
                            text: 'Julian Date (day)',
                            font: {
                                size: 16
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Value',
                            font: {
                                size: 16
                            }
                        }
                    }
                },
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 14
                            }
                        }
                    },
                    emptyMessage: emptyMessagePlugin
                }
            }
        });
    
        window.histogramChart = new Chart(ctxHistogram, {
            type: 'bar',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Value Ranges',
                            font: {
                                size: 16
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Frequency Count',
                            font: {
                                size: 16
                            }
                        }
                    }
                },
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            font: {
                                size: 14
                            }
                        }
                    },
                    emptyMessage: emptyMessagePlugin
                }
            }
        });
    }
    

    // Function to handle file upload
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
                    //layer.addTo(pngLayerGroup);
    
                    // Extract the base name of the ortho_path
                    const baseName = item.ortho_path.split('/').pop();
                    // Split the base name by underscores and extract the second and third strings
                    const parts = baseName.split('_');
                    const displayName = parts[2] + '_' + parts[3];
    
                    const option = new Option(displayName, item.ortho_path);
                    $(option).data('original-ortho-path', item.original_ortho_path);
                    $('#ortho-select').append(option);
                    layer.fullPath = item.ortho_path;
                    layerControl1.addOverlay(layer, displayName);
                }
            });
    
            // Load GeoJSON files after processing images
            loadGeoJSONFiles();
        });
    });
    

    // Dropdown selectors for ortho images
    document.getElementById('ortho-select').addEventListener('change', function() {
        activeReferenceOrtho = this.value;
        const selectedOption = $('#ortho-select option:selected');
        originalReferenceOrthoPath = selectedOption.data('original-ortho-path');

        // Debugging: Log the activeReferenceOrtho
        console.log('Selected ortho:', activeReferenceOrtho);

        // Print all layers' full paths for debugging
        console.log('All layers in layerControl1:');
        Object.values(layerControl1._layers).forEach(layer => {
            console.log('Layer name:', layer.name, 'Full path:', layer.layer.fullPath);
        });

        // Zoom to the selected reference ortho
        const selectedLayer = Object.values(layerControl1._layers).find(layer => layer.layer.fullPath === activeReferenceOrtho);
        if (selectedLayer) {
            map1.fitBounds(selectedLayer.layer.getBounds());
        } else {
            // Debugging: Log if the layer is not found
            console.log('Layer not found for:', activeReferenceOrtho);
        }
    });

    
    document.getElementById('shp-select').addEventListener('change', function() {
        activeReferenceSHP = this.value;
    
        // Send the active SHP file to the backend to get accessions
        fetch('/get-accessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ shp_file: activeReferenceSHP })
        })
        .then(response => response.json())
        .then(result => {
            updateAccessionList(result.accessions); // Update the accession list
            window.shpFile = result.shp_file; // Store the shp_file globally
        })
        .catch(error => console.error('Error:', error));
    });

    // Function to update the accession list
    function updateAccessionList(accessions) {
        const accessionList = document.getElementById('accession-items');
        accessionList.innerHTML = ''; // Clear the existing list

        accessions.forEach(accession => {
            const listItem = document.createElement('li');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = accession;
            checkbox.id = `accession-${accession}`;

            const label = document.createElement('label');
            label.htmlFor = `accession-${accession}`;
            label.textContent = accession;

            listItem.appendChild(checkbox);
            listItem.appendChild(label);
            accessionList.appendChild(listItem);
        });
    }

    // Function to get selected accessions
    function getSelectedAccessions() {
        const checkboxes = document.querySelectorAll('#accession-items input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(checkbox => checkbox.value);
    }


    // Add event listener to send selected polygons button
    document.getElementById('send-selected-polygons').addEventListener('click', function() {
        console.log('Button clicked'); // Test log to verify the event listener
        sendSelectedPolygons();
    });

    let geojsonLayers = {}; // Object to store GeoJSON layers by filename
    let selectedLayers = []; // Array to store selected layers
    let selectedPlots = []; // Array to store selected plots' order ID and GeoJSON path

    // Function to reset colors of all selected polygons and clear the selected plots list
    window.resetSelectedPolygons = function() {
        // Clear the selected layers and plots
        selectedLayers.forEach(layer => {
            layer.setStyle({
                color: 'blue' // Reset to original color or any default color
            });
        });
        selectedLayers = [];
        selectedPlots = [];
        //updateSelectedPlotsDisplay();

        // Clear all GeoJSON layers from the map
        clearGeoJSONLayers();

        // Clear the shp-select dropdown to prevent duplication
        const shpSelect = document.getElementById("shp-select");
        shpSelect.innerHTML = '';

        // Reload the GeoJSON files
        loadGeoJSONFiles();

        initializeEmptyCharts();
    }

    // Function to clear all GeoJSON layers from the map
    function clearGeoJSONLayers() {
        for (const file in geojsonLayers) {
            map1.removeLayer(geojsonLayers[file]);
            layerControl1.removeLayer(geojsonLayers[file]);
        }
        geojsonLayers = {};
    }



    function loadGeoJSONFiles() {
        console.log('loadGeoJSONFiles function called'); // Log to indicate the function is called
    
        // Clear the shp-select dropdown to prevent duplication
        const shpSelect = document.getElementById("shp-select");
        shpSelect.innerHTML = '';
    
        // Load all .shifted.geojson files from Flask backend
        fetch('/list-geojson-files')
            .then(response => {
                console.log('Fetch /list-geojson-files response:', response); // Log the response
                return response.json();
            })
            .then(files => {
                console.log('Files received:', files); // Log the files received
                files.forEach(file => {
                    // Fetch and add GeoJSON to the map
                    fetch(`/reprojected-geojson/${file}`)
                        .then(response => {
                            console.log(`Fetch /reprojected-geojson/${file} response:`, response); // Log the response
                            return response.json();
                        })
                        .then(data => {
                            console.log(`Data for ${file}:`, data); // Log the data received
                            const layer = L.geoJSON(data, {
                                onEachFeature: function (feature, layer) {
                                    layer.on('mouseover', function (e) {
                                        const properties = feature.properties;
                                        let popupContent = '<div>';
                                        for (let key in properties) {
                                            popupContent += `<strong>${key}:</strong> ${properties[key]}<br>`;
                                        }
                                        popupContent += '</div>';
                                        layer.bindPopup(popupContent).openPopup();
                                    });
    
                                    layer.on('mouseout', function (e) {
                                        // Close the popup
                                        layer.closePopup();
                                    });
    
                                    layer.on('click', function (e) {
                                        const properties = feature.properties;
                                        const orderID = properties.order; // Assuming 'order' is the property name
                                        const geojsonPath = file;
    
                                        // Check if the layer is already selected
                                        const index = selectedLayers.indexOf(layer);
                                        if (index === -1) {
                                            // Change polygon color on click
                                            layer.setStyle({
                                                color: 'red'
                                            });
    
                                            // Add to selected layers and plots
                                            selectedLayers.push(layer);
                                            selectedPlots.push({ orderID, geojsonPath });
    
                                            // Print the new plot added to the list
                                            console.log(`New plot added: Order ID: ${orderID}, GeoJSON Path: ${geojsonPath}`);
    
                                            // Print the updated list
                                            console.log('Updated list of selected plots:', selectedPlots);
    
                                            // Update the front end with the new plot and updated list
                                            //updateSelectedPlotsDisplay();
                                        }
                                    });
                                }
                            }).addTo(map1);
                            //}).addTo(geojsonLayerGroup);
                            geojsonLayers[file] = layer;
    
                            // Extract the base name of the GeoJSON file
                            const baseName = file.split(/[/\\]/).pop();
                            
                            console.log('base name is', baseName);
                            // Split the base name by underscores and extract the second and third strings
                            const parts = baseName.split('_');
                            //const displayName = parts.slice(1, 3).join('_');

                            const displayName = parts[1] + '_' + parts[2];
    
                            console.log('display name is', displayName);
    
                            // Add to shp-select dropdown
                            const option = new Option(displayName, file);
                            shpSelect.appendChild(option);
    
                            // Add to layer control
                            //layerControl1.addOverlay(layer, displayName);
    
                            // Optionally, adjust the map view to fit the loaded GeoJSON
                            map1.fitBounds(layer.getBounds());
                        })
                        .catch(error => console.error('Error loading GeoJSON:', error));
                });
            })
            .catch(error => console.error('Error fetching list of GeoJSON files:', error));
    }

    // Function to send selected polygons and accessions to the backend
    function sendSelectedPolygons() {
        console.log('hello'); // Print hello when the button is clicked

        if (selectedPlots.length === 0 && getSelectedAccessions().length === 0) {
            console.error('No plots or accessions selected');
            return;
        }

        const data = {
            selectedPlots: selectedPlots.length > 0 ? selectedPlots : null,
            selectedAccessions: getSelectedAccessions().length > 0 ? getSelectedAccessions() : null,
            shp_file: window.shpFile // Include the shp_file
        };

        console.log('Sending selected data to the backend:', data);

        // Fetch selected polygons data
        fetch('/process-selected-polygons', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            console.log('Statistics:', result);
            selectedResults = JSON.parse(result.selected_plots); // Store the selected plots data in the global results object
            console.log('Results:', selectedResults);
            allResults = JSON.parse(result.all_plots); // Store the all plots data in the global allPlotsResult object
            console.log('ALL Results:', allResults);
            updateChart(selectedResults, 'Band_6_max');
            updateHistogramChart(allResults, 'Band_6_max');

            // Check if filtered_geojson is provided in the response
            if (result.filtered_geojson) {
                const filteredGeoJSON = JSON.parse(result.filtered_geojson);
                if (filteredGeoJSON.type === 'FeatureCollection' && Array.isArray(filteredGeoJSON.features)) {
                    reloadGeoJSONLayer(filteredGeoJSON);
                    console.log('Filtered GeoJSON:', filteredGeoJSON);
                } else {
                    console.error('Invalid GeoJSON format:', filteredGeoJSON);
                }
            }
        })
        .catch(error => console.error('Error:', error));
    }

    // Function to reload the specific GeoJSON layer on the map
    function reloadGeoJSONLayer(geojsonData) {
        // Find and remove the existing layer for the shp_file
        map1.eachLayer(function(layer) {
            if (layer instanceof L.GeoJSON && layer.options.shpFile === window.shpFile) {
                map1.removeLayer(layer);
            }
        });

        // Add the new GeoJSON layer with selected plots highlighted in red
        const layer = L.geoJSON(geojsonData, {
            style: function(feature) {
                return {
                    color: feature.properties.selected ? 'red' : 'blue'
                };
            },
            onEachFeature: function(feature, layer) {
                layer.on('mouseover', function(e) {
                    const properties = feature.properties;
                    let popupContent = '<div>';
                    for (let key in properties) {
                        popupContent += `<strong>${key}:</strong> ${properties[key]}<br>`;
                    }
                    popupContent += '</div>';
                    layer.bindPopup(popupContent).openPopup();
                });

                layer.on('mouseout', function(e) {
                    // Close the popup
                    layer.closePopup();
                });
            },
            shpFile: window.shpFile // Store the shp_file in the layer options for identification
        }).addTo(map1);

        // Fit the map view to the bounds of the new GeoJSON layer
        map1.fitBounds(layer.getBounds());
    }




    // Function to send selected polygons and accessions to the backend
//     function sendSelectedPolygons() {
//         console.log('hello'); // Print hello when the button is clicked

//         if (selectedPlots.length === 0 && getSelectedAccessions().length === 0) {
//             console.error('No plots or accessions selected');
//             return;
//         }

//         const data = {
//             selectedPlots: selectedPlots.length > 0 ? selectedPlots : null,
//             selectedAccessions: getSelectedAccessions().length > 0 ? getSelectedAccessions() : null,
//             shp_file: window.shpFile // Include the shp_file
//         };

//         console.log('Sending selected data to the backend:', data);

//         // Fetch selected polygons data
//         fetch('/process-selected-polygons', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify(data)
//         })
//         .then(response => response.json())
//         .then(result => {
//             console.log('Statistics:', result);
//             selectedResults = JSON.parse(result.selected_plots); // Store the selected plots data in the global results object
//             console.log('Results:', selectedResults);
//             allResults = JSON.parse(result.all_plots); // Store the all plots data in the global allPlotsResult object
//             console.log('ALL Results:', allResults);
//             updateChart(selectedResults, 'Band_6_max');
//             updateHistogramChart(allResults, 'Band_6_max');
//         })
//         .catch(error => console.error('Error:', error));
//     }

    // Add event listener to the y-variable dropdown
    document.getElementById('y-variable-select').addEventListener('change', function() {
        const selectedYVariable = this.value;
        updateChart(selectedResults, selectedYVariable);
        updateHistogramChart(allResults, selectedYVariable);
        console.log('selected variable and values are', selectedYVariable)
    });

    // Fetch initial data and initialize the chart
    fetch('/api/data')
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        results = data; // Store the initial data in the global results object
        updateChart(selectedResults, 'Band_6_max');
    })
    .catch(error => {
        console.error('Error fetching initial data:', error);
    });
    // Handle window resize events
    window.addEventListener('resize', function() {
        if (window.resultChart) {
            window.resultChart.resize();
        }
        if (window.histogramChart) {
            window.histogramChart.resize();
        }
    });
});
