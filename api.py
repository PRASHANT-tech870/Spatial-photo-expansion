import os
# Force CPU usage - set these before any imports
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Disable CUDA
os.environ["MPS_DEVICE"] = ""  # Disable MPS
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"  # Disable MPS memory

# Force CPU only 
import torch
# Safer way to disable MPS
if hasattr(torch.backends, 'mps'):
    # Just use the environment variables instead of trying to call internal methods
    os.environ["PYTORCH_NO_MPS"] = "1"
torch.set_default_device('cpu')

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from gradio_client import Client, handle_file
import shutil
from pathlib import Path
import subprocess
import logging
import sys
import uuid
from PIL import Image

# For outpainting
from gradio_client import Client, handle_file

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories if they don't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPAINT_DIR = Path("outpainted")
OUTPAINT_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Set up environment variables for subprocess
        env = os.environ.copy()
        env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
        env["CUDA_VISIBLE_DEVICES"] = ""
        env["MPS_DEVICE"] = ""
        env["PYTHONPATH"] = str(Path().absolute())
        env["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
        env["PYTORCH_NO_MPS"] = "1"
        env["MPS_DEVICE"] = ""
        
        # Get the absolute path to main.py in the same directory as this script
        main_script = Path(__file__).parent / "main.py"
        
        # Process the image using the command line approach with Python executable directly
        python_executable = sys.executable
        cmd = [python_executable, str(main_script), "--photo", str(file_path)]
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run the command and capture output
        result = subprocess.run(
            cmd, 
            env=env,
            capture_output=True, 
            text=True
        )
        
        logger.info(f"Command output: {result.stdout}")
        logger.error(f"Command error (if any): {result.stderr}")
        
        if result.returncode != 0:
            raise Exception(f"Command failed: {result.stderr}")
        
        # Get the original filename (strip _outpainted if it's an outpainted image)
        original_filename = os.path.splitext(file.filename)[0]
        base_filename = original_filename
        if base_filename.endswith('_outpainted'):
            base_filename = base_filename.replace('_outpainted', '')
        
        # Get the output directory based on the filename
        output_dir = file_path.parent / f"{original_filename}_output"
        
        if not output_dir.exists():
            raise Exception(f"Output directory not found: {output_dir}")
            
        return JSONResponse({
            "message": "Image processed successfully",
            "output_directory": str(output_dir),
            "files": {
                "depth_image": f"{output_dir}/depth_image.jpg",
                "stereo_left": f"{output_dir}/stereo_left.png",
                "stereo_right": f"{output_dir}/stereo_right.png",
                "output_hevc_file": f"{output_dir}/{base_filename}_sbs.hevc"
            }
        })
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{path:path}")
async def download_file(path: str):

    
    # Convert the path to a Path object
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )

@app.post("/outpaint/")
async def outpaint_image(file: UploadFile = File(...)):
    logger.info("========== OUTPAINT ENDPOINT CALLED ==========")
    logger.info(f"Received file: {file.filename}, size: {file.size}, content_type: {file.content_type}")
    
    try:
        # Save the uploaded file
        file_path = UPLOAD_DIR / file.filename
        logger.info(f"Saving uploaded file to: {file_path}")
        
        with open(file_path, "wb") as buffer:
            logger.info("Copying file content...")
            content = await file.read()
            buffer.write(content)
            await file.seek(0)  # Reset file pointer for potential future reads
            logger.info(f"File saved successfully, size: {len(content)} bytes")
        
        # Get output filename
        base_filename = os.path.splitext(file.filename)[0]
        png_output_path = OUTPAINT_DIR / f"{base_filename}_outpainted.png"
        logger.info(f"Output PNG path will be: {png_output_path}")
        
        logger.info(f"Starting outpainting process for {file_path}")
        
        try:
            # Initialize the client - EXACTLY as in gen.ipynb
            logger.info("Initializing gradio client...")
            client = Client("fffiloni/diffusers-image-outpaint")
            
            # Handle input file - EXACTLY as in gen.ipynb
            logger.info("Handling input file...")
            input_file = handle_file(str(file_path))
            logger.info(f"Input file prepared: {input_file}")
            
            # Run the model - EXACTLY as in gen.ipynb with same parameter names
            logger.info("Running outpainting model prediction...")
            result = client.predict(
                image=input_file,
                width=1280,
                height=720,
                overlap_percentage=10,
                num_inference_steps=10,
                resize_option="Full",
                custom_resize_percentage=50,
                prompt_input="blend seamlessly",
                alignment="Middle",
                overlap_left=True,
                overlap_right=True,
                overlap_top=True,
                overlap_bottom=True,
                api_name="/infer"
            )
            logger.info(f"Predict call completed, result: {result}")
            
            # Process results - EXACTLY as in gen.ipynb, but convert to PNG
            if isinstance(result, list) and len(result) > 0:

                logger.info(f"Result: {result[0]}")
                logger.info(f"Result: {result[1]}")
                # Get the first result
                source_path = result[1]

                logger.info(f"Result path from model: {source_path}")
                
                # Convert to PNG
                logger.info("Opening source image...")
                img = Image.open(source_path)
                logger.info(f"Saving PNG to: {png_output_path}")
                img.save(png_output_path)
                
                logger.info(f"Outpainted image saved as PNG to {png_output_path}")
                
                return JSONResponse({
                    "message": "Image outpainted and converted to PNG successfully",
                    "outpaint_path": str(png_output_path)
                })
            else:
                logger.error(f"Invalid result from model: {result}")
                raise Exception("Outpainting did not return any result files")
                
        except Exception as e:
            logger.error(f"Error in outpainting process: {str(e)}")
            raise e
            
    except Exception as e:
        logger.error(f"Error outpainting image: {str(e)}")
        logger.exception("Full exception details:")
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 