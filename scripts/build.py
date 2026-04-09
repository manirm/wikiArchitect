import os
import sys
import shutil
import subprocess
import argparse

def get_sqlite_vss_paths():
    """Locates the sqlite-vss extension files."""
    try:
        import sqlite_vss
        base_dir = os.path.dirname(sqlite_vss.__file__)
        files = [f for f in os.listdir(base_dir) if f.endswith(('.so', '.dylib', '.dll'))]
        return [os.path.join(base_dir, f) for f in files]
    except ImportError:
        return []

def run_build():
    parser = argparse.ArgumentParser(description="WikiArchitect Nuitka Build Script")
    parser.add_argument("--dry-run", action="store_true", help="Print command without running")
    args = parser.parse_args()

    # 1. Prepare Environment
    main_path = os.path.join("src", "main.py")
    output_dir = "dist"
    os.makedirs(output_dir, exist_ok=True)

    # 2. Configure Nuitka Command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--output-dir=" + output_dir,
        "--remove-output",
        # UI/App Identity
        "--company-name=ManiRM",
        "--product-name=WikiArchitect",
        "--file-version=0.2.0",
        "--product-version=0.2.0",
    ]

    # 3. Add Resource Data (Conditional)
    if os.path.isdir("vault"):
        cmd.append("--include-data-dir=vault=vault")
    
    if os.path.isdir(os.path.join("src", "ui", "assets")):
        cmd.append("--include-data-dir=src/ui/assets=assets")

    # 4. Include sqlite-vss extensions
    vss_files = get_sqlite_vss_paths()
    for f in vss_files:
        # Nuitka 2.0+ uses --include-data-files or --include-binaries
        cmd.append(f"--include-data-files={f}={os.path.basename(f)}")

    # 4. OS Specific Flags
    if sys.platform == "darwin":
        cmd.append("--macos-create-app-bundle")
        # cmd.append("--macos-app-icon=assets/icon.icns")
    elif sys.platform == "win32":
        cmd.append("--enable-plugin=tk-inter") # just in case, though we use wx
        # cmd.append("--windows-icon-from-ico=assets/icon.ico")
        cmd.append("--windows-uac-admin")
    
    cmd.append(main_path)

    print(f"Building for {sys.platform}...")
    print("Command:", " ".join(cmd))

    if not args.dry_run:
        subprocess.run(cmd, check=True)
    else:
        print("Dry run complete.")

if __name__ == "__main__":
    run_build()
