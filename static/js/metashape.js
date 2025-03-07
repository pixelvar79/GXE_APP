// let selectedInputDir = "";
// let map1;
// let layerControl;
// const layers = {};

// function openDirectorySelector(callback) {
//     const input = document.createElement('input');
//     input.type = 'file';
//     input.webkitdirectory = true;
//     input.addEventListener('change', (event) => {
//         const files = event.target.files;

//         if (files.length > 0) {
//             const fullPath = files[0].path || files[0].webkitRelativePath;
//             const folderPath = fullPath.split('/')[0];
//             console.log("Clicked Folder Path:", folderPath);
//             callback(folderPath);
//         } else {
//             console.log("No files selected.");
//         }
//     });
//     input.click();
// }

// document.getElementById("selectInputDirBtn").onclick = function() {
//     openDirectorySelector((path) => {
//         selectedInputDir = path;
//         document.getElementById("inputDir").value = selectedInputDir;
//         console.log("Selected Input Directory (Clicked Folder):", selectedInputDir);
//     });
// };

// document.getElementById("submitBtn").onclick = function() {
//     // const outputDir = document.getElementById("outputDir").value.trim();
//     // if (selectedInputDir === "" || outputDir === "") {
//     //     console.error("Please select an input directory and enter an output directory.");
//     //     return;
//     // }

//     // const requestData = {
//     //     inputDir: selectedInputDir,
//     //     outputDir: outputDir
//     // };
//     console.clear();

//     const outputDir = document.getElementById("outputDir").value.trim();
//     const outputTypes = Array.from(document.querySelectorAll('input[name="outputType"]:checked')).map(cb => cb.value);
//     if (selectedInputDir === "" || outputDir === "") {
//         console.error("Please select an input directory and enter an output directory.");
//         return;
//     }

//     const requestData = {
//         inputDir: selectedInputDir,
//         outputDir: outputDir,
//         outputTypes: outputTypes
//         //logMessages: [] // Initialize an empty array for log messages
//     };

//     console.log("Request Data:", requestData);

//     fetch('/api/metashape', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify(requestData)
//     })
//     .then(response => response.json())
//     .then(data => {
//         console.log("Response from server:", data);
//         displayMap(data.results);
//     })
//     .catch(error => {
//         console.error("Error sending data to the backend:", error);
//     });
// };

// function fetchLogs() {
//     fetch('/api/logs')
//         .then(response => response.json())
//         .then(data => {
//             const consoleDiv = document.getElementById('console');
//             consoleDiv.innerHTML = data.logs.join('<br>');
//             consoleDiv.scrollTop = consoleDiv.scrollHeight;
//         });
// }

// setInterval(fetchLogs, 1000);

// function displayMap(results) {
//     if (!map1) {
//         map1 = L.map('map').setView([20, 0], 2);

//         const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//             maxZoom: 40,
//             attribution: '&copy; OpenStreetMap contributors'
//         });

//         osm.addTo(map1);

//         // Add legend to the map
//         const legend = L.control({ position: 'bottomright' });

//         legend.onAdd = function (map) {
//             const div = L.DomUtil.create('div', 'info legend');
//             const grades = [clip_min, clip_max];
//             const labels = [];

//             // Loop through our density intervals and generate a label with a colored square for each interval
//             for (let i = 0; i < grades.length; i++) {
//                 div.innerHTML +=
//                     '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
//                     grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
//             }

//             return div;
//         };

//         legend.addTo(map1);
//     }

//     results.forEach(item => {
//         if (item.bounds && item.png_path) {
//             const imageBounds = [[item.bounds[0][0], item.bounds[0][1]], [item.bounds[1][0], item.bounds[1][1]]];
//             const layer = L.imageOverlay(item.png_path, imageBounds).addTo(map1);
//             map1.fitBounds(imageBounds);

//             // Extract the base name of the ortho_path
//             let baseName = item.ortho_path.split(/[/\\]+/).pop();
//             // Remove the .tif extension
//             baseName = baseName.replace('.tif', '');
//             // Use the base name as the displayName
//             const displayName = baseName;

//             // Set the name property for the layer to the displayName
//             layer.name = displayName;
//             // Store the full path as a custom property
//             layer.fullPath = item.ortho_path;

//             // Add layer to layers object
//             layers[displayName] = layer;

//             // Debugging: Log the layer name and displayName
//             console.log('Added layer:', layer.fullPath, displayName);
//         }
//     });

//     // Add layer control to the map
//     if (!layerControl) {
//         layerControl = L.control.layers(null, layers).addTo(map1);
//     } else {
//         layerControl.addOverlay(layers);
//     }
// }

