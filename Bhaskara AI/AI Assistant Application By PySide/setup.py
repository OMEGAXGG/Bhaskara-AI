from cx_Freeze import setup, Executable
import os

# Include FFmpeg DLLs
ffmpeg_dlls = [os.path.join(os.path.dirname(__file__), 'ffmpeg', dll) for dll in ['avcodec-58.dll', 'avutil-56.dll']]


# Path to your model directory (adjust accordingly)
model_path = os.path.join(os.path.dirname(__file__), 'models', 'mistral-7b-instruct-v0.2-q4_k_m.gguf')

# Update the build options to include the model file
setup(
    name="Bhaskara AI",
    version="1.0",
    description="My PySide6 Application",
    options={
        'build_exe': {
            'packages': ['os', 'json', 'PySide6', 'ffmpeg'],  # Include necessary packages
            'include_files': ffmpeg_dlls,  # Include FFmpeg DLLs
            'include_files': [model_path],  # Include the model file
        }
    },
    executables=[Executable("main_gui.py", base="Win32GUI")]  # GUI mode without console
)
