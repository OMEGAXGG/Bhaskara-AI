Here are the Models we use in this project:-

Mistral 7B Instruct- huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF

Stable Diffusion- huggingface.co/second-state/stable-diffusion-v1-5-GGUF/blob/main/stable-diffusion-v1-5-pruned-emaonly-Q8_0.gguf

To make your Bhaskara AI application work properly with both Mistral-7B-Instruct-v0.2-GGUF (for LLM) and stable-diffusion-v1-5-pruned-emaonly-Q8_0.gguf (for image generation) inside a Python virtual environment, follow these steps to structure and set up the system:

✅ 1. Create and Activate Virtual Environment

      python -m venv bhaskara_env
      source bhaskara_env/bin/activate      # For Linux/macOS
      bhaskara_env\Scripts\activate.bat     # For Windows


✅ 2. Install Required Libraries
    Core Dependencies:
    
            pip install PySide6 numpy opencv-python pillow
  ✅ For LLM (Mistral-7B via llama-cpp-python):
          
            pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/  # Use CPU or GPU variant
Use the appropriate wheel for your system: CPU-only or GPU (CUDA, ROCm, etc.).

For Stable Diffusion (via ctransformers or llama-cpp-python variant that supports GGUF image models — or load via diffusers with compatible model):
✅If using Stable Diffusion GGUF
    
      pip install ctransformers  # Experimental GGUF SD support (limited)
✅If using the Hugging Face Diffusers library:

      pip install torch torchvision diffusers transformers accelerate


✅ 3. Organize Model Files
      Place models in a structured folder like this:
          BhaskaraAI/
          ├── models/
          │   ├── mistral/
          │   │   └── mistral-7b-instruct-v0.2-q4_k_m.gguf
          │   └── stable-diffusion/
          │       └── stable-diffusion-v1-5-pruned-emaonly-Q8_0.gguf


✅ 4. Integrate with Bhaskara AI GUI
    Use PySide6 to route prompts from the user interface to the loaded models. Display LLM output in the chat and SD images in a QLabel using QPixmap.fromImage().
