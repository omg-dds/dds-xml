from lxml import etree as ET
import glob
from collections import namedtuple

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


def get_profile_names(xml_files):
    """Extract profile name, considering library context."""
    #
    defined = set()
    library_profiles = dict()  # lib_name -> set(profile_names)
    #
    for xmlfile in xml_files:
        try:
            tree = ET.parse(xmlfile)
            root = tree.getroot()
            # Check if the root is a qos_library
            if root.tag == f"{{{ns['dds']}}}qos_library":
                qlib_elements = [root] + root.findall('.//dds:qos_library', ns)
            else:
                qlib_elements = root.findall('.//dds:qos_library', ns)
            for qlib in qlib_elements:
                lib_name = qlib.attrib.get('name')
                lib_profiles = set()
                # Only direct children qos_profile
                for prof in qlib.findall('dds:qos_profile', ns):
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
    #
    return defined, library_profiles

# Collect all defined qos_profile names, with library context if present 
defined, library_profiles = get_profile_names(xml_files)

print("Defined profiles:", sorted(defined))
print("Library profiles:", {k: sorted(v) for k, v in library_profiles.items()})

# Named tuple to store references
Reference = namedtuple('Reference', ['base_name', 'xmlfile', 'tag_name', 'elem_line', 'elem_name', 'lib_name'])

def get_profile_references(xml_files, elements_with_base_name):
    """Extract the Qos profiles referenced using the base_profile="..." attribute."""
    # Collect all referenced base_name values from selected elements in all XML files, and where they were referenced from
    references = []  # list of (base_name, xmlfile, tag_name, elem_line, elem_name, lib_name)
    for xmlfile in xml_files:
        try:
            tree = ET.parse(xmlfile)
            root = tree.getroot()
            for tag in elements_with_base_name:
                for t in root.findall(f'.//dds:{tag}', ns):
                    base_name = t.attrib.get('base_name')
                    if base_name:
                        # Find the closest ancestor qos_library for this element
                        lib_name = None
                        parent = t.getparent()
                        while parent is not None:
                            if parent.tag == f"{{{ns['dds']}}}qos_library":
                                lib_name = parent.attrib.get('name')
                                break
                            parent = parent.getparent()
                        elem_line = t.sourceline if hasattr(t, 'sourceline') else '?'
                        tag_name = t.tag.split('}', 1)[-1] if '}' in t.tag else t.tag
                        elem_name = t.attrib.get('name')
                        references.append(Reference(base_name, xmlfile, tag_name, elem_line, elem_name, lib_name))
        except Exception as e:
            print(f"Error parsing {xmlfile}: {e}")
    #
    return references

# Collect all referenced base_name values from selected elements in all XML files
references = get_profile_references(xml_files, elements_with_base_name)
print("References found:")
print("References:", [(ref.base_name, ref.lib_name) for ref in references])

# Helper to check if a base_name is defined, considering local library context
def is_defined(base_name, lib_name):
    # Qualified reference (with ::)
    if "::" in base_name:
        return base_name in defined
    # Unqualified reference: check in same library
    if lib_name and lib_name in library_profiles and base_name in library_profiles[lib_name]:
        return True
    # Also allow global profiles (not in any library)
    if base_name in defined:
        return True
    return False

# Find missing references
missing_refs = {}
for ref in references:
    if not is_defined(ref.base_name, ref.lib_name):
        name_str = f' name="{ref.elem_name}"' if ref.elem_name else ""
        missing_refs.setdefault(ref.base_name, []).append(
            f"    Referenced from: {ref.xmlfile} <{ref.tag_name}{name_str}> (line {ref.elem_line})"
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

