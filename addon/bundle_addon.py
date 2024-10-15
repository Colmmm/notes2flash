import os
import shutil
import subprocess
import zipfile

def bundle_addon():
    addon_dir = "/app/addon"
    libs_dir = os.path.join(addon_dir, "libs")
    output_file = "/app/notes2flash.ankiaddon"

    # Step 1: Clean up any existing libs folder
    if os.path.exists(libs_dir):
        shutil.rmtree(libs_dir)

    # Step 2: Install dependencies into the 'libs' folder
    print("Installing dependencies...")
    subprocess.run(["pip", "install", "--target", libs_dir, "-r", "/app/requirements.txt"], check=True)

    # Step 3: Clean up any existing __pycache__ folders
    print("Removing __pycache__ folders...")
    for root, dirs, _ in os.walk(addon_dir):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                shutil.rmtree(os.path.join(root, dir_name))

    # Step 4: Create the zip archive for the add-on (.ankiaddon file)
    if os.path.exists(output_file):
        os.remove(output_file)

    print("Creating addon package...")
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(addon_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, addon_dir)
                zipf.write(file_path, arcname)

    print(f"Addon packaged successfully as {output_file}!")

if __name__ == "__main__":
    bundle_addon()
