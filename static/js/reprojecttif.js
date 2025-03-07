let selectedInputDir = "";

// Function to open directory selector
function openDirectorySelector(callback) {
    const input = document.createElement('input');
    input.type = 'file';
    input.webkitdirectory = true; // Enable directory selection
    input.addEventListener('change', (event) => {
        const files = event.target.files;

        if (files.length > 0) {
            // The first file's path represents the selected folder
            const fullPath = files[0].path || files[0].webkitRelativePath;

            // Get the top-level folder path
            const folderPath = fullPath.split('/')[0];  // Get the first part of the path

            console.log("Clicked Folder Path:", folderPath); // Log the selected directory
            callback(folderPath); // Pass the top-level folder only
        } else {
            console.log("No files selected.");
        }
    });
    input.click();
}

// Button click event to select input directory
document.getElementById("selectInputDirBtn").onclick = function() {
    openDirectorySelector((path) => {
        selectedInputDir = path;
        document.getElementById("inputDir").value = selectedInputDir; // Display selected path
        console.log("Selected Input Directory (Clicked Folder):", selectedInputDir); // Print to console
    });
};

// Button click event to submit data
document.getElementById("submitBtn").onclick = function() {
    const newOutputFolder = document.getElementById("newOutputFolder").value.trim();
    const targetCRS = document.getElementById("targetCRS").value.trim();
    if (selectedInputDir === "" || newOutputFolder === "" || targetCRS === "") {
        console.error("Please select an input directory, enter a new output folder name, and specify the target CRS.");
        return;
    }

    const requestData = {
        inputDir: selectedInputDir,
        outputDir: newOutputFolder,  // Use the new output folder name
        targetCRS: targetCRS
    };

    console.log("Request Data:", requestData); // Log the request data for verification

    // Send data to the backend using fetch
    fetch('/api/reproject', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Response from server:", data); // Log server response
        startProgressUpdates(); // Start polling for progress
    })
    .catch(error => {
        console.error("Error sending data to the backend:", error);
    });
};

// Polling function to check progress
function startProgressUpdates() {
    const interval = setInterval(() => {
        fetch('/progress')
            .then(response => response.json())
            .then(data => {
                const progressBar = document.getElementById('progress-bar');
                const progressText = document.getElementById('progress-text');
                progressBar.value = data.progress;
                progressText.innerText = `${data.progress}%`;
                if (data.progress >= 100) {
                    clearInterval(interval); // Stop polling when complete
                }
            })
            .catch(error => {
                console.error("Error fetching progress:", error);
                clearInterval(interval); // Stop on error
            });
    }, 1000); // Poll every second
}