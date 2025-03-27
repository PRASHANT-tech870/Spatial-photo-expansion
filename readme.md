# Spatial Photo Expansion

This application converts regular 2D photos into spatial (3D) images compatible with devices that support HEVC spatial format, such as Apple Vision Pro. It also provides image outpainting capabilities to expand image boundaries.

## See it live running live at http://52.233.80.176:8002/ (hosted on azure cloud)


## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Usage](#usage)
- [Technical Details](#technical-details)
- [Project Structure](#project-structure)
- [File Storage](#file-storage)

## Features

- **2D to 3D Conversion**: Transform regular photos into spatial 3D images
- **Depth Map Generation**: Create depth maps for photos using deep learning
- **Stereo Image Creation**: Generate left and right stereo images
- **HEVC Spatial Format**: Convert to Apple Vision Pro compatible format
- **Image Outpainting**: Expand image boundaries with AI-generated content
- **Web Interface**: Easy-to-use browser-based interface
- **CPU-Only Processing**: No GPU required (optimized for CPU use)

## Installation

### Prerequisites

- Python 3.8+ 
- FFmpeg (for HEVC encoding)
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Spatial-photo-expansion.git
   cd Spatial-photo-expansion
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

   Note: The requirements.txt should include:
   - fastapi
   - uvicorn
   - python-multipart
   - pillow
   - numpy
   - scipy
   - opencv-python
   - torch
   - transformers
   - gradio_client

3. Create necessary directories:
   ```
   mkdir -p uploads outpainted
   ```

## How to Run

1. Start the FastAPI server:
   ```
   cd APP
   python api.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8002
   ```

3. The web interface will allow you to upload, process, and download your spatial images.

## Usage

### Web Interface

1. **Upload an Image**:
   - Drag and drop an image or click to select one from your file system.

2. **Process Options**:
   - **Convert to Spatial (HEVC)**: Converts your 2D image to a 3D spatial image.
   - **Outpaint Image**: Expands the boundaries of your image using AI.

3. **Processing Results**:
   - After processing, you'll see download links for:
     - Depth image
     - Left stereo image
     - Right stereo image
     - Final HEVC spatial file
   - Click "Download All Files" to get everything at once.

### Command Line Usage

You can also use the processing functionality directly via command line:

```python main.py --photo path/to/your/image.jpg```


This will create a directory named `image_output` containing all processed files.

## Technical Details

### 2D to 3D Conversion Process

1. **Depth Map Generation**:
   - Uses Hugging Face's Depth-Anything-V2 model to generate a depth map
   - Analyzes the image to determine which parts are closer or further away

2. **Stereo Image Creation**:
   - Creates left and right perspectives using the depth map
   - Shifts pixels based on estimated depth values
   - Inpaints any missing areas created during the shift process

3. **HEVC Encoding**:
   - Uses FFmpeg to combine left and right images in side-by-side format
   - Encodes using HEVC (H.265) with special parameters for spatial compatibility

### Outpainting Process

1. Uses the "diffusers-image-outpaint" model via Gradio client
2. Expands image boundaries while maintaining visual coherence
3. Returns an expanded version of the original image
4. The expanded image can then be processed into a spatial 3D image

## Project Structure

- **`api.py`**: FastAPI server that handles web requests, file uploads, and processes
- **`main.py`**: Command-line entry point for image processing
- **`image_handler.py`**: Core functionality for depth map generation and 3D conversion
- **`file_mixin.py`**: Handles file and directory operations
- **`static/index.html`**: Web interface

## File Storage

The application uses two main directories for file storage:

- **`uploads/`**: Stores all uploaded images from users
  - Original images are stored with their original filenames
  - These files serve as inputs for both 3D conversion and outpainting

- **`outpainted/`**: Stores the results of the outpainting process
  - Outpainted images are saved with the naming pattern `{original_filename}_outpainted.png`
  - These files can be further processed into 3D spatial images

When processing an image (either original or outpainted), the system creates an additional folder:

- **`{filename}_output/`**: Contains all files generated during 3D conversion:
  - `depth_image.jpg`: The generated depth map
  - `stereo_left.png`: Left-eye perspective
  - `stereo_right.png`: Right-eye perspective
  - `{filename}_sbs.hevc`: Final spatial HEVC file

These directories are automatically created if they don't exist. All processed files remain available for download until manually removed.