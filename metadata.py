import os
import re
import json

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

def find_file_in_directory(filename, root_directory):
    """
    Recursively searches for a file within all subdirectories of a root directory.

    Parameters:
    - filename (str): The name of the file to find.
    - root_directory (str): The root directory to start the search from.

    Returns:
    - str: The full path of the file if found; otherwise, None.
    """
    print(f"Starting search in root directory: {root_directory}")  # Debug statement
    for root, _, files in os.walk(root_directory):
        for file in files:
            # Debug output to confirm traversal
            # print(f"Checking file: {file} in {root}")  # Debug statement
            if file == filename:
                full_path = os.path.join(root, file)
                print(f"Found file '{filename}' at: {full_path}")  # Debug statement
                return full_path
    print(f"File '{filename}' not found in any subdirectory of {root_directory}")
    return None

def parse_joinmap_info(class_name, root_directory):
    """
    Parses all JoinDataComplete entries from the specified file for a given class name.

    Parameters:
    - class_name (str): The name of the class to parse.
    - root_directory (str): The root directory to search for the file.

    Returns:
    - list of dict: Each dictionary contains 'join_number', 'type', and 'description' for each join.
    """
    filename = f"{class_name}.cs"
    file_path = find_file_in_directory(filename, root_directory)

    if not file_path:
        print(f"File not found: {filename}. Skipping...")
        return []

    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

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
    markdown_chart += "| Join |  Type (RW) | Description|\n"
    markdown_chart += "| --- | --- |  ---| \n"
    for join in joins:
        if join["type"] == "Digital":
            markdown_chart += f"| {join['join_number']} | R | {join['description']} |\n"

    markdown_chart += "\n### Analogs\n\n"
    markdown_chart += "| Join | Type (RW) | Description |\n"
    markdown_chart += "| --- | --- | --- |\n"
    for join in joins:
        if join["type"] == "Analog":
            markdown_chart += f"| {join['join_number']} | R | {join['description']}\n"

    markdown_chart += "\n### Serials\n\n"
    markdown_chart += "| Join | Type (RW) | Description |\n"
    markdown_chart += "| --- | --- |  ---|\n"
    for join in joins:
        if join["type"] == "Serial":
            markdown_chart += f"| {join['join_number']} | R | {join['description']}|\n"
    return markdown_chart

def print_markdown_list(title, items):
    """
    Prints a list of items in markdown format.
    """
    print(f"### {title}:\n")
    for item in items:
        print(f"- {item}")
    print()

def find_config_classes(directory):
    """
    Finds all classes that end with 'Config' in .cs files in the given directory.

    Returns:
    - A dictionary mapping class names to their file paths.
    """
    config_classes = {}
    class_pattern = re.compile(r'^\s*(?:\[[^\]]+\]\s*)*(?:public\s+|private\s+|protected\s+)?class\s+([A-Za-z_]\w*Config)\b', re.MULTILINE)
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.cs'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = class_pattern.findall(content)
                    for class_name in matches:
                        config_classes[class_name] = file_path
    return config_classes

def parse_config_class(class_name, file_path):
    """
    Parses the properties of the given config class.

    Returns:
    - A list of dictionaries representing the class's properties.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Find the class definition
    class_pattern = re.compile(r'class\s+' + re.escape(class_name) + r'\s*(?::\s*[^{]+)?\s*{(.*?)}', re.DOTALL)
    match = class_pattern.search(content)
    if not match:
        print(f"Class {class_name} not found in {file_path}")
        return None
    class_body = match.group(1)
    # Parse the properties
    property_pattern = re.compile(
        r'(?:\s*\[JsonProperty\("([^"]+)"\)\s*)?'  # Optional [JsonProperty("name")]
        r'\s*(?:public|private|protected)\s+'      # Access modifier
        r'([A-Za-z_<>,\s]+?)\s+'                   # Type (e.g., int, string, Dictionary<string, ApOutletConfig>)
        r'([A-Za-z_]\w+)\s*'                       # Property name
        r'{\s*get;\s*set;\s*}',                    # { get; set; }
        re.MULTILINE
    )
    properties = []
    for prop_match in property_pattern.finditer(class_body):
        json_property_name = prop_match.group(1)
        prop_type = prop_match.group(2).strip()
        prop_name = prop_match.group(3)
        properties.append({
            "json_property_name": json_property_name if json_property_name else prop_name,
            "property_name": prop_name,
            "property_type": prop_type
        })
    return properties

def extract_class_body(content, start_index):
    """
    Extracts the body of a class from the content, starting at start_index.
    Returns the class body and the index where it ends.
    """
    brace_count = 1
    index = start_index
    while brace_count > 0 and index < len(content):
        if content[index] == '{':
            brace_count += 1
        elif content[index] == '}':
            brace_count -= 1
        index += 1
    return content[start_index:index - 1], index - 1

def parse_all_classes(directory):
    class_defs = {}
    class_pattern = re.compile(
        r'^\s*(?:\[[^\]]+\]\s*)*'      # Optional attributes
        r'(?:public\s+|private\s+|protected\s+)?'  # Access modifier
        r'class\s+([A-Za-z_]\w*)'       # Class name
        r'(?:\s*:\s*[^\{]+)?'           # Optional inheritance
        r'\s*\{',                       # Opening brace
        re.MULTILINE
    )
    property_pattern = re.compile(
        r'^\s*'
        r'(?:\[[^\]]*\]\s*)*'              # Optional attributes
        r'(?:public|private|protected)\s+'  # Access modifier
        r'(?:static\s+|virtual\s+|override\s+|abstract\s+|readonly\s+)?'  # Optional modifiers
        r'([A-Za-z0-9_<>,\s\[\]]+?)\s+'     # Type
        r'([A-Za-z_]\w*)\s*'                # Property name
        r'\{[^}]*?\}',                      # Property body
        re.MULTILINE
    )
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.cs'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Find all class definitions
                    for class_match in class_pattern.finditer(content):
                        class_name = class_match.group(1)
                        class_start = class_match.end()
                        # Find the matching closing brace for the class
                        class_body, end_index = extract_class_body(content, class_start)
                        # Parse properties within the class body
                        properties = []
                        for prop_match in property_pattern.finditer(class_body):
                            json_property_name = re.search(r'\[JsonProperty\("([^"]+)"\)\]', prop_match.group(0))
                            json_property_name = json_property_name.group(1) if json_property_name else None
                            prop_type = prop_match.group(1).strip()
                            prop_name = prop_match.group(2)
                            properties.append({
                                "json_property_name": json_property_name if json_property_name else prop_name,
                                "property_name": prop_name,
                                "property_type": prop_type
                            })
                        class_defs[class_name] = properties
    return class_defs

def generate_sample_value(property_type, class_defs, processed_classes=None):
    """
    Generates a sample value for the given property type.

    Parameters:
    - property_type (str): The type of the property.
    - class_defs (dict): Dictionary of class definitions parsed.

    Returns:
    - A sample value for the property.
    """
    if processed_classes is None:
        processed_classes = set()
    property_type = property_type.strip()
    # Handle nullable types
    property_type = property_type.rstrip('?')
    # Handle primitive types
    if property_type in ('int', 'long', 'float', 'double', 'decimal'):
        return 0
    elif property_type == 'string':
        return "SampleString"
    elif property_type == 'bool':
        return True
    elif property_type == 'DateTime':
        return "2021-01-01T00:00:00Z"
    # Handle collections
    elif property_type.startswith('List<') or property_type.startswith('IList<') or property_type.startswith('IEnumerable<') or property_type.startswith('ObservableCollection<'):
        inner_type = property_type[property_type.find('<')+1:-1]
        return [generate_sample_value(inner_type, class_defs, processed_classes)]
    elif property_type.startswith('Dictionary<'):
        # e.g., Dictionary<string, ApOutletConfig>
        types = property_type[property_type.find('<')+1:-1].split(',')
        key_type = types[0].strip()
        value_type = types[1].strip()
        key_sample = generate_sample_value(key_type, class_defs, processed_classes)
        value_sample = generate_sample_value(value_type, class_defs, processed_classes)
        return { key_sample: value_sample }
    # Handle custom classes
    elif property_type in class_defs:
        if property_type in processed_classes:
            # Avoid infinite recursion
            return {}
        processed_classes.add(property_type)
        properties = class_defs[property_type]
        sample_obj = {}
        for prop in properties:
            prop_name = prop['json_property_name']
            prop_type = prop['property_type']
            sample_obj[prop_name] = generate_sample_value(prop_type, class_defs, processed_classes)
        processed_classes.remove(property_type)
        return sample_obj
    else:
        # Unknown type, default to None or string
        return "SampleValue"

def generate_sample_config(config_class_name, class_defs, supported_types):
    """
    Generates a sample config JSON object for the given config class.

    Parameters:
    - config_class_name (str): The name of the config class.
    - class_defs (dict): Dictionary of class definitions.
    - supported_types (list): List of supported types.

    Returns:
    - A dictionary representing the sample config JSON.
    """
    # Map the config class name to the supported type
    # Assumes that the supported type is the config class name without 'Config'
    type_name = config_class_name[:-6]  # Remove 'Config'
    if type_name not in supported_types:
        type_name = supported_types[0] if supported_types else type_name
    config = {
        "key": "GeneratedKey",
        "uid": 1,
        "name": "GeneratedName",
        "type": type_name,
        "group": "Group",
        "properties": generate_sample_value(config_class_name, class_defs)
    }
    return config

if __name__ == "__main__":
    project_directory = os.path.abspath("./")
    results = read_files_in_directory(project_directory)

    # Existing code to print markdown lists
    print_markdown_list("Interfaces Implemented", results["interfaces"])
    print_markdown_list("Base Classes", results["base_classes"])
    print_markdown_list("Supported Types", results["supported_types"])
    print_markdown_list("Minimum Essentials Framework Versions", results["minimum_versions"])
    print_markdown_list("Public Methods", results["public_methods"])

    # Identify Join Map Classes and Parse Information
    class_names = read_class_names_from_files(project_directory)
    joinmap_classes = find_joinmap_classes(class_names)
    joinmap_info = [parse_joinmap_info(cls, project_directory) for cls in joinmap_classes]

    # Print join maps in table format
    markdown_chart = generate_markdown_chart([j for sublist in joinmap_info for j in sublist])
    print("\n### Join Maps:\n", markdown_chart)

    # Generate Config Example
    # Parse all classes in the project
    class_defs = parse_all_classes(project_directory)

    # Identify the main config class (assuming it's the one with the most properties)
    config_classes = [cls for cls in class_defs if cls.endswith('Config')]
    if not config_classes:
        print("No config classes found.")
    else:
        main_config_class = max(config_classes, key=lambda cls: len(class_defs[cls]))

        sample_config = generate_sample_config(main_config_class, class_defs, results["supported_types"])
        print("\n### Config Example:\n")
        print("```json")
        print(json.dumps(sample_config, indent=4))
        print("```")
