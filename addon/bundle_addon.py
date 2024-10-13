import os
import shutil
import subprocess

def bundle_addon():
    addon_dir = "./"
    libs_dir = os.path.join(addon_dir, "libs")

    # Step 1: Clean up any existing libs folder
    if os.path.exists(libs_dir):
        shutil.rmtree(libs_dir)

    # Step 2: Install dependencies into the 'libs' folder
    print("Installing dependencies...")
    subprocess.run(["pip", "install", "--target", libs_dir, "-r", "requirements.txt"], check=True)

    # Step 3: Create a zip archive of the addon if needed (optional)
    output_file = "notes2flash_addon.zip"
    if os.path.exists(output_file):
        os.remove(output_file)

    print("Creating addon package...")
    shutil.make_archive("notes2flash_addon", 'zip', addon_dir)

    print(f"Addon packaged successfully as {output_file}!")

if __name__ == "__main__":
    bundle_addon()
