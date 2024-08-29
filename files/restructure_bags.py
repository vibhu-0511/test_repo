import re
import os
import json
import argparse
from datetime import datetime
from bagpy import bagreader
import rosbag

def extract_datetime(s):
    # Update if the folder name format changes
    datetime_str = os.path.basename(s).replace('_0.bag', "").split("_")[1]
    return datetime.strptime(datetime_str, '%Y-%m-%d-%H-%M-%S')

def nav_topic(bagfile_path, suffix):
    """Find a topic in the ROS bag file that ends with the specified suffix.
    
    Args:
        bagfile_path (str): Path to the ROS bag file.
        suffix (str): The suffix that the topic should end with.

    Returns:
        str or None: The topic that matches the suffix, or None if not found.
    """
    # Open the bag file
    with rosbag.Bag(bagfile_path, 'r') as bag:
        # Get the list of topics
        topics = bag.get_type_and_topic_info()[1].keys()
        
        # Find and return the topic that ends with the specified suffix
        for topic in topics:
            if topic.endswith(suffix):
                print(f"Found topic: {topic}")
                return topic
        
        print(f"No topic ending with {suffix} found in the bag file.")
        return None
    

def restructure(golden_data_path, restructured_folder_path, save_mapping_path=None):
        if not os.path.exists(restructured_folder_path):
            os.makedirs(restructured_folder_path)
        golden_data = os.path.join(golden_data_path)
        policy_golden_data = restructured_folder_path
        if save_mapping_path:
            save_mapping_folder = save_mapping_path
        else:
            save_mapping_folder = restructured_folder_path
        
        target_suffix = "/nav/task"
        final_mapping = {}
        bag_pairs = {}
        
        for fil in os.listdir(golden_data):
            bag_file = os.path.join(golden_data, fil, f"{fil}_0.bag")
            
            # Find the nav task topic
            nav_task_topic = nav_topic(bag_file, target_suffix)
            if not nav_task_topic:
                print(f"No nav task topic found in file {bag_file}. Skipping.")
                continue
            
            b = bagreader(bag_file)
            msg_list = []
            tstart = None
            tend = None
            time = []
            for topic, msg, t in b.reader.read_messages(topics=nav_task_topic, start_time=tstart, end_time=tend): 
                time.append(t)
                msg_list.append(msg)
            
            # Delete folder if extracted
            temp_folder = bag_file.strip(".bag")
            if os.path.exists(temp_folder):
                os.system(f"rm -r {temp_folder}")
            
            pattern = r'event_id:\s*"([^"]+)"'
            match = re.search(pattern, str(msg_list[0]))
            if match:
                event_id = match.group(1)
                print("Extracted event_id:", event_id)
            else:
                print("No event_id found in the string.")
                continue
            
            if event_id in bag_pairs:
                bag_pairs[event_id].append(bag_file)
                if len(bag_pairs[event_id]) == 2:
                    sorted_list = sorted(bag_pairs[event_id], key=extract_datetime)
                    main_event_id = os.path.basename(sorted_list[0]).replace("_0.bag", "")
                    mhe_folder = os.path.join(policy_golden_data, main_event_id)
                    os.makedirs(mhe_folder, exist_ok=True)
                    for i, _bag in enumerate(bag_pairs[event_id]):
                        os.system(f"cp {_bag} {mhe_folder}/{main_event_id}_{i}.bag")
                        final_mapping[_bag] = f"{mhe_folder}/{main_event_id}_{i}.bag"
            else:
                bag_pairs[event_id] = [bag_file]
        
        # Save non-policy event bag to policy event bag map
        with open(f"{save_mapping_folder}/non_pol_to_pol_golden_map.json", "w") as f:
            json.dump(final_mapping, f)
        
        # Save event id to non-policy bags mapping
        with open(f"{save_mapping_folder}/event_event_id_golden_map.json", "w") as f:
            json.dump(bag_pairs, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to restructure bag files')
    parser.add_argument('--golden_data_path', help='Path to golden data set', required=True)
    parser.add_argument('--restructured_folder_path', help='Path to save restructured bags', required=True)
    parser.add_argument('--save_mapping_path', help='Path to save old to new bag mappings', required=False)
    args = parser.parse_args()

    restructure(args.golden_data_path, args.restructured_folder_path)

    
