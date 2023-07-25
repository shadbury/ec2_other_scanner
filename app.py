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

    Args:
        profile (str): AWS profile name

    Returns:
        list: List of regions
    """
    session = boto3.session.Session(profile_name=profile)
    regions = session.get_available_regions("ec2")
    successful_regions = []

    if regions is not None:
        for region in regions:
            try:
                client = session.client("ec2", region_name=region)
                client.describe_volumes()
                successful_regions.append(region)
                logger.info("Access to region successful: {}".format(region))
            except Exception as e:
                logger.warning("Access to region failed: {}".format(region))
    return successful_regions


def get_ebs_volumes(profile, region):
    """
    Get EBS volumes for the given region.

    Args:
        profile (str): AWS profile name
        region (str): AWS region

    Returns:
        EbsVolumes: EbsVolumes object
    """
    try:
        return EbsVolumes(profile, region)
    except Exception as e:
        logger.warning(f"Error fetching EBS volumes for region {region}: {str(e)}")
        return None

    
def get_unused_volumes(profile, region):
    '''
    Get a dictionary of unused EBS volumes and their potential savings

    Args:
        profile (str): AWS profile name
        region (str): AWS region

    Returns:
        EbsVolumes: EbsVolumes object
    '''
    ebs_volumes = EbsVolumes(profile, region)
    unused_volumes = ebs_volumes.get_unused_volumes()

    if unused_volumes:
        for volume_id, savings in unused_volumes.items():
            volume = ebs_volumes.get_volume_by_id(volume_id)
            if not volume['Attachments']:
                logger.warning("Unused volumes found. Calculating potential savings...")
                volume_type = volume['VolumeType']
                volume_size = volume['Size']
                # Default to 0.1 USD per GB if price not found
                price_per_gb = ebs_volumes.volume_pricing.get(volume_type, 0.1)
                savings = volume_size * price_per_gb
                unused_volumes[volume_id] = savings
        return ebs_volumes  # Return the EbsVolumes object
    else:
        pass
        return None




def create_unused_volumes_list(profile, regions):
    """
    Function to create the dictionary of EbsVolumes objects

    Args:
        profile (str): AWS profile name
        regions (list): List of AWS regions

    Returns:
        dict: Dictionary of EbsVolumes objects
    """
    logger.info("Getting list of EBS volumes...")
    region_potential_savings = {}
    for region in regions:
        try:
            ebs_volumes = get_unused_volumes(profile, region)
            if ebs_volumes and ebs_volumes.volumes:  # Check if ebs_volumes has volumes
                region_potential_savings[region] = ebs_volumes  # Store the EbsVolumes object in the dictionary
            else:
                logger.info(f"{region}: No volumes found.")
        except Exception as e:
            logger.error(f"Error occurred in {region}: {str(e)}", exc_info=True)
    return region_potential_savings



def get_potential_savings(profile, regions):
    """
    Function to get the potential savings from unused EBS volumes

    Args:
        profile (str): AWS profile name
        regions (list): List of AWS regions

    Returns:
        dict: Dictionary of unused EBS volumes and their potential savings
    """
    ebs_volumes_list = create_unused_volumes_list(profile, regions)
    region_potential_savings = {}
    for region, ebs_volumes in ebs_volumes_list.items():
        unused_volumes_savings = ebs_volumes.get_unused_volumes()
        if unused_volumes_savings:
            logger.info("Mapping unused volumes to savings: {}".format(unused_volumes_savings))
            region_potential_savings[region] = unused_volumes_savings

    return region_potential_savings


def create_ebs_volumes_dataframe(region_potential_savings, gp2_to_gp3_savings):
    """
    Function to create the dataframe of EBSVolumes objects

    Args:
        region_potential_savings (dict): Dictionary of EbsVolumes objects
        gp2_to_gp3_savings (dict): Dictionary of gp2 to gp3 savings

    Returns:
        DataFrame: DataFrame of EBSVolumes objects
    """
    logger.info("Generating report...")
    if not region_potential_savings:
        logger.warning("No data to create dataframe.")
        return None

    # Create a list of dictionaries for unused volumes
    ebs_volumes_list = []
    for region, ebs_volumes in region_potential_savings.items():
        for ebs_volume, savings in ebs_volumes.items():
            ebs_volume_data = {
                "Region": region,
                "ResourceType": "EBS Volume",
                "VolumeId": ebs_volume,
                "Findings": "Unused EBS Volume",
                "MonthlySavings": f"${savings:.2f}"
            }
            ebs_volumes_list.append(ebs_volume_data)

    # Create a list of dictionaries for gp2 to gp3 savings
    gp2_to_gp3_list = []
    for region, gp2_to_gp3_savings_dict in gp2_to_gp3_savings.items():
        for volume_id, estimated_savings in gp2_to_gp3_savings_dict.items():
            gp2_to_gp3_data = {
                "Region": region,
                "ResourceType": "EBS Volume",
                "VolumeId": volume_id,
                "Findings": "GP2 to GP3 Savings",
                "MonthlySavings": f"${estimated_savings:.2f}"
            }
            gp2_to_gp3_list.append(gp2_to_gp3_data)

    # Combine the two lists
    combined_list = ebs_volumes_list + gp2_to_gp3_list

    logger.info("Transform data into dataframe...")
    ebs_volumes_dataframe = pd.DataFrame(combined_list)

    return ebs_volumes_dataframe



def save_report_to_csv(ebs_volumes_dataframe, output_file):
    """
    Function to save the report as a CSV file

    Args:
        ebs_volumes_dataframe (DataFrame): DataFrame of EBSVolumes objects
        output_file (str): Output file name

    Returns:
        None
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

        # Sleep for a few seconds before opening the CSV file
        time.sleep(5)

        # Open the CSV file with conditional formatting
        open_files(csv_filepath)


