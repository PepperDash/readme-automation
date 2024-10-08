import os
import re

def extract_implemented_interfaces(file_content):
    interface_pattern = re.compile(r'class\s+\w+\s*:\s*([^{]+)')
    match = interface_pattern.search(file_content)
    if match:
        items = match.group(1).split(',')
        interfaces = [item.strip() for item in items if item.strip().startswith('I')]
        base_classes = [item.strip() for item in items if not item.strip().startswith('I') and not item.strip().startswith('EssentialsPluginDeviceFactory')]
        return interfaces, base_classes
    return [], []

def extract_supported_types(file_content):
    types_pattern = re.compile(r'TypeNames\s*=\s*new\s*List<string>\(\)\s*{([^}]+)}')
    match = types_pattern.search(file_content)
    if match:
        types = [type_name.strip().strip('"') for type_name in match.group(1).split(',')]
        return types
    return []

def extract_minimum_essentials_framework_version(file_content):
    version_pattern = re.compile(r'MinimumEssentialsFrameworkVersion\s*=\s*"([^"]+)"')
    match = version_pattern.search(file_content)
    if match:
        return match.group(1)
    return None

def extract_public_methods(file_content):
    methods_pattern = re.compile(r'public\s+\w+\s+\w+\s*\([^)]*\)\s*')
    matches = methods_pattern.findall(file_content)
    return [match.strip() for match in matches]

def extract_join_map(file_content):
    join_pattern = re.compile(
        r'public\s+JoinDataComplete\s+(\w+)\s*=\s*new\s+JoinDataComplete\([^)]*\)\s*{[^}]*Description\s*=\s*"([^"]+)"[^}]*JoinType\s*=\s*eJoinType\.(\w+)[^}]*JoinNumber\s*=\s*(\d+)', 
        re.DOTALL
    )
    
    joins = []
    for join_name, description, join_type, join_number in join_pattern.findall(file_content):
        joins.append({
            "name": join_name,
            "description": description,
            "type": join_type,
            "join_number": join_number
        })
    return joins

def read_files_in_directory(directory):
    all_interfaces = []
    all_base_classes = []
    all_supported_types = []
    all_minimum_versions = []
    all_public_methods = []
    all_joins = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.cs'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    interfaces, base_classes = extract_implemented_interfaces(content)
                    supported_types = extract_supported_types(content)
                    minimum_version = extract_minimum_essentials_framework_version(content)
                    public_methods = extract_public_methods(content)
                    joins = extract_join_map(content)

                    all_interfaces.extend(interfaces)
                    all_base_classes.extend(base_classes)
                    all_supported_types.extend(supported_types)
                    if minimum_version:
                        all_minimum_versions.append(minimum_version)
                    all_public_methods.extend(public_methods)
                    all_joins.extend(joins)

    return {
        "interfaces": all_interfaces,
        "base_classes": all_base_classes,
        "supported_types": all_supported_types,
        "minimum_versions": all_minimum_versions,
        "public_methods": all_public_methods,
        "joins": all_joins
    }

def find_joinmap_classes(class_names):
    return [class_name for class_name in class_names if class_name.endswith('JoinMap')]

def read_class_names_from_files(directory):
    class_names = []
    class_pattern = re.compile(r'^\s*(?:\[[^\]]+\]\s*)*(?:public\s+|private\s+|protected\s+)?class\s+([A-Za-z_]\w*)\b', re.MULTILINE)
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.cs'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    class_names.extend(class_pattern.findall(content))

    return class_names

def parse_joinmap_info(class_name, filename):
    """
    Parses all JoinDataComplete entries from the specified file for a given class name.

    Parameters:
    - class_name (str): The name of the class to parse.
    - filename (str): The path to the file containing the join map.

    Returns:
    - list of dict: Each dictionary contains 'join_number', 'type', and 'description' for each join.
    """
    with open(filename, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # Updated regex to capture each JoinDataComplete entry with JoinNumber, JoinType, and Description
    join_pattern = re.compile(
        r'public\s+JoinDataComplete\s+\w+\s*=\s*new\s+JoinDataComplete\(\s*new\s+JoinData\s*{[^}]*JoinNumber\s*=\s*(\d+)[^}]*}\s*,\s*new\s+JoinMetadata\s*{[^}]*Description\s*=\s*"([^"]+)"[^}]*JoinType\s*=\s*eJoinType\.(\w+)',
        re.DOTALL
    )

    joinmap_info = []
    for join_number, description, join_type in join_pattern.findall(file_content):
        joinmap_info.append({
            "join_number": join_number,
            "type": join_type,
            "description": description
        })

    return joinmap_info

def generate_markdown_chart(joins):
    markdown_chart = ""

    markdown_chart += "### Digitals\n\n"
    markdown_chart += "Legacy Join | Standalone Join | Type (RW) | Description\n"
    markdown_chart += "--- | --- | --- | ---\n"
    for join in joins:
        if join["type"] == "Digital":
            markdown_chart += f"{join['join_number']} | {join['join_number']} | R | {join['description']}\n"

    markdown_chart += "\n### Analogs\n\n"
    markdown_chart += "Legacy Join | Standalone Join | Type (RW) | Description\n"
    markdown_chart += "--- | --- | --- | ---\n"
    for join in joins:
        if join["type"] == "Analog":
            markdown_chart += f"{join['join_number']} | {join['join_number']} | R | {join['description']}\n"

    markdown_chart += "\n### Serials\n\n"
    markdown_chart += "Legacy Join | Standalone Join | Type (RW) | Description\n"
    markdown_chart += "--- | --- | --- | ---\n"
    for join in joins:
        if join["type"] == "Serial":
            markdown_chart += f"{join['join_number']} | {join['join_number']} | R | {join['description']}\n"
    return markdown_chart

def print_markdown_list(title, items):
    """
    Prints a list of items in markdown format.
    """
    print(f"### {title}:\n")
    for item in items:
        print(f"- {item}")
    print()

if __name__ == "__main__":
    project_directory = "./PDT.PanasonicDisplay.EPI"
    results = read_files_in_directory(project_directory)

    # Print sections in markdown list format
    print_markdown_list("Interfaces Implemented", results["interfaces"])
    print_markdown_list("Base Classes", results["base_classes"])
    print_markdown_list("Supported Types", results["supported_types"])
    print_markdown_list("Minimum Essentials Framework Versions", results["minimum_versions"])
    print_markdown_list("Public Methods", results["public_methods"])

    # Identify Join Map Classes and Parse Information
    class_names = read_class_names_from_files(project_directory)
    joinmap_classes = find_joinmap_classes(class_names)
    joinmap_info = [parse_joinmap_info(cls, os.path.join(project_directory, f"{cls}.cs")) for cls in joinmap_classes]

    # Print join maps in table format
    markdown_chart = generate_markdown_chart([j for sublist in joinmap_info for j in sublist])
    print("\n### Join Maps:\n", markdown_chart)
