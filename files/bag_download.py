import sys
import os
import subprocess
import argparse
import tempfile

def download(src_path: str, dst_path: str, **kwargs: dict) -> bool:
    """Download files from Google Cloud Storage (GCS) to the local filesystem.

    Args:
        src_path (str): The path of the file or directory in GCS to download from.
        dst_path (str): The local directory where the files will be downloaded to.
        **kwargs: Additional keyword arguments.

    Returns:
        bool: True if the download is successful, False otherwise.
    """
    os.makedirs(dst_path, exist_ok=True)
    success = True
    try:
        if not src_path.startswith("gs://"):
            src_path = "gs://" + src_path
        process = subprocess.Popen(
            f"""sudo gsutil -m cp -r {src_path} {dst_path}""",
            stdout=sys.stdout, stderr=sys.stderr, shell=True
        )
        process.communicate()
    except subprocess.CalledProcessError as exc:
        success = False
        if "logger" in kwargs:
            kwargs["logger"].error(f"Error: {exc.output}")
        print("Error:", exc.output)
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download files from GCS to the local filesystem.")
    
    parser.add_argument("--base_dir", required=True, help="Base Directory to download data from gcp")
    parser.add_argument("--facility_code", required=True, help="Facility code for the dataset.")
    parser.add_argument("--version", required=True, help="Version of the dataset.")
    parser.add_argument("--dst_path", required=False, help="Local destination path for the downloaded files.")
    
    args = parser.parse_args()

    src_path = os.path.join("test_data_automation", args.facility_code,
                            args.version)
    
    if args.dst_path is None:
        base_dir = "/Cimage"
        args.dst_path = tempfile.mkdtemp(dir=base_dir)
    
    print(f"Destination path: {args.dst_path}")
    download(src_path, args.dst_path)

    dataset_path_file = os.path.join(args.dst_path, args.version, "golden_dataset", "dataset_path.txt")

    if os.path.exists(dataset_path_file):
        with open(dataset_path_file, "r") as file:
            path = file.read()

        print(f"GCP location for dataset: {path}")
        
        download(path, 
                 os.path.join(args.dst_path, "golden_dataset"))
    else:
        print(f"File {dataset_path_file} does not exist.")
