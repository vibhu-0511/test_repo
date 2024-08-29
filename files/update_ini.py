import configparser
import argparse
import os
import subprocess

def update_database_ini(file_path, database_name):
    if not os.path.exists(file_path):
        print(f"database.ini not found at {file_path}")
        return
    
    config = configparser.ConfigParser()
    config.read(file_path)
    
    if 'postgresql' not in config.sections():
        print(f"[postgresql] section not found in {file_path}")
        return
    
    config.set('postgresql', 'database', database_name)
    
    with open(file_path, 'w') as configfile:
        config.write(configfile)
    
    print(f"Updated {file_path} successfully with database '{database_name}'.")

def restart_container(container_name):
    try:
        subprocess.run(f"docker restart {container_name}", shell=True, check=True)
        print(f"Successfully restarted container: {container_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart container: {container_name}. Error: {e}")

def update_ini(database_name, pipeline_count, facility_code):

    # Extracting values from arguments
    db_name = database_name
    pipeline_count = pipeline_count
    facility_code = facility_code

    # File paths for cvp pipelines and bag handler
    cvp_paths = [f"/opt/vr/cvpipeline/ocr/{facility_code}/pipeline_{i}/config/database.ini" for i in range(1, pipeline_count + 1)]
    luna_path = "/opt/vr/luna/service_configs/database.ini"
    bag_handler_path = f"/opt/vr/bagfile_handler/{facility_code}/config/database.ini"

    # Update database.ini files for cvp pipelines
    for cvp_path in cvp_paths:
        update_database_ini(cvp_path, db_name)

    # Update luna and bag handler database.ini files
    update_database_ini(luna_path, db_name)
    update_database_ini(bag_handler_path, db_name)

    # Restart relevant containers
    # for i in range(1, pipeline_count + 1):
    #     restart_container(f"{facility_code}_cvp_pipeline_{i}")
    # restart_container("luna")
    # restart_container(f"{facility_code}_baghandler")
    restart_container("$(docker ps -q --filter 'name=6shv')")
    restart_container("luna")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update database.ini files and restart relevant containers.")
    parser.add_argument('--database_name', help="Database name to set in the database.ini file", required=False)
    parser.add_argument('--pipeline_count', type=int, help="Number of pipelines", required=False)
    parser.add_argument('--facility_code', help="Facility name for constructing paths", required=False)

    args = parser.parse_args()

    update_ini(args.database_name, args.pipeline_count, args.facility_code)

