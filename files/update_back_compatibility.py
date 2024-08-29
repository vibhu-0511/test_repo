import json
import yaml
import argparse
import subprocess
import traceback

def update_json_file(json_file):
    try:
        with open(json_file, 'r+') as file:
            data = json.load(file)
            data['backward_compatible_mode'] = True
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
        print(f"Updated JSON file: {json_file}")
    except Exception as e:
        print(f"Error updating JSON file {json_file}: {e}")
        traceback.print_exc()

def update_yaml_file(yaml_file):
    try:
        with open(yaml_file, 'r+') as file:
            data = yaml.safe_load(file)
            if 'modules' not in data:
                data['modules'] = {}
            if 'extraction' not in data['modules']:
                data['modules']['extraction'] = {}
            data['modules']['extraction']['backward_compatible_mode'] = True

            file.seek(0)
            yaml.safe_dump(data, file)
            file.truncate()
        print(f"Updated YAML file: {yaml_file}")
    except Exception as e:
        print(f"Error updating YAML file {yaml_file}: {e}")
        traceback.print_exc()

def update_backwards_compatibility(short_facility_code, full_facility_code, container_name):
    # Path on the server
    json_path = f"/opt/vr/bagfile_handler/{short_facility_code}/config/params.autoscan.json"
    
    # Path inside the container
    yaml_path = f"/home/cvpipeline/deploy/config/facility/{full_facility_code}.yaml"
    
    # Update the JSON file on the server
    update_json_file(json_path)
    
    # Step 1: Copy the YAML file from the container to the host
    local_yaml_path = f"/tmp/{full_facility_code}.yaml"
    copy_command = f"docker cp {container_name}:{yaml_path} {local_yaml_path}"
    try:
        subprocess.run(copy_command, shell=True, check=True)
        print(f"Copied YAML file from container to host: {local_yaml_path}")
        
        # Step 2: Update the YAML file on the host
        update_yaml_file(local_yaml_path)
        
        # Step 3: Copy the modified YAML file back to the container
        copy_back_command = f"docker cp {local_yaml_path} {container_name}:{yaml_path}"
        subprocess.run(copy_back_command, shell=True, check=True)
        print(f"Copied updated YAML file back to container: {yaml_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error copying YAML file to/from container: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update STMHE bag compatibility.')
    parser.add_argument('--facility_code', type=str, required=True, help='Facility code (short form).')
    parser.add_argument('--full_facility_code', type=str, required=True, help='Facility code (full form).')

    args = parser.parse_args()
    container_name = f"SW_{args.facility_code}_bagfile_handler"
    update_backwards_compatibility(args.facility_code, args.full_facility_code, container_name)

