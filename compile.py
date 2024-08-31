import ast
import os
import pathlib
import re


def merge_files(output_file, source_files):
    import_set = set()  # To keep track of unique imports
    merged_code = ""

    for fname in source_files:
        with open(fname) as infile:
            for line in infile:
                # Check if the line is an import statement
                import_match = re.match(r"^\s*(import|from)\s+(\S+)", line)
                if import_match:
                    import_statement = import_match.group(0)
                    # Skip local imports that start with a dot
                    if not re.match(r"^\s*(import|from)\s+\.", import_statement):
                        # Add to import set if it's a new import
                        if import_statement not in import_set:
                            import_set.add(import_statement)
                            merged_code += line
                else:
                    # Add non-import lines to the merged code
                    merged_code += line
            merged_code += "\n\n"  # Ensure separation between files

    # create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # Write the merged code to the output file
    with open(output_file, "w") as outfile:
        outfile.write(merged_code)

    print(f"Merged files into {output_file}")


# ------------------------------------------------------------
# Post processing
# ------------------------------------------------------------


def list_top_level_functions(source_file):
    with open(source_file, "r") as file:
        tree = ast.parse(file.read(), filename=source_file)

    attach_parents(tree)  # Attach parent references before processing

    top_level_functions = []

    for node in ast.walk(tree):
        # Check for top-level function definitions
        if isinstance(node, ast.FunctionDef):
            # Ensure the function is not within a class
            if not within_class(node):
                top_level_functions.append(node)

    return top_level_functions


def within_class(node):
    """
    Check if the given node is within a class definition.
    """
    while hasattr(node, "parent"):
        node = node.parent
        if isinstance(node, ast.ClassDef):
            return True
    return False


def attach_parents(tree):
    """
    Attach parent references to each node in the AST.
    """
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node


def remove_duplicate_functions(source_file):
    with open(source_file, "r") as file:
        tree = ast.parse(file.read(), filename=source_file)

    attach_parents(tree)  # Attach parent references before processing

    func_names = set()
    nodes_to_remove = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not within_class(node):
                if node.name in func_names:
                    nodes_to_remove.append(node)
                else:
                    func_names.add(node.name)

    # Remove the nodes from the source by reconstructing the source code
    lines = open(source_file).readlines()
    for node in nodes_to_remove:
        start_lineno = node.lineno - 1
        end_lineno = node.end_lineno if hasattr(node, "end_lineno") else node.lineno
        for i in range(start_lineno, end_lineno):
            lines[i] = ""

    with open(source_file, "w") as file:
        file.writelines(lines)

    print(f"Removed duplicate top-level functions from {source_file}")


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


if __name__ == "__main__":
    # List your Python files in the order you want them to be merged.
    source_files = [
        "portal/utils/color.py",
        "portal/data_struct/packet.py",
        "portal/handlers.py",
        "portal/server/mmap_server.py",
        "portal/server/udp_server.py",
        "portal/server/pipe_server.py",
        "portal/server/websockets_server.py",
        "portal/managers.py",
        "portal/operators.py",
        "portal/panels.py",
        "portal/__init__.py",
    ]

    # Output single script file
    version = read_version("portal")
    output_file = f"bin/portal.blender-{version}.py"

    merge_files(output_file, source_files)

    remove_duplicate_functions(output_file)

    with open(output_file, "r") as file:
        tree = ast.parse(file.read(), filename=output_file)
        attach_parents(tree)