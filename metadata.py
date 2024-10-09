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
    for root, _, files in os.walk(root_directory):
        for file in files:
            if file == filename:
                full_path = os.path.join(root, file)
                return full_path
    return None

def parse_joinmap_info(class_name, root_directory):
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
    
    # Digitals
    markdown_chart += "#### Digitals\n\n"
    markdown_chart += "| Join | Type (RW) | Description |\n"
    markdown_chart += "| --- | --- | --- |\n"
    for join in joins:
        if join["type"] == "Digital":
            markdown_chart += f"| {join['join_number']} | R | {join['description']} |\n"
    
    # Analogs
    markdown_chart += "\n#### Analogs\n\n"
    markdown_chart += "| Join | Type (RW) | Description |\n"
    markdown_chart += "| --- | --- | --- |\n"
    for join in joins:
        if join["type"] == "Analog":
            markdown_chart += f"| {join['join_number']} | R | {join['description']} |\n"
    
    # Serials
    markdown_chart += "\n#### Serials\n\n"
    markdown_chart += "| Join | Type (RW) | Description |\n"
    markdown_chart += "| --- | --- | --- |\n"
    for join in joins:
        if join["type"] == "Serial":
            markdown_chart += f"| {join['join_number']} | R | {join['description']} |\n"
    return markdown_chart

def generate_config_example_markdown(sample_config):
    markdown = ""
    markdown += "```json\n"
    markdown += json.dumps(sample_config, indent=4)
    markdown += "\n```\n"
    return markdown

def generate_markdown_list(items):
    """
    Generates a list of items in markdown format.
    
    Returns:
    - str: The markdown content.
    """
    markdown = ''
    for item in items:
        markdown += f"- {item}\n"
    markdown += '\n'
    return markdown

def find_config_classes(directory):
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
        r'([A-Za-z0-9_<>,\s\[\]\?]+?)\s+'     # Type
        r'([A-Za-z_]\w*)\s*'                # Property name
        r'\{[^}]*?\}',                      # Property body
        re.MULTILINE | re.DOTALL
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
                            prop_string = prop_match.group(0)
                            json_property_match = re.search(r'\[JsonProperty\("([^"]+)"\)\]', prop_string)
                            json_property_name = json_property_match.group(1) if json_property_match else None
                            prop_type = prop_match.group(1).strip()
                            prop_name = prop_match.group(2)
                            properties.append({
                                "json_property_name": json_property_name if json_property_name else prop_name,
                                "property_name": prop_name,
                                "property_type": prop_type
                            })
                        class_defs[class_name] = properties
    return class_defs

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

def generate_sample_value(property_type, class_defs, processed_classes=None):
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
        types = property_type[property_type.find('<')+1:-1].split(',')
        key_type = types[0].strip()
        value_type = types[1].strip()
        key_sample = generate_sample_value(key_type, class_defs, processed_classes)
        value_sample = generate_sample_value(value_type, class_defs, processed_classes)
        return { key_sample: value_sample }
    # Handle custom classes
    elif property_type in class_defs:
        if property_type in processed_classes:
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

def generate_config_example_markdown(sample_config):
    markdown = "### Config Example:\n\n"
    markdown += "```json\n"
    markdown += json.dumps(sample_config, indent=4)
    markdown += "\n```\n"
    return markdown

def read_readme_file(filepath):
    if not os.path.exists(filepath):
        print(f"README.md file not found at {filepath}. A new file will be created.")
        return ""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def update_readme_section(readme_content, section_title, new_section_content):
    start_marker = f'<!-- START {section_title} -->'
    end_marker = f'<!-- END {section_title} -->'
    
    pattern = re.compile(
        rf'{re.escape(start_marker)}(.*?){re.escape(end_marker)}',
        re.DOTALL | re.IGNORECASE
    )
    
    match = pattern.search(readme_content)
    
    if match:
        print(f"Updating existing section: {section_title}")
        updated_section = f'{start_marker}\n{new_section_content.rstrip()}\n{end_marker}'
        updated_readme = readme_content[:match.start()] + updated_section + readme_content[match.end():]
    else:
        print(f"Adding new section: {section_title}")
        updated_section = f'\n{start_marker}\n### {section_title}\n\n{new_section_content.rstrip()}\n{end_marker}\n'
        updated_readme = readme_content + updated_section
    return updated_readme

def remove_duplicates_preserve_order(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]

if __name__ == "__main__":
    project_directory = os.path.abspath("./")
    results = read_files_in_directory(project_directory)

    # Generate markdown sections without titles
    # Remove duplicates from interfaces and base classes while preserving order
    unique_interfaces = remove_duplicates_preserve_order(results["interfaces"])
    unique_base_classes = remove_duplicates_preserve_order(results["base_classes"])

    # Generate markdown sections without titles using the deduplicated lists
    interfaces_markdown = generate_markdown_list(unique_interfaces)
    base_classes_markdown = generate_markdown_list(unique_base_classes)
    supported_types_markdown = generate_markdown_list(results["supported_types"])
    minimum_versions_markdown = generate_markdown_list(results["minimum_versions"])
    public_methods_markdown = generate_markdown_list(results["public_methods"])

    # Generate Join Maps markdown
    class_names = read_class_names_from_files(project_directory)
    joinmap_classes = find_joinmap_classes(class_names)
    joinmap_info = [parse_joinmap_info(cls, project_directory) for cls in joinmap_classes]
    join_maps_markdown = generate_markdown_chart([j for sublist in joinmap_info for j in sublist])

    # Generate Config Example markdown
    class_defs = parse_all_classes(project_directory)
    config_classes = [cls for cls in class_defs if cls.endswith('Config')]
    if not config_classes:
        print("No config classes found.")
        config_example_markdown = ""
    else:
        main_config_class = max(config_classes, key=lambda cls: len(class_defs[cls]))
        sample_config = generate_sample_config(main_config_class, class_defs, results["supported_types"])
        config_example_markdown = generate_config_example_markdown(sample_config)

    # Read the existing README.md content
    readme_path = os.path.join(project_directory, 'README.md')
    readme_content = read_readme_file(readme_path)

    # Update or insert sections with section titles handled in update_readme_section
    readme_content = update_readme_section(readme_content, "Interfaces Implemented", interfaces_markdown)
    readme_content = update_readme_section(readme_content, "Base Classes", base_classes_markdown)
    readme_content = update_readme_section(readme_content, "Supported Types", supported_types_markdown)
    readme_content = update_readme_section(readme_content, "Minimum Essentials Framework Versions", minimum_versions_markdown)
    readme_content = update_readme_section(readme_content, "Public Methods", public_methods_markdown)
    readme_content = update_readme_section(readme_content, "Join Maps", join_maps_markdown)
    if config_example_markdown:
        readme_content = update_readme_section(readme_content, "Config Example", config_example_markdown)

    # Write the updated content back to README.md
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("README.md has been updated.")
