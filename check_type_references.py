import xml.etree.ElementTree as ET
import glob

# Find all XML files in the current directory
xml_files = glob.glob("*.xml")

# Namespace handling
ns = {'dds': 'http://www.omg.org/spec/DDS-XML'}

# Collect all defined types from all XML files, including module context
type_tags = ['struct', 'enum', 'union', 'bitset', 'bitmask', 'typedef', 'exception']  # Add more if needed

def collect_types_in_module(module_elem, module_path, defined_types):
    for tag in type_tags:
        for t in module_elem.findall(f'dds:{tag}', ns):
            type_name = t.attrib.get('name')
            if type_name:
                qualified_name = '::'.join(module_path + [type_name])
                defined_types.add(qualified_name)
    # Recurse into nested modules
    for submodule in module_elem.findall('dds:module', ns):
        submodule_name = submodule.attrib.get('name')
        if submodule_name:
            collect_types_in_module(submodule, module_path + [submodule_name], defined_types)

def get_type_names(xml_files):
    defined_types = set()
    for xmlfile in xml_files:
        try:
            tree = ET.parse(xmlfile)
            root = tree.getroot()
            # Top-level modules
            for module in root.findall('.//dds:module', ns):
                parent = module.find("..")
                # Only process top-level modules (not nested)
                if parent is None or parent.tag != f"{{{ns['dds']}}}module":
                    module_name = module.attrib.get('name')
                    if module_name:
                        collect_types_in_module(module, [module_name], defined_types)
            # Also collect global types (not inside any module)
            for tag in type_tags:
                for t in root.findall(f'.//dds:{tag}', ns):
                    parent = t.find("..")
                    if parent is None or parent.tag != f"{{{ns['dds']}}}module":
                        type_name = t.attrib.get('name')
                        if type_name:
                            defined_types.add(type_name)
        except ET.ParseError as e:
            print(f"Exception (defined) file: {xmlfile}: {e}")
            if hasattr(e, 'position'):
                print(f"  Error at line {e.position[0]}, column {e.position[1]}")
        except Exception as e:
            print(f"Exception2 (defined) file: {xmlfile}: {e}")
    return defined_types

def find_type_references(xml_files):
    referenced_types = set()
    for xmlfile in xml_files:
        try:
            tree = ET.parse(xmlfile)
            root = tree.getroot()
            for tag in type_tags:
                for t in root.findall(f'.//dds:{tag}', ns):
                    for attr in ['type_ref', 'nonBasicTypeName', 'baseType']:
                        type_ref = t.attrib.get(attr)
                        if type_ref:
                            referenced_types.add(type_ref)
        except ET.ParseError as e:
            print(f"Exception (referenced) file: {xmlfile}: {e}")
            if hasattr(e, 'position'):
                print(f"  Error at line {e.position[0]}, column {e.position[1]}")
        except Exception as e:
            print(f"Exception2 (referenced) file: {xmlfile}: {e}")
    return referenced_types

defined_types = get_type_names(xml_files)
print("Defined types:")
for dt in sorted(defined_types):
    print(f"  {dt}")
print("End of Defined types:")

referenced_types = find_type_references(xml_files)
print("Referenced types:")
for rt in sorted(referenced_types):
    print(f"  {rt}")
print("End of Referenced types:")

# Show referenced types that are not defined anywhere
missing = referenced_types - defined_types

if missing:
    print("Missing type definitions for type_ref(s):")
    for m in sorted(missing):
        print(f"  {m}")
else:
    print("All type_ref values are defined in the loaded XML files.")