// // Initialize the map on page load
// document.addEventListener('DOMContentLoaded', function() {
//     map1 = L.map('map').setView([20, 0], 2);

//     const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
//         maxZoom: 40,
//         attribution: '&copy; OpenStreetMap contributors'
//     });

//     osm.addTo(map1);
// });

// function getColor(d) {
//     return d > clip_max ? '#800026' :
//            d > clip_min ? '#BD0026' :
//                           '#FFEDA0';
// }

let selectedInputDir = "";
let map1;
let layerControl;
const layers = {};

function openDirectorySelector(callback) {
    const input = document.createElement('input');
    input.type = 'file';
    input.webkitdirectory = true;
    input.addEventListener('change', (event) => {
        const files = event.target.files;

        if (files.length > 0) {
            const fullPath = files[0].path || files[0].webkitRelativePath;
            const folderPath = fullPath.split('/')[0];
            console.log("Clicked Folder Path:", folderPath);
            callback(folderPath);
        } else {
            console.log("No files selected.");
        }
    });
    input.click();
}

document.getElementById("selectInputDirBtn").onclick = function() {
    openDirectorySelector((path) => {
        selectedInputDir = path;
        document.getElementById("inputDir").value = selectedInputDir;
        console.log("Selected Input Directory (Clicked Folder):", selectedInputDir);
    });
};

document.getElementById("submitBtn").onclick = function() {
    console.clear();

    const outputDir = document.getElementById("outputDir").value.trim();
    const outputTypes = Array.from(document.querySelectorAll('input[name="outputType"]:checked')).map(cb => cb.value);
    if (selectedInputDir === "" || outputDir === "") {
        console.error("Please select an input directory and enter an output directory.");
        return;
    }

    const requestData = {
        inputDir: selectedInputDir,
        outputDir: outputDir,
        outputTypes: outputTypes
    };

    console.log("Request Data:", requestData);

    fetch('/api/metashape', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Response from server:", data);
        displayMap(data.results);
    })
    .catch(error => {
        console.error("Error sending data to the backend:", error);
    });
};

function fetchLogs() {
    fetch('/api/logs')
        .then(response => response.json())
        .then(data => {
            const consoleDiv = document.getElementById('console');
            consoleDiv.innerHTML = data.logs.join('<br>');
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
        });
}

setInterval(fetchLogs, 1000);

function displayMap(results) {
    if (!map1) {
        map1 = L.map('map').setView([20, 0], 2);

        const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 40,
            attribution: '&copy; OpenStreetMap contributors'
        });

        osm.addTo(map1);

        // Add legend to the map
        const legend = L.control({ position: 'bottomright' });

        legend.onAdd = function (map) {
            const div = L.DomUtil.create('div', 'info legend');
            const grades = [clip_min, clip_max];
            const labels = [];

            // Loop through our density intervals and generate a label with a colored square for each interval
            for (let i = 0; i < grades.length; i++) {
                div.innerHTML +=
                    '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
                    grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
            }

            return div;
        };

        legend.addTo(map1);
    }

    results.forEach(item => {
        if (item.bounds && item.png_path) {
            const imageBounds = [[item.bounds[0][0], item.bounds[0][1]], [item.bounds[1][0], item.bounds[1][1]]];
            const layer = L.imageOverlay(item.png_path, imageBounds).addTo(map1);
            map1.fitBounds(imageBounds);

            // Extract the base name of the ortho_path
            let baseName = item.ortho_path.split(/[/\\]+/).pop();
            // Remove the .tif extension
            baseName = baseName.replace('.tif', '');
            // Use the base name as the displayName
            const displayName = baseName;

            // Set the name property for the layer to the displayName
            layer.name = displayName;
            // Store the full path as a custom property
            layer.fullPath = item.ortho_path;

            // Add layer to layers object
            layers[displayName] = layer;

            // Debugging: Log the layer name and displayName
            console.log('Added layer:', layer.fullPath, displayName);
        }
    });

    // Add layer control to the map
    if (!layerControl) {
        layerControl = L.control.layers(null, layers).addTo(map1);
    } else {
        layerControl.addOverlay(layers);
    }
}

// Initialize the map on page load
document.addEventListener('DOMContentLoaded', function() {
    map1 = L.map('map').setView([20, 0], 2);

    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 40,
        attribution: '&copy; OpenStreetMap contributors'
    });

    osm.addTo(map1);
});

function getColor(d) {
    return d > clip_max ? '#800026' :
           d > clip_min ? '#BD0026' :
                          '#FFEDA0';
}

document.getElementById("outputTypesBtn").onclick = function() {
    document.querySelector(".dropdown-content").classList.toggle("show");
}

