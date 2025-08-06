import os

def replace_string_in_files(file_extension, input_directory, output_directory, old_string, new_string):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    for filename in os.listdir(input_directory):
        if filename.endswith(file_extension):
            input_filepath = os.path.join(input_directory, filename)
            output_filepath = os.path.join(output_directory, filename)
            
            with open(input_filepath, 'r') as file:
                filedata = file.read()
            
            newdata = filedata.replace(old_string, new_string)
            
            with open(output_filepath, 'w') as file:
                file.write(newdata)

TIMESTAMP = "20250901"

if __name__ == "__main__":
    input_directory =  "./"
    output_directory = "./omg_dds-xml_machine_readable"
    old_string = 'schemaLocation="./dds-xml'
    new_string = f'schemaLocation="https://www.omg.org/spec/DDS-XML/{TIMESTAMP}/dds-xml'
    replace_string_in_files(".xsd", input_directory, output_directory, old_string, new_string)

    # Namespaces use http:// they just define a scope. The are not URLs to be resolved.
    # schemaLocations use https:// they are URLs to be resolved.
    old_string = 'schemaLocation="http://www.omg.org/spec/DDS-XML ./dds-xml'
    new_string = f'schemaLocation="http://www.omg.org/spec/DDS-XML https://www.omg.org/spec/DDS-XML/{TIMESTAMP}/dds-xml'
    replace_string_in_files(".xml", input_directory, output_directory, old_string, new_string)
    