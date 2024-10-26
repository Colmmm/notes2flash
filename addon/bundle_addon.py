import os
import shutil
import subprocess
import zipfile

def bundle_addon():
    addon_dir = "/app/addon"
    libs_dir = os.path.join(addon_dir, "libs")
    output_file = "/app/notes2flash.ankiaddon"
    requirements_file = "/app/requirements.txt"
    installed_packages_file = os.path.join(libs_dir, "installed_packages.txt")

    # Step 1: Check if the libs directory needs updating
    if not os.path.exists(libs_dir):
        os.makedirs(libs_dir)
        install_dependencies = True
    else:
        # Compare installed packages with the requirements file
        try:
            with open(requirements_file, 'r') as f:
                required_packages = f.read().splitlines()

            installed_packages = subprocess.check_output(
                ["pip", "freeze", "--path", libs_dir]
            ).decode("utf-8").splitlines()

            # Check if there's a difference between required and installed packages
            install_dependencies = set(required_packages) != set(installed_packages)
        except Exception as e:
            print(f"Error checking installed packages: {e}")
            install_dependencies = True  # Install if comparison fails

    # Step 2: Install or update dependencies only if needed
    if install_dependencies:
        print("Installing or updating dependencies...")
        subprocess.run(["pip", "install", "--target", libs_dir, "-r", requirements_file], check=True)
        with open(installed_packages_file, 'w') as f:
            f.write('\n'.join(subprocess.check_output(
                ["pip", "freeze", "--path", libs_dir]
            ).decode("utf-8").splitlines()))
    else:
        print("Dependencies are already up to date. Skipping installation.")

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
                # Exclude service_account.json from the bundle
                if file == "service_account.json":
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, addon_dir)
                zipf.write(file_path, arcname)

    print(f"Addon packaged successfully as {output_file}!")

if __name__ == "__main__":
    bundle_addon()
