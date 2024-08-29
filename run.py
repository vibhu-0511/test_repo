import os
import sys
import time
import argparse
import tempfile
import subprocess
import concurrent.futures
from files.bag_download import download
from cvpipeline.db_update import db_update
from files.restructure_bags import restructure
from files.launch_containers import launch
from files.health_check import health_check
from files.update_ini import update_ini
from files.update_back_compatibility import update_backwards_compatibility
from files.trigger import trigger_events
from cvpipeline.deployments.services.testing_simulator.docker_stats import docker_stats
from cvpipeline.redis_polling import RedisPolling  # Import Redis functions
# from cvpipeline.status_logs import get_events_logs
# from cvpipeline.cal_tat import get_tat_metrics
# from cvpipeline.accuracy_testing import check_for_accuracy


def parse_arguments():
    """Parse and return the command-line arguments."""
    parser = argparse.ArgumentParser(description="Main script for handling various operations.")

    # Database update arguments
    parser.add_argument("--csv_src_folder", help="Source folder containing CSV files for database update", required=False)
    parser.add_argument("--csv_dest_folder", help="Destination folder to copy CSV files to", required=False)

    # Bag file download arguments
    parser.add_argument("--base_dir", required=False, help="Base Directory to download data from gcp")
    parser.add_argument("--facility_code", help="Facility code for the dataset.", required=False)
    parser.add_argument("--version", help="Version of the dataset.", required=False)
    parser.add_argument("--bags_dst_path", help="Local destination path for the downloaded files.", required=False)

    # Health check of containers
    parser.add_argument('--server_ip', type=str, required=False, help="Server ip for endpoint")

    # Arguments for updating database.ini
    parser.add_argument('--database_name', help="Database name to set in the database.ini file", required=False)
    parser.add_argument('--pipeline_count', type=int, help="Number of pipelines", required=False)

    # Backward compatibility arguments
    parser.add_argument("--full_facility_code", type=str, help="Full facility code.", required=False)

    # Event triggering arguments
    parser.add_argument("--count", type=int, help="Count of events to trigger.", required=False)

    # Redis polling arguments
    parser.add_argument("--schema_name", help="Schema name for Redis polling", required=False)

    return parser.parse_args()


def handle_bag_download(args):
    """Handle the bag file download process."""
    if args.facility_code and args.version:
        print("Starting bag file download...")
        src_path = os.path.join("test_data_automation", args.facility_code, args.version)
        
        if not args.bags_dst_path:
            base_dir = args.base_dir
            args.bags_dst_path = tempfile.mkdtemp(dir=base_dir)
            print(f"Generated temporary destination path: {args.bags_dst_path}")

        download(src_path, args.bags_dst_path)

        dataset_path_file = os.path.join(args.bags_dst_path, args.version, "golden_dataset", f"{args.facility_code}_"+"dataset_path.txt")
        if os.path.exists(dataset_path_file):
            with open(dataset_path_file, "r") as file:
                paths = file.readline()
                for line in paths:
                    path = line.strip()
                    print(f"GCP location for dataset: {path}")
                    download(os.path.join(path, "STMHE-0001_2024-06-04-14*"), os.path.join(args.bags_dst_path, "golden_dataset"))
        else:
            print(f"Dataset path file not found: {dataset_path_file}")

        print("Bag file download completed.\n" + "-"*60)

def handle_db_update(args):
    """Handle the database update process."""
    if args.csv_src_folder and args.csv_dest_folder:
        print("Starting database update...")
        csv_src_folder = args.bags_dst_path

        db_update(args.csv_src_folder, args.csv_dest_folder)
        print("Database update completed.\n" + "-"*60)

def handle_restructuring(args):
    """Handle the restructuring of bag files."""
    print("Starting bag file restructuring...")
    golden_dataset_path = "/Cimage/vibhanshu/test_automation/tmp31gy8c4e/golden_dataset"
    restructured_folder_path = "/Cimage/vibhanshu/test_automation/tmp31gy8c4e/restructured_files"
    restructure(golden_dataset_path, restructured_folder_path)
    print("Bag file restructuring completed.\n" + "-"*60)
        

def handle_gcp_key_check():
    """Check for the existence of the GCP key."""
    if check():
        print("GCP JSON key is present at /home/vimaan/key.\n" + "-"*60)

