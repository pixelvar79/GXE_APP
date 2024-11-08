import os
from pyodm import Node
import glob
import subprocess
import time
import requests
import shutil
import uuid
import json

# Name of the Docker volume
volume_name = "odm_data_outputs"
container_name = "my_custom_container"

# Check if the container already exists
existing_containers = subprocess.check_output(["docker", "ps", "-aqf", f"name={container_name}"]).decode().strip()
if existing_containers:
    # Stop and remove the existing container
    print(f"Container '{container_name}' is already running. Stopping and removing it...")
    subprocess.run(["docker", "stop", container_name], check=False)
    subprocess.run(["docker", "rm", container_name], check=False)
    
# Create the Docker volume if it doesn't exist
subprocess.run(["docker", "volume", "create", volume_name], check=True)

# Start the container and capture the container ID
#container_id = subprocess.check_output(["docker", "run", "-d", "-p", "3000:3000", "--name", container_name, "opendronemap/nodeodm"]).decode().strip()
container_id = subprocess.check_output(["docker", "run", "-d", "--gpus", "all", "-p", "3000:3000", "--name", container_name, "opendronemap/nodeodm"]).decode().strip()


# Wait for a few seconds to ensure the container is up and running
time.sleep(5)

# Use docker inspect to retrieve the container's details as JSON
container_info = json.loads(subprocess.check_output(["docker", "inspect", container_id]))
#print(container_info)

# Retrieve the container UUID
#container_uuid = container_info[0]["Config"]["Labels"]["org.label-schema.version"]


# Define the path to the output folder (local Windows folder)
output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'odm','images','output_folder')

# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Define the path to the input projects folder
projects_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'odm','images','input_folder')

# Create an empty list to store project IDs
#project_ids = []

# Initialize a NodeODM instance with the specified host and port
n = Node('localhost', 3000)

# Define processing options and flags
processing_options = {
    "auto-boundary": True,
    #"camera-lens": "brown",
    "dem-resolution": 1.5,
    "dsm": True,
    "min-num-features": 12000,
    "optimize-disk-space": True,
    "orthophoto-resolution": 1,
    "pc-quality": "high",
    "use-hybrid-bundle-adjustment": True,
    "radiometric-calibration": "camera+sun",
    "split": 300,
    "split-overlap": 10,
    #"texturing-skip-global-seam-leveling": True,
    "use-3dmesh": True,
    #"use-hybrid-bundle-adjustment": True,
    #"output_path": output_folder
    #"output_path": "/outputs"
    # Modify the "output_path" to point to the mounted volume inside the container
    #"output_path": "/path/in/container"
}


# Iterate through project folders
for project_folder in os.listdir(projects_folder):
    # Get the project ID from the NodeODM container's environment variables
    #container_project_id = subprocess.check_output(["docker", "exec", container_name, "echo $Id"]).decode().strip()
    #print(container_project_id)

    # Append the project_id to the list
    #project_ids.append(container_project_id)


    # Define the path to the input images folder for the current project
    input_images = os.path.join(projects_folder, project_folder)
    #print(input_images)
    # Create a list of TIF files in the input folder
    tif_files = glob.glob(os.path.join(input_images, '*.TIF'))
    print(len(tif_files))

    # Create a single processing task for all TIF files
    task = n.create_task(tif_files, options=processing_options)

    # Print a message to indicate the start of processing
    print(f"Processing started for {project_folder}...")

    # Wait for the processing to complete
    task.wait_for_completion()

    # Move the output files to the local output folder with the container_project_id
# Now you have a list of project IDs that you can use to copy files from the container to the local output folder
#for project_id in project_ids:
    # Move the output files to the local output folder with the project_id
    #project_output_folder = os.path.join(output_folder, project_id)
#os.makedirs(output_folder)
    #subprocess.run(["docker", "cp", f"{container_name}:/var/www/data/{project_id}/all.zip", project_output_folder], check=True)
subprocess.run(["docker", "cp", f"{container_name}:/var/www/data", output_folder], check=True)

# Optionally, you can stop the Docker container if it's no longer needed
subprocess.run(["docker", "stop", container_id], check=False)   

