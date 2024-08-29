import os
import subprocess
import json
import configparser

def load_ini_values(ini_file_path):
    """
    Load values from an INI file.

    :param ini_file_path: Path to the INI file
    :return: Dictionary with INI values
    """
    config = configparser.ConfigParser()
    config.read(ini_file_path)

    # Extract values from the INI file
    params = dict(config['deployment_params'])
    vars_content = dict(config['vars_content'])

    return params, vars_content

def clone_repository(repo_url, clone_dir):
    """
    Clone a Git repository using SSH.

    :param repo_url: URL of the repository
    :param clone_dir: Directory to clone the repository into
    """
    if not os.path.exists(clone_dir):
        print(f"Cloning repository from {repo_url} to {clone_dir}...")
        ssh_command = "GIT_SSH_COMMAND='ssh -i /home/vimaan/key/gitlabpb.key' git clone --quiet --depth 1 --recurse-submodules --shallow-submodules"
        full_command = f"{ssh_command} {repo_url} {clone_dir}"
        subprocess.run(full_command, shell=True, check=True)
    else:
        print(f"Repository already cloned in {clone_dir}")

def update_git_submodules(repo_dir):
    """
    Initialize and update Git submodules.

    :param repo_dir: Directory containing the Git repository
    """
    print(f"Updating Git submodules in {repo_dir}...")
    os.chdir(repo_dir)
    subprocess.run(["git", "submodule", "update", "--init"], check=True)

def launch():
    # Define repository URL and directory
    repo_url = "git@gitlab.com:vimaanrobotics/devops/deployments.git"
    repo_dir = os.path.join(os.getcwd(), "deployment")

    # Clone the repository
    clone_repository(repo_url, repo_dir)

    # Load values from INI file
    ini_file_path = "/Cimage/vibhanshu/files/deployment_config.ini"  # Path to your INI file
    params, vars_content = load_ini_values(ini_file_path)

    # Define variables from the INI file content
    inventory = params.get("inventory", "default_inventory")
    facility_code = params.get("facility_code", "default_facility_code")
    pipeline_count = params.get("pipeline_count", "default_pipeline_count")
    pipeline_config_version = params.get("pipeline_config_version", "default_pipeline_config_version")
    only_config_update = params.get("only_config_update", "false")
    deployment_config_version = params.get("deployment_config_version", "default_deployment_config_version")
    selective_service_deployment = params.get("selective_service_deployment", "true")

    # Navigate to the already cloned repo directory
    os.chdir(repo_dir)

    # Checkout the specific version
    subprocess.run(["git", "checkout", "v2.2.9.patch4"])
    print("Current working directory:", os.getcwd())

    # Change to the ansible directory
    os.chdir("ansible")

    # Populate the vars file
    vars_file_path = "vars/st_mhe_with_triton_vars.json"

    # Write the vars content to the file
    with open(vars_file_path, "w") as vars_file:
        json.dump(vars_content, vars_file, indent=4)

    # Build the ansible-playbook command
    cmd = [
        "sudo", "ansible-playbook", "st_mhe_with_triton.yaml",
        "-i", f"inventory/{inventory}",
        "-i", "inventory/strategy",
        "-e", f"json_file={vars_file_path}",
        "-e", f"@{vars_file_path}",
        "-e", f"facility_code={facility_code}",
        "-e", f"selective_service_deployment={selective_service_deployment}",
        "-e", f"pipeline_count={pipeline_count}",
        "-e", f"pipeline_config_version={pipeline_config_version}",
        "-e", f"only_config_update={only_config_update}",
        "-e", f"deployment_config_version={deployment_config_version}"
    ]

    # Run the command
    subprocess.run(cmd)
    print("Deployment completed.")

if __name__ == "__main__":
    launch()
