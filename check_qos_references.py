from lxml import etree as ET
import glob

xml_files = glob.glob("*.xml")
ns = {'dds': 'http://www.omg.org/spec/DDS-XML'}

elements_with_base_name = [
    'qos_profile',
    'datawriter_qos',
    'datareader_qos',
    'participant_qos',
    'publisher_qos',
    'subscriber_qos'
]

defined = set()
library_profiles = dict()  # lib_name -> set(profile_names)

# Collect all defined qos_profile names, with library context if present (do NOT include qos_snippet)
for xmlfile in xml_files:
    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        for qlib in root.findall('.//dds:qos_library', ns):
            lib_name = qlib.attrib.get('name')
            lib_profiles = set()
            for prof in qlib.findall('.//dds:qos_profile', ns):
                prof_name = prof.attrib.get('name')
                if lib_name and prof_name:
                    defined.add(f"{lib_name}::{prof_name}")
                    lib_profiles.add(prof_name)
                elif prof_name:
                    defined.add(prof_name)
                    lib_profiles.add(prof_name)
            if lib_name:
                library_profiles[lib_name] = lib_profiles
        # Also allow global <qos_profile> (not inside a library)
        for prof in root.findall('.//dds:qos_profile', ns):
            parent = prof.getparent() if hasattr(prof, "getparent") else None
            if parent is None or parent.tag != f"{{{ns['dds']}}}qos_library":
                prof_name = prof.attrib.get('name')
                if prof_name:
                    defined.add(prof_name)
    except Exception as e:
        print(f"Error parsing {xmlfile}: {e}")

# Collect all referenced base_name values from selected elements in all XML files, and where they were referenced from
references = []  # list of (base_name, xmlfile, tag_name, elem_line, elem_name, lib_name)
for xmlfile in xml_files:
    try:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        # Find all qos_library elements and their descendants
        for qlib in root.findall('.//dds:qos_library', ns):
            lib_name = qlib.attrib.get('name')
            for tag in elements_with_base_name:
                for t in qlib.findall(f'.//dds:{tag}', ns):
                    base_name = t.attrib.get('base_name')
                    if base_name:
                        elem_line = t.sourceline if hasattr(t, 'sourceline') else '?'
                        tag_name = t.tag.split('}', 1)[-1] if '}' in t.tag else t.tag
                        elem_name = t.attrib.get('name')
                        references.append((base_name, xmlfile, tag_name, elem_line, elem_name, lib_name))
        # Also check for global elements (not inside a qos_library)
        for tag in elements_with_base_name:
            for t in root.findall(f'.//dds:{tag}', ns):
                # Skip if already found in a library above
                if t.getroottree().getpath(t).count('qos_library') > 0:
                    continue
                base_name = t.attrib.get('base_name')
                if base_name:
                    elem_line = t.sourceline if hasattr(t, 'sourceline') else '?'
                    tag_name = t.tag.split('}', 1)[-1] if '}' in t.tag else t.tag
                    elem_name = t.attrib.get('name')
                    references.append((base_name, xmlfile, tag_name, elem_line, elem_name, None))
    except Exception as e:
        print(f"Error parsing {xmlfile}: {e}")

# Helper to check if a base_name is defined, considering local library context
def is_defined(base_name, lib_name):
    if base_name in defined:
        return True
    if lib_name and "::" not in base_name:
        if lib_name in library_profiles and base_name in library_profiles[lib_name]:
            return True
    return False

# Find missing references
missing_refs = {}
for base_name, xmlfile, tag_name, elem_line, elem_name, lib_name in references:
    if not is_defined(base_name, lib_name):
        name_str = f' name="{elem_name}"' if elem_name else ""
        missing_refs.setdefault(base_name, []).append(
            f"    Referenced from: {xmlfile} <{tag_name}{name_str}> (line {elem_line})"
        )

if missing_refs:
    print("Missing Qos definitions for base_name(s):")
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