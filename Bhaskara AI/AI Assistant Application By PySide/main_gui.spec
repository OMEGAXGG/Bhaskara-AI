# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(".")
icon_path = os.path.join("icons_and_assets", "Bhaskara AI.png")

# ✅ List large binary files individually to avoid packing them
dlls = [
    (os.path.join(project_root, "llama_libs", "llama.dll"), "llama_libs"),
    (os.path.join(project_root, "stable_diff_libs", "stable_diffusion.dll"), "stable_diff_libs"),
]

# ✅ List large model files individually too
models = [
    (os.path.join(project_root, "models", "mistral-7b-instruct-v0.2-q4_k_m.gguf"), "models"),
    (os.path.join(project_root, "models", "stable-diffusion-v1-5-pruned-emaonly-Q8_0.gguf"), "models"),
]

datas = [
    ("icons_and_assets", "icons_and_assets"),
    ("utils", "utils"),
    ("login_signup.py", "."),
] + models  # ✅ Add models to data section instead of binaries

hiddenimports = collect_submodules("PySide6.QtWebEngineWidgets") + [
    "llama_cpp",
    "stable_diffusion_cpp"
]

a = Analysis(
    ["main_gui.py"],
    pathex=[project_root],
    binaries=dlls,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)  # ✅ Removed cipher=a.cipher

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Bhaskara_AI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_path
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="Bhaskara_AI"
)
