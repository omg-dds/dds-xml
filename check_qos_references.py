from lxml import etree as ET
import glob

# Find all XML files in the current directory
xml_files = glob.glob("*.xml")

# Namespace handling
ns = {'dds': 'http://www.omg.org/spec/DDS-XML'}

# Elements to check for base_name references
elements_with_base_name = [
    'qos_profile',
    'datawriter_qos',
    'datareader_qos',
    'participant_qos',
    'publisher_qos',
    'subscriber_qos'
]

# Collect all defined qos_profile names, with library context if present (do NOT include qos_snippet)
defined = set()
for xmlfile in xml_files:
    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        for qlib in root.findall('.//dds:qos_library', ns):
            lib_name = qlib.attrib.get('name')
            # <qos_profile> only
            for prof in qlib.findall('.//dds:qos_profile', ns):
                prof_name = prof.attrib.get('name')
                if lib_name and prof_name:
                    defined.add(f"{lib_name}::{prof_name}")
                elif prof_name:
                    defined.add(prof_name)
        # Also allow global <qos_profile> (not inside a library)
        for prof in root.findall('.//dds:qos_profile', ns):
            parent = prof.find("..")
            if parent is None or parent.tag != f"{{{ns['dds']}}}qos_library":
                prof_name = prof.attrib.get('name')
                if prof_name:
                    defined.add(prof_name)
    except Exception as e:
        print(f"Error parsing {xmlfile}: {e}")

# Collect all referenced base_name values from selected elements in all XML files
referenced = set()
for xmlfile in xml_files:
    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        for tag in elements_with_base_name:
            for t in root.findall(f'.//dds:{tag}', ns):
                base_name = t.attrib.get('base_name')
                if base_name:
                    referenced.add(base_name)
    except Exception as e:
        print(f"Error parsing {xmlfile}: {e}")

# Compute missing references
missing = referenced - defined

# Show referenced base_names that are not defined anywhere, with element name and line number
if missing:
    print("Missing Qos definitions for base_name(s):")
    # Collect all references for missing base_names
    missing_refs = {}
    for xmlfile in xml_files:
        try:
            tree = ET.parse(xmlfile)
            root = tree.getroot()
            for tag in elements_with_base_name:
                for t in root.findall(f'.//dds:{tag}', ns):
                    base_name = t.attrib.get('base_name')
                    if base_name in missing:
                        elem_line = t.sourceline if hasattr(t, 'sourceline') else '?'
                        tag_name = t.tag.split('}', 1)[-1] if '}' in t.tag else t.tag
                        elem_name = t.attrib.get('name')
                        name_str = f' name="{elem_name}"' if elem_name else ""
                        missing_refs.setdefault(base_name, []).append(
                            f"    Referenced from: {xmlfile} <{tag_name}{name_str}> (line {elem_line})"
                        )
        except Exception as e:
            print(f"Error parsing {xmlfile}: {e}")
    # Print each missing base_name once, followed by all its references
    for m in sorted(missing_refs):
        print(f"  {m}")
        for ref in missing_refs[m]:
            print(ref)
        # Suggest possible matches by profile name
        base = m.split("::")[-1]
        suggestions = [d for d in defined if d.endswith(f"::{base}")]
        if suggestions:
            print(f"    Did you mean: {', '.join(suggestions)}?")
else:
    print("All base_name references resolve to a defined qos_profile.")