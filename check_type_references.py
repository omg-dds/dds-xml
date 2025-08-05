from lxml import etree as ET
import glob
from collections import namedtuple

# Find all XML files in the current directory
xml_files = glob.glob("*.xml")

# Namespace handling
ns = {'dds': 'http://www.omg.org/spec/DDS-XML'}

type_tags = ['struct', 'enum', 'union', 'bitset', 'bitmask', 'typedef', 'exception']

Reference = namedtuple('Reference', ['referenced_type', 'xmlfile', 'tag_name', 'elem_line', 'elem_name', 'module_path'])

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
            # Top-level modules (including root as module)
            if root.tag == f"{{{ns['dds']}}}module":
                module_name = root.attrib.get('name')
                if module_name:
                    collect_types_in_module(root, [module_name], defined_types)
            for module in root.findall('.//dds:module', ns):
                parent = module.getparent()
                if parent is None or parent.tag != f"{{{ns['dds']}}}module":
                    module_name = module.attrib.get('name')
                    if module_name:
                        collect_types_in_module(module, [module_name], defined_types)
            # Also collect global types (not inside any module)
            for tag in type_tags:
                for t in root.findall(f'.//dds:{tag}', ns):
                    parent = t.getparent()
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
    refs = []
    for xmlfile in xml_files:
        try:
            tree = ET.parse(xmlfile)
            root = tree.getroot()
            for tag in type_tags:
                for t in root.findall(f'.//dds:{tag}', ns):
                    # Find module path for this element
                    module_path = []
                    parent = t.getparent()
                    while parent is not None:
                        if parent.tag == f"{{{ns['dds']}}}module":
                            module_name = parent.attrib.get('name')
                            if module_name:
                                module_path.insert(0, module_name)
                        parent = parent.getparent()
                    for attr in ['type_ref', 'nonBasicTypeName', 'baseType']:
                        type_ref = t.attrib.get(attr)
                        if type_ref:
                            elem_line = t.sourceline if hasattr(t, 'sourceline') else '?'
                            tag_name = t.tag.split('}', 1)[-1] if '}' in t.tag else t.tag
                            elem_name = t.attrib.get('name')
                            refs.append(Reference(
                                referenced_type=type_ref,
                                xmlfile=xmlfile,
                                tag_name=tag_name,
                                elem_line=elem_line,
                                elem_name=elem_name,
                                module_path=module_path
                            ))
        except ET.ParseError as e:
            print(f"Exception (referenced) file: {xmlfile}: {e}")
            if hasattr(e, 'position'):
                print(f"  Error at line {e.position[0]}, column {e.position[1]}")
        except Exception as e:
            print(f"Exception2 (referenced) file: {xmlfile}: {e}")
    return refs

defined_types = get_type_names(xml_files)
referenced_types = find_type_references(xml_files)

# Helper to check if a type reference is defined, considering module context
def is_defined(ref, defined):
    ref_name = ref.referenced_type.strip()
    # Absolute reference: must match from the root
    if ref_name.startswith("::"):
        candidate = ref_name[2:]
        return candidate in defined
    # Relative reference: try from innermost to outermost scope
    for i in range(len(ref.module_path), -1, -1):
        candidate = '::'.join(ref.module_path[:i] + [ref_name]) if ref.module_path[:i] else ref_name
        if candidate in defined:
            return True
    return False

# Find and print missing references with file and line number
missing_refs = {}
for ref in referenced_types:
    if not is_defined(ref, defined_types):
        name_str = f' name="{ref.elem_name}"' if ref.elem_name else ""
        missing_refs.setdefault(ref.referenced_type, []).append(
            f"    Referenced from: {ref.xmlfile} <{ref.tag_name}{name_str}> (line {ref.elem_line})"
        )

if missing_refs:
    print("Missing type definitions for type_ref(s):")
    for m in sorted(missing_refs):
        print(f"  {m}")
        for ref_line in missing_refs[m]:
            print(ref_line)
else:
    print("All type_ref values are defined in the loaded XML files.")