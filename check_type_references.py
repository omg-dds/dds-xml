import xml.etree.ElementTree as ET
import glob

# Find all XML files in the current directory
xml_files = glob.glob("*.xml")

# Namespace handling
ns = {'dds': 'http://www.omg.org/spec/DDS-XML'}

# Collect all defined types from all XML files, including module context
defined = set()
type_tags = ['struct', 'enum', 'union', 'bitset', 'bitmask']  # Add more if needed

for xmlfile in xml_files:
    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        # Find all modules (if any)
        for module in root.findall('.//dds:module', ns):
            module_name = module.attrib.get('name')
            # Types defined via <struct>, <enum>, <union>, etc. inside module
            for tag in type_tags:
                for t in module.findall(f'.//dds:{tag}', ns):
                    type_name = t.attrib['name']
                    defined.add(f"{module_name}::{type_name}")
        # Also collect global types (not inside a module)
        for tag in type_tags:
            for t in root.findall(f'.//dds:{tag}', ns):
                parent = t.find("..")
                if parent is None or parent.tag != f"{{{ns['dds']}}}module":
                    defined.add(t.attrib['name'])
    except Exception as e:
        print(f"Error parsing {xmlfile}: {e}")

# Collect all referenced type_ref values from all XML files
referenced = set()
for xmlfile in xml_files:
    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        for t in root.findall('.//*[@type_ref]', ns):
            referenced.add(t.attrib['type_ref'])
    except Exception as e:
        print(f"Error parsing {xmlfile}: {e}")

# Show referenced types that are not defined anywhere
missing = referenced - defined
if missing:
    print("Missing type definitions for type_ref(s):")
    for m in sorted(missing):
        print(f"  {m}")
        base_type = m.split("::")[-1]
        suggestions = [d for d in defined if d.endswith(f"::{base_type}")]
        if suggestions:
            print(f"    Did you mean: {', '.join(suggestions)}?")
else:
    print("All type_ref values are defined in the loaded XML files.")