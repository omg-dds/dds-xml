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

def get_snippet_names(xml_files):
    """Extract snippet names, considering library context."""
    #
    defined = set()
    library_snippets = dict()  # lib_name -> set(snippet_names)
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
                for snippet in qlib.findall('dds:qos_snippet', ns):
                    snippet_name = snippet.attrib.get('name')
                    if lib_name and snippet_name:
                        defined.add(f"{lib_name}::{snippet_name}")
                        lib_profiles.add(snippet_name)
                    elif snippet_name:
                        defined.add(snippet_name)
                        lib_profiles.add(snippet_name)
                if lib_name:
                    library_snippets[lib_name] = lib_profiles
            # Also allow global <qos_snippet> (not inside a library)
            for snippet in root.findall('.//dds:qos_snippet', ns):
                parent = snippet.getparent() if hasattr(snippet, "getparent") else None
                if parent is None or parent.tag != f"{{{ns['dds']}}}qos_library":
                    snippet_name = snippet.attrib.get('name')
                    if snippet_name:
                        defined.add(snippet_name)
        except Exception as e:
            print(f"Error parsing {xmlfile}: {e}")
    #
    return defined, library_snippets

# Named tuple to store references
Reference = namedtuple('Reference', ['base_name', 'xmlfile', 'tag_name', 'elem_line', 'elem_name', 'lib_name'])

def find_profile_references(xml_files, elements_with_base_name):
    """Extract the Qos profiles referenced using the base_profile="..." attribute."""
    # Collect all referenced base_name values from selected elements in all XML files, and where they were referenced from
    refs = []  # list of (base_name, xmlfile, tag_name, elem_line, elem_name, lib_name)
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
                        refs.append(Reference(base_name, xmlfile, tag_name, elem_line, elem_name, lib_name))
        except Exception as e:
            print(f"Error parsing {xmlfile}: {e}")
    #
    return refs

def find_snippet_references(xml_files):
    """Extract all qos_snippet references from the XML files."""
    # Collect all referenced qos_snippet names from all XML files
    refs = []  # list of snippet_ref values
    for xmlfile in xml_files:
        try:
            tree = ET.parse(xmlfile)
            root = tree.getroot()
            # Find all <qos_snippets> elements
            for qos_snippets in root.findall('.//dds:qos_snippets', ns):
                # Find all <snippet> children
                for snippet in qos_snippets.findall('dds:snippet', ns):
                    snippet_ref = snippet.attrib.get('snippet_ref')
                    if snippet_ref:
                        # Find the closest ancestor qos_library for this element
                        lib_name = None
                        parent = snippet.getparent()
                        while parent is not None:
                            if parent.tag == f"{{{ns['dds']}}}qos_library":
                                lib_name = parent.attrib.get('name')
                                break
                            parent = parent.getparent()
                        elem_line = snippet.sourceline if hasattr(snippet, 'sourceline') else '?'
                        tag_name  = snippet.tag.split('}', 1)[-1] if '}' in snippet.tag else snippet.tag
                        elem_name = snippet.attrib.get('name')
                        refs.append(Reference(snippet_ref, xmlfile, tag_name, elem_line, elem_name, lib_name))
        except Exception as e:
            print(f"Error parsing {xmlfile}: {e}")
    #
    return refs

# Helper to check if a base_name is defined, considering local library context
def is_defined(base_name, lib_name, defined, library_profiles):
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

def find_missing_refs(references, defined, library_profiles):
    missing = {}
    for ref in references:
        if not is_defined(ref.base_name, ref.lib_name, defined, library_profiles):
            name_str = f' name="{ref.elem_name}"' if ref.elem_name else ""
            missing.setdefault(ref.base_name, []).append(
                f"    Referenced from: {ref.xmlfile} <{ref.tag_name}{name_str}> (line {ref.elem_line})"
            )

    return missing

'''# Find missing Qos Profile references
missing_profile_refs = {}
for ref in p_references:
    if not is_defined(ref.base_name, ref.lib_name, defined, library_profiles):
        name_str = f' name="{ref.elem_name}"' if ref.elem_name else ""
        missing_profile_refs.setdefault(ref.base_name, []).append(
            f"    Referenced from: {ref.xmlfile} <{ref.tag_name}{name_str}> (line {ref.elem_line})"
        )
'''

defined, library_profiles = get_profile_names(xml_files)
p_references = find_profile_references(xml_files, elements_with_base_name)
missing_profile_refs = find_missing_refs(p_references, defined, library_profiles)

if missing_profile_refs:
    print("Missing Qos Profile definitions:")
    for m in sorted(missing_profile_refs):
        print(f"  {m}")
        for ref in missing_profile_refs[m]:
            print(ref)
else:
    print("All base_name references resolve to a defined qos_profile.")

#
# Find missing Qos Snippet references
#
defined, library_snippets = get_snippet_names(xml_files)
s_references = find_snippet_references(xml_files)
missing_snippet_refs = find_missing_refs(s_references, defined, library_snippets)

if missing_snippet_refs:
    print("Missing Qos Snippet definitions:")
    for m in sorted(missing_snippet_refs):
        print(f"  {m}")
        for ref in missing_snippet_refs[m]:
            print(ref)
else:
    print("All snippet_ref references resolve to a defined qos_snippet.")

