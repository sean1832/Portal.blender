import argparse
import fnmatch
import os
import pathlib
import re
import zipfile


def parser():
    parser = argparse.ArgumentParser(description="Pack a directory into a .zip file")
    parser.add_argument("source", help="Directory to pack")
    parser.add_argument("destination", help="Destination .zip file")
    return parser


def should_exclude(path, exclude_patterns):
    """
    Check if a given path (file or directory) should be excluded based on the exclusion patterns.
    """
    for pattern in exclude_patterns:
        # Check if the path matches any of the exclusion patterns
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def pack(source, destination, exclude_patterns=[]):
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    # Adding the source directory to the zip
    with zipfile.ZipFile(destination, "w") as zipf:
        # Iterate through all files and directories in the source directory
        for root, dirs, files in os.walk(source):
            # Exclude directories based on patterns (e.g., '__pycache__/')
            dirs[:] = [
                d for d in dirs if not should_exclude(os.path.join(root, d), exclude_patterns)
            ]

            # Add the directory itself to the zip file (if not excluded)
            if not should_exclude(root, exclude_patterns):
                zipf.write(root, os.path.relpath(root, os.path.dirname(source)))

            for file in files:
                file_path = os.path.join(root, file)
                # Skip files that match the exclude pattern (e.g., '*.pyc')
                if should_exclude(file_path, exclude_patterns):
                    continue

                # Add each file to the zip file
                zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(source)))


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
    pack(args.source, target_path, exclude_patterns=["__pycache__", "*.pyc"])


if __name__ == "__main__":
    main()
