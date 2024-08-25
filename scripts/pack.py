import argparse
import os
import pathlib
import re
import zipfile


def parser():
    parser = argparse.ArgumentParser(description="Pack a directory into a .zip file")
    parser.add_argument("source", help="Directory to pack")
    parser.add_argument("destination", help="Destination .zip file")
    return parser


def pack(source, destination):
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    # Adding the source directory to the zip
    with zipfile.ZipFile(destination, "w") as zipf:
        # Iterate through all files and directories in the source directory
        for root, _, files in os.walk(source):
            # Add the directory itself to the zip file
            zipf.write(root, os.path.relpath(root, os.path.dirname(source)))
            for file in files:
                # Add each file to the zip file
                zipf.write(
                    os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.dirname(source))
                )


def read_version(source_dir):
    version_file = pathlib.Path(source_dir, "__init__.py")
    if version_file.exists():
        with version_file.open() as f:
            content = f.read()
            version_match = re.search(r"\"version\":\s*\((\d+),\s*(\d+),\s*(\d+)\)", content)
            if version_match:
                version = ".".join(version_match.groups())
                return version
    return None


def main():
    args = parser().parse_args()
    version = read_version(args.source)
    if version:
        print(f"Version found: {version}")
    else:
        print("Version not found.")
    project_name = pathlib.Path(os.path.abspath(args.source)).parent.name
    print(f"Packing {project_name}...")
    target_filename = f"{project_name}-{version}.zip"
    target_path = os.path.join(args.destination, target_filename)
    pack(args.source, target_path)


if __name__ == "__main__":
    main()
