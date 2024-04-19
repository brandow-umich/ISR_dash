# ISR_dash

## Project Overview
This project automates the processing of donor and affiliate data for ISR (Institute for Social Research). It includes cleaning data, merging datasets, geocoding addresses, handling interests, and generating reports on affiliations. The project utilizes Python, Pandas for data manipulation, and the ArcGIS API for geocoding.

## Getting Started

### Prerequisites
- Conda Package Manager
- Python 3.8 or newer
- Git (Optional, if cloning the repo)

### Clone Repository and Setup

1. **Clone the repository (optional if you have the files another way):**
   ```bash
   git clone https://github.com/brandow-umich/ISR_dash.git
   cd ISR_dash
   ```
 ## Setting Up the Conda Environment

2. **After cloning the repository, you can create the Conda environment using the `environment.yml` file included in the repository. Run the following command in the root directory of the project:**
  
  ```bash
  conda env create -f environment.yml
  ```
  ```bash
  conda activate ISRenv
  ```
# Project Setup Guide

## Downloading and Setting Up Anaconda

### Step 1: Download and Install Anaconda
- **Visit the Anaconda Download Page**: Access [Anaconda's official website](https://www.anaconda.com/products/individual) and head to the download section.
- **Select the Installer**: Choose the appropriate installer for your operating system: Windows, macOS, or Linux.
- **Download the Installer**: Click on the download button for the latest version of Anaconda.
- **Run the Installer**:
  - **Windows**: Open the downloaded `.exe` file and follow the on-screen instructions. It's recommended to check the box "Add Anaconda to my PATH environment variable" for easier command line usage.
  - **macOS/Linux**: Open the downloaded `.pkg` or `.sh` file and follow the on-screen instructions.

### Step 2: Install Visual Studio Code through Anaconda (If not already installed)
- **Open Anaconda Navigator**:
  - **Windows**: Search for Anaconda Navigator in your Start menu and open it.
  - **macOS/Linux**: Open Anaconda Navigator from your Applications folder or via the terminal with `anaconda-navigator`.
- **Install VSCode**:
  - Locate the Visual Studio Code tile within the Anaconda Navigator interface.
  - Click the 'Install' button. Anaconda Navigator will manage the installation.

### Step 3: Launch Visual Studio Code
- If you haven't created the virtual environment yet, launch VSCode directly from Anaconda Navigator by clicking the 'Launch' button in the Visual Studio Code tile.

### Step 4: Setting Up VSCode for Python Development
- **Download VSCode**: Navigate to [Visual Studio Code's website](https://code.visualstudio.com/) and download the version for your device. For non-Mac devices, visit [alternate downloads](https://code.visualstudio.com/#alt-downloads).
- **Install Extensions**: In VSCode, go to the extension tab (fourth tab in the menu) and download the extensions 'Python' and 'Python Debugger'.
- **Open/Create Python Files**: To open an existing Python file, click '+Open'. To create a new Python file, click '+ New File'.
- **Trust Authors and Libraries**: You may need to approve authors and external libraries. To all pop-up criteria, hit "Trust."

### Step 5: Creating the Virutal Environment
- **ctrl + `** to open a new terminal.
- **In the terminal:** 
  -  `conda env create -f environment.yml`
  -  `conda activate ISRenv`
-  **All set to run the code**

## Cleaning Dataset
- **Download Data**: Download the `9.0 MProfile` Excel sheet from Business Objects as usual.
**If using Google Drive still:**
- **Upload to Google Drive**: Drag and drop the file into the shared Google Drive folder under the `dashboard_coding` directory.
- **Prepare VSCode**:
  - Open a new VSCode window.
  - Drag and drop the `dashboard_coding` folder from your file organizer into VSCode.
  - Trust the authors of the files by selecting 'Trust'.
**If you cloned**
- Open VSCode
- **If you are updating a report with new entries**:
  - Open the `isr_clean_final.py` file from the sidebar.
  - Scroll to the `main()` function
    - Update `geocoded_data_path` to the file path of the last completed csv file from this script (Note: 3-18-dataset_copy.csv was the last csv from handoff).
    - Update `file_path` to the new 9.0 MProfile excel file.
  - Run the script by clicking the play button on the upper right side. Monitor the script's progress in the output window at the bottom.
  - When the script prints `"Processing Complete"` you're all set.
- **Data Output**: The updated `new_main_dataset.csv` and all files within the `affiliation_layers` folder are now ready to be used for dashboard creation.

### Congratulations on setting up your project environment and data workflow!
