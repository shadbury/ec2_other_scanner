import sys
import pandas as pd
import subprocess
import os
from scanner.logger import configure_logger
from scanner.ebs_volumes.ebs import EbsVolumes
import boto3
import time

# Configure the logger to send logs to the logger.py file
logger = configure_logger("app.log")


def get_all_regions(profile):
    """
    Function to get all available regions for the given profile
    """
    session = boto3.session.Session(profile_name=profile)
    regions = session.get_available_regions("ec2")
    successful_regions = []

    if regions is not None:
        for region in regions:
            try:
                logger.info("Access to region successful: {}".format(region))
                client = session.client("ec2", region_name=region)
                client.describe_volumes()
                successful_regions.append(region)
            except Exception as e:
                logger.warning("Access to region failed: {}".format(region))
    return successful_regions


def get_ebs_volumes(profile, region):
    """
    Function to get EBS volumes for a specific region
    """
    try:
        ebs_volumes = EbsVolumes(profile, region)
        logger.info("Looking for Unused EBS Volumes in {}".format(region))
        unused_volumes = ebs_volumes.get_unused_volumes()

        return unused_volumes
    except Exception as e:
        logger.error(f"Error occurred in {region}: {str(e)}", exc_info=True)
        return None


def create_ebs_volumes_list(profile, regions):
    """
    Function to create the array of EbsVolumes objects
    """
    logger.info("Getting list of EBS volumes...")
    ebs_volumes_list = []
    for region in regions:
        try:
            ebs_volumes = get_ebs_volumes(profile, region)
            if ebs_volumes: 
                ebs_volumes_list.append((ebs_volumes, region))
                logger.warning(f"{region}: {len(ebs_volumes)} volumes found.")
        except Exception as e:
            logger.error(f"Error occurred in {region}: {str(e)}", exc_info=True)
    return ebs_volumes_list


def get_potential_savings(profile, regions):
    """
    Function to get the potential savings from unused EBS volumes
    """
    ebs_volumes_list = create_ebs_volumes_list(profile, regions)
    region_potential_savings = {}
    for ebs_volumes, region in ebs_volumes_list:
        unused_volumes_savings = ebs_volumes
        if unused_volumes_savings:
            logger.info("Mapping unused volumes to savings: {}".format(unused_volumes_savings))
            region_potential_savings[region] = unused_volumes_savings

    return region_potential_savings


def create_ebs_volumes_dataframe(region_potential_savings):
    """
    Function to create the dataframe of EBSVolumes objects
    """
    logger.info("Generating report...")
    if not region_potential_savings:
        logger.warning("No data to create dataframe.")
        return None, None
    logger.info("Transform data into dataframe: {}".format(region_potential_savings))
    
    # Create a list of EbsVolumes objects
    ebs_volumes_list = []
    for region, ebs_volumes in region_potential_savings.items():
        for ebs_volume in ebs_volumes:
            ebs_volume_data = {
                "Region": region,
                "ResourceType": "EBS Volume",
                "VolumeId": ebs_volume,
                "Findings": "Unused EBS Volume",
                "MonthlySavings": f"${ebs_volumes[ebs_volume]:.2f}"
            }
            logger.info("EBS Volume: {}".format(ebs_volume_data))
            ebs_volumes_list.append(ebs_volume_data)
        logger.info("Completed transformation into dataframe in region: {}".format(region))
    logger.info("No more regions to check...")
   # Create a dataframe from the list of dictionaries
    ebs_volumes_dataframe = pd.DataFrame(ebs_volumes_list)

    return ebs_volumes_dataframe


def save_report_to_csv(ebs_volumes_dataframe, output_file):
    """
    Function to save the report as a CSV file
    """
    logger.info("Saving report...")
    if ebs_volumes_dataframe is None:
        logger.warning("No data to save.")
    else:
        report_folder = "reports"
        if not os.path.exists(report_folder):
            os.makedirs(report_folder)

        csv_filepath = os.path.join(report_folder, output_file)
        df = pd.DataFrame(ebs_volumes_dataframe)
        df.to_csv(csv_filepath, index=False)
        logger.info(f"CSV report saved as {csv_filepath}")
    time.sleep(5)


def open_files(csv_file_path):
    """
    Function to open files
    """
    logger.info("Opening Report...")
    try:
        subprocess.run(["open", csv_file_path])
    except Exception as e:
        logger.error(f"Error occurred while opening files: {str(e)}")


def main():
    """
    Main function
    """

    # Check if the AWS profile is provided
    if len(sys.argv) < 2:
        logger.error(
            "Error occurred: Please provide the AWS profile as the first command-line argument. Example: python3 app.py my_aws_profile"
        )
        return

    profile = sys.argv[1]
    try:
         session = boto3.session.Session(profile_name=profile)
         logger.info("Credentials loaded successfully")

    except Exception as e:
        if e ==  "ProfileNotFound":
            logger.error(f"Error Occured: {str(e)}", exc_info=True)
        else:
            logger.error(
                f"Error occurred: AWS profile '{profile}' not found. Please check your credentials file (~/.aws/credentials)."
            )
        return
    try:
        # Get all available regions for the given profile
        #regions = get_all_regions(profile)
        regions = ["ap-southeast-2"]

        # Create the array of EbsVolumes objects and get potential savings
        region_potential_savings = get_potential_savings(profile, regions)

        # Create DataFrame from the results and save the report
        ebs_volumes_dataframe = create_ebs_volumes_dataframe(region_potential_savings)

        # Save the CSV report
        if ebs_volumes_dataframe is not None:
            # Save the CSV report for resources
            save_report_to_csv(ebs_volumes_dataframe, "ebs_volumes_report.csv")

            
            open_files("reports/ebs_volumes_report.csv")
        else:
            logger.warning("No data to save.")

    except Exception as e:
        # Include traceback information
        logger.error(f"Error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
