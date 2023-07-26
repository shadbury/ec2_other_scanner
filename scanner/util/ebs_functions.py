import scanner.util.logger as log
from scanner.ebs_volumes.ebs import EbsVolumes
import pandas as pd


logger = log.get_logger()

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
    
def get_unused_volume_savings(profile, regions):
    """
    Function to get the potential savings from unused EBS volumes

    Args:
        profile (str): AWS profile name
        regions (list): List of AWS regions

    Returns:
        dict: Dictionary of unused EBS volumes and their potential savings
    """
    ebs_volumes_list = get_unused_volumes_by_region(profile, regions)
    region_potential_savings = {}
    for region, ebs_volumes in ebs_volumes_list.items():
        unused_volumes_savings = ebs_volumes.get_unused_volumes()
        if unused_volumes_savings:
            logger.info("Mapping unused volumes to savings: {}".format(unused_volumes_savings))
            region_potential_savings[region] = unused_volumes_savings

    return region_potential_savings
    

def get_unused_volumes_by_region(profile, regions):
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


def create_ebs_volumes_dataframe(region_potential_savings, gp2_to_gp3_savings):
    """
    Function to create the dataframe of EBSVolumes objects
    """
    logger.info("Generating report...")
    if not region_potential_savings:
        logger.warning("No data to create dataframe.")
        return None

    # Create a list of dictionaries for unused volumes
    ebs_volumes_list = []
    total_savings = 0  # Initialize total savings

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
            total_savings += savings  # Add savings to the total

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

    # Add a row for the total savings
    total_savings_row = {
        "Region": "Total Savings",
        "ResourceType": "EBS Volume",
        "VolumeId": "",
        "Findings": "",
        "MonthlySavings": f"${total_savings:.2f}"
    }
    combined_list.append(total_savings_row)

    logger.info("Transform data into dataframe...")
    ebs_volumes_dataframe = pd.DataFrame(combined_list)

    return ebs_volumes_dataframe