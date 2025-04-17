# -*- mode: python ; coding: utf-8 -*-
import os
from PIL import Image
import sys

block_cipher = None

# Get the absolute path to resources
script_dir = os.path.dirname(SPECPATH)
root_dir = os.path.abspath(os.path.join(script_dir, '..'))
resources_dir = os.path.join(root_dir, 'resources')

# Check for logo in multiple locations
logo_paths = [
    os.path.join(root_dir, 'logoicon.png'),  # Root directory
    os.path.join(script_dir, 'logoicon.png'),  # src directory
    os.path.join(os.path.dirname(root_dir), 'logoicon.png')  # Parent directory
]

# Find the first existing logo path
logo_path = None
for path in logo_paths:
    if os.path.exists(path):
        logo_path = path
        print(f"Found logo at: {logo_path}")
        break

# Other resource paths
bmc_qr_path = os.path.join(root_dir, 'bmc_qr.png')
app_icon_path = os.path.join(resources_dir, 'app_icon.ico')
bmc_button_path = os.path.join(resources_dir, 'bmc_button.gif')

# Print paths for debugging
print(f"Root dir (absolute): {os.path.abspath(root_dir)}")
print(f"Script dir: {script_dir}")
print(f"Resources dir: {resources_dir}")

if not os.path.exists(bmc_button_path):
    print(f"Warning: {bmc_button_path} not found!")
    bmc_button_path = None

# Create resources directory if it doesn't exist
if not os.path.exists(resources_dir):
    os.makedirs(resources_dir)
    print(f"Created resources directory: {resources_dir}")

# Convert PNG to ICO if the source image exists
if logo_path and os.path.exists(logo_path):
    try:
        img = Image.open(logo_path)
        # Save as ico with multiple sizes for better Windows integration
        img.save(app_icon_path, sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        print(f"Successfully converted {logo_path} to {app_icon_path}")
    except Exception as e:
        print(f"Error converting icon: {e}")
        # If conversion fails, set app_icon_path to None to avoid icon errors
        app_icon_path = None
else:
    print(f"Warning: Icon file not found in any of the checked locations!")
    app_icon_path = None

# Prepare data files
datas = []
if os.path.exists(bmc_qr_path):
    datas.append((bmc_qr_path, '.'))
    print(f"Added {bmc_qr_path} to datas")
if bmc_button_path and os.path.exists(bmc_button_path):
    datas.append((bmc_button_path, 'resources'))
    print(f"Added {bmc_button_path} to datas")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add the icon to datas if it exists
if app_icon_path and os.path.exists(app_icon_path):
    a.datas += [(os.path.join('resources', os.path.basename(app_icon_path)), app_icon_path, 'DATA')]
    print(f"Added {app_icon_path} to a.datas")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Version Diving',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set back to False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon_path if app_icon_path and os.path.exists(app_icon_path) else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Version Diving',
) 