def handle_container_launch():
    """Launch the necessary containers."""
    print("Launching containers...")
    launch()
    print("Containers launched.\n" + "-"*60)

def health_check_with_retries(args, retries=10, delay=30):
    """
    Perform health check with retries and delay.

    :param facility_code: Facility code to generate paths.
    :param pipeline_count: Number of pipelines to check.
    :param retries: Number of retries if containers are unhealthy.
    :param delay: Time to wait between retries (in seconds).
    :return: Boolean indicating if all services are healthy.
    """
    for attempt in range(retries):
        print(f"\nAttempt {attempt + 1}/{retries} to check container health...")
        all_healthy = health_check(args.facility_code, args.pipeline_count, args.server_ip)
        
        if all_healthy:
            # print("All services are healthy.")
            return True
        
        if attempt < retries - 1:
            print(f"Waiting for {delay} seconds before retrying...")
            time.sleep(delay)

    return False

def handle_ini_update(args):
    """Update INI files."""
    print("Updating INI files...")
    update_ini(args.database_name, args.pipeline_count, args.facility_code)
    print("INI files updated.\n" + "-"*60)

def handle_backward_compatibility(args):
    """Update backward compatibility settings."""
    if args.facility_code and args.full_facility_code:
        print("Updating backward compatibility...")
        container_name = f"SW_{args.facility_code}_bagfile_handler"
        update_backwards_compatibility(args.facility_code, args.full_facility_code, container_name)
        print("Backward compatibility updated.\n" + "-"*60)

def handle_event_triggering(args):
    """Trigger the pipeline events."""
    if args.facility_code and args.count:
        print("Triggering pipeline events")
        restructured_folder_path = "/Cimage/vibhanshu/test_automation/tmp31gy8c4e/restructured_files"
        trigger_events(args.facility_code, restructured_folder_path, args.count)
        print("Pipeline events triggered.\n" + "-"*60)



def monitor_redis_and_docker(args):
    #Checking Redis and Docker parallely
    redis_instance = RedisPolling()
    nav_entries = redis_instance.check_nav_entries(args.schema_name)

    while not nav_entries:
        print("running while loop until we got nav entries in activity proc table")
        nav_entries = redis_instance.check_nav_entries(args.schema_name)
        time.sleep(10)

    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit the Redis polling task
        redis_future = executor.submit(redis_instance.start_polling, args.schema_name)
        # Submit the Docker stats task
        docker_future = executor.submit(redis_instance.run_docker_stats)

        # Wait for the Redis polling to finish
        redis_future.result()

        # Cancel the Docker stats task if it's still running
        docker_future.cancel()

# def get_all_metrics(args):
#     get_events_logs()
#     get_tat_metrics()
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     events_path = os.path.join(script_dir, "trigger_events.txt")
#     gt_data_path = os.path.join(args.bags_dst_path, args.version, "gt_data")
#     # gt_data_path = "/Cimage/vibhanshu/tmpva41alm6/v1.1/gt_data/6shv1 GT data june 4th onwards.csv"
#     check_for_accuracy(events_path, gt_data_path)


def main():
    """Main function to orchestrate the different operations."""
    args = parse_arguments()

    # Handle various tasks based on arguments
    # handle_bag_download(args)
    # handle_db_update(args)
    # handle_restructuring(args)
    handle_container_launch()
    if health_check_with_retries(args):
        print("All containers are healthy!!")
        handle_ini_update(args)
        handle_backward_compatibility(args)
        handle_event_triggering(args)
        monitor_redis_and_docker(args)
        print("hello")
    else:
        raise RuntimeError("Error: Not all containers are healthy! Please check the container status.")
    redis_instance = RedisPolling()
    if redis_instance.check_entries():
        get_all_metrics(args)
    
    

if __name__ == "__main__":
    main()

# Example command to run the script
# sudo python3 main.py --facility_code 6shv1 --full_facility_code 00006shv0001 --csv_src_folder test_data_automation/6shv1/v1.1/nav_table --csv_dest_folder /Cimage/vibhanshu/csv_files --version v1.1 --database_name test --pipeline_count 1 --count 8 --schema_name public --server_ip 10.72.99.25