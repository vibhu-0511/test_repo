import yaml
import re
import subprocess
import argparse

def extract_service_info(yaml_file):
    """
    Extracts service names and health check ports from a YAML file.

    :param yaml_file: Path to the YAML file containing service information.
    :return: List of dictionaries containing service names and ports.
    """
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    services = data.get('services', {})
    service_list = []

    for service_name, service_info in services.items():
        healthcheck = service_info.get('healthcheck', {})
        test_command = healthcheck.get('test', '')

        # Extract port using a regular expression
        port_match = re.search(r'http://[^\s:]+:(\d+)', test_command)
        port = port_match.group(1) if port_match else None

        if port:
            service_list.append({'name': service_name, 'port': port})

    return service_list

def check_container_health(service):
    """
    Checks the health of a container by querying the health endpoint using curl.

    :param service: Dictionary containing service name and port.
    :return: Boolean indicating if the service is healthy.
    """
    url = f"http://127.0.0.1:{service['port']}/status"
    try:
        # Execute the curl command
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, check=True)

        # Convert output to lowercase and check if 'true' is in the output
        if 'true' in result.stdout.lower():
            print(f"Service: {service['name']} is healthy.")
            return True
        else:
            print(f"Service: {service['name']} is unhealthy. Response does not contain 'True'.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Service: {service['name']} is unhealthy. Curl command failed.")
        return False

def health_check(facility_code, pipeline_count):
    cvp_paths = [f"/opt/vr/cvpipeline/ocr/{facility_code}/pipeline_{i}/docker-compose.ocr.yaml" for i in range(1, pipeline_count + 1)]
    luna_path = "/opt/vr/luna/docker-compose.yaml"
    bag_handler_path = f"/opt/vr/bagfile_handler/{facility_code}/docker-compose.yaml"
    business_mgr = "/opt/vr/businessmgr/docker-compose.yaml"

    # List of all paths
    paths = cvp_paths + [luna_path, bag_handler_path, business_mgr]

    all_healthy = True

    # Check health of each service in the provided paths
    for path in paths:
        print(f"\nChecking services in: {path}")
        try:
            service_list = extract_service_info(path)
            for service in service_list:
                if not check_container_health(service):
                    all_healthy = False
        except Exception as e:
            print(f"Failed to check services in {path}. Error: {e}")
            all_healthy = False

    return all_healthy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check the health of containers for CVP, LUNA, and Bag Handler.")
    
    # Add arguments for facility code and pipeline count
    parser.add_argument('--facility_code', type=str, required=True, help="Facility code to generate the paths.")
    parser.add_argument('--pipeline_count', type=int, required=True, help="Number of pipelines to check.")

    # Parse arguments
    args = parser.parse_args()

    # Perform the health check and print result
    if health_check(args.facility_code, args.pipeline_count):
        print("All services are healthy.")
    else:
        print("Some services are unhealthy.")