def open_files(csv_file_path):
    """
    Function to open files

    Args:
        csv_file_path (str): CSV file path

    Returns:
        None
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
    region = sys.argv[2]
    try:
        session = boto3.session.Session(profile_name=profile)
        logger.info("Credentials loaded successfully")

    except Exception as e:
        if e == "ProfileNotFound":
            logger.error(f"Error Occurred: {str(e)}", exc_info=True)
        else:
            logger.error(
                f"Error occurred: AWS profile '{profile}' not found. Please check your credentials file (~/.aws/credentials)."
            )
        return

    try:
        # Get all available regions for the given profile
        if not region:
            regions = get_all_regions(profile)
        else:
            regions = [region]

        # Create the array of EbsVolumes objects and get potential savings
        region_potential_savings = get_potential_savings(profile, regions)

        # Get the estimated gp2 to gp3 savings
        gp2_to_gp3_savings = {}
        for region in regions:
            ebs_volumes = get_ebs_volumes(profile, region)
            if isinstance(ebs_volumes, EbsVolumes):  # Check if ebs_volumes is an instance of EbsVolumes
                gp2_to_gp3_savings[region] = ebs_volumes.get_gp2_to_gp3_savings()
            else:
                logger.warning(f"{region}: ebs_volumes is not an instance of EbsVolumes.")

        # Create DataFrame from the results and save the report
        ebs_volumes_dataframe = create_ebs_volumes_dataframe(
            region_potential_savings, gp2_to_gp3_savings)

        # Save the CSV report
        if ebs_volumes_dataframe is not None:
            # Save the CSV report for resources
            save_report_to_csv(ebs_volumes_dataframe, "ebs_volumes_report.csv")

            # Open the CSV file with conditional formatting
            open_files("reports/ebs_volumes_report.csv")
        else:
            logger.warning("No data to save.")

    except Exception as e:
        # Include traceback information
        logger.error(f"Error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
