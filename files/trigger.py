import os
import random
import argparse

def trigger_events(facility_code, restructured_folder_path, count=1):
    container = f"SW_{facility_code}_bagfile_handler"
    script = "/home/cvpipeline/scripts/add_db_entry.py"
    src = restructured_folder_path
    dest = "/Cimage/syncthing/config/autoacceptfolder"

    # Print the maximum count for debugging
    print(f"Max count: {count}")
    events = [_ for _ in os.listdir(src) if 'STMHE' in _]

    # Shuffle events for random processing
    unique_events = set(events)
    random.shuffle(events)

    # Print events to be processed
    print(f"Events: {events[:count]}")

    # Process events
    for i, event in enumerate(events):
        if "STMHE" not in event:
            continue
        if i >= count:
            break
        os.system(f"cp -rv {os.path.join(src, event)} {dest}")
        os.system(f"docker exec -it {container} python3 {script} {event} {event.rsplit('_', 1)[-1]} 2 STMHE 0001")

    # Print the list of processed events for debugging
    print(events[:i])

# Command-line interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some files and trigger events.')
    parser.add_argument('--facility_code', help='Facility code for the container name', required=True)
    parser.add_argument('--restructured_folder_path', help='Path to save restructured bags', required=False)
    parser.add_argument('--count', type=int, default=1, help='Number of events to process (default: 1)')
    args = parser.parse_args()

    trigger_events(args.facility_code, args.restructured_folder_path, args.count)
