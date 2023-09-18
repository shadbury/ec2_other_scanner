import scanner.util.logger as log
from scanner.ebs_volumes.ebs import EbsVolumes
import pandas as pd


logger = log.get_logger()

volumes = []

def get_all_volumes(profile, region):
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
    

def get_gp2_to_gp3_savings(ebs_volumes, region):
    """
    Calculate the estimated gp2 to gp3 savings for each gp2 volume

    Args:
        None

    Returns:
        dict: Dictionary of gp2 to gp3 savings
    """
    gp2_to_gp3_savings = {}
    volumes = ebs_volumes.get_volumes(region)
    if volumes:
        for volume in volumes['Volumes']:
            if volume['VolumeType'] == 'gp2':
                logger.warning("GP2 volumes found. Calculating potential savings...")
                volume_size = volume['Size']
                gp2_price_per_gb = ebs_volumes.volume_pricing.get('gp2', 0.1)
                gp3_price_per_gb = ebs_volumes.volume_pricing.get('gp3', 0.08)
                gp2_savings = volume_size * gp2_price_per_gb
                gp3_savings = volume_size * gp3_price_per_gb
                gp2_to_gp3_savings[volume['VolumeId']] = gp2_savings - gp3_savings
    return gp2_to_gp3_savings

    
def get_unused_volume_savings(profile, regions):
    """
    Function to get the potential savings from unused EBS volumes

    Args:
        profile (str): AWS profile name
        regions (list): List of AWS regions

    Returns:
        dict: Dictionary of unused EBS volumes and their potential savings
    """

    def get_unused_volumes_and_savings(volumes, region):
        '''
        Get a dictionary of unused EBS volumes and their potential savings

        Args:
            profile (str): AWS profile name
            region (str): AWS region

        Returns:
            EbsVolumes: EbsVolumes object
        '''
        ebs_volumes = volumes.get_volumes(region)
        unused_volumes = {}
        if ebs_volumes:
            for ebs in ebs_volumes['Volumes']:
                volume_id = ebs['VolumeId']
                if not ebs['Attachments']:
                    volume_type = ebs['VolumeType']
                    volume_size = ebs['Size']
                    # Default to 0.1 USD per GB if price not found
                    price_per_gb = volumes.volume_pricing.get(volume_type, 0.1)
                    savings = volume_size * price_per_gb
                    unused_volumes[volume_id] = savings
            return unused_volumes  # Return the EbsVolumes object
        else:
            pass
            return None
        
    def get_unused_volumes_in_region(profile, regions):
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
                logger.info("Checking for volumes in {}...".format(region))
                all_volumes = EbsVolumes(profile, region)
                unused_volumes = get_unused_volumes_and_savings(all_volumes, region)
                if unused_volumes:
                    logger.warning("Unused volumes: {}".format(unused_volumes))
                    region_potential_savings[region] = unused_volumes
                else:
                    logger.info(f"{region}: No volumes found.")
            except Exception as e:
                logger.error(f"Error occurred in {region}: {str(e)}", exc_info=True)
        return region_potential_savings




    ebs_volumes_list = get_unused_volumes_in_region(profile, regions)
    savings = {}
    unused_potential_savings = {}
    
    for region, ebs_volumes in ebs_volumes_list.items():
        unused_volumes = ebs_volumes_list[region]
        for volume in unused_volumes.items():
            volume_id = volume[0]
            savings = volume[1]
            
            savings = {
                "VolumeId" : volume_id, 
                "Savings" : float(savings)
                }
            try:
                logger.debug("Mapping Unused Volume: {} to savings: {}".format(volume_id, savings))
                if not region in unused_potential_savings:
                    unused_potential_savings[region] = []
                unused_potential_savings[region].insert(len(unused_potential_savings[region]), savings)
            except Exception as e:
                logger.error(f"Error Occurred: {str(e)}", exc_info=True)
    return unused_potential_savings
    


def create_ebs_dataframe(dataframe):
    """
    Function to create the dataframe of EBSVolumes objects

    Args:
        dataframe (dict): Dictionary of EBSVolumes objects

    Returns:
        pandas.DataFrame: Dataframe of EBSVolumes objects
    """
    logger.info("Creating dataframe...")
    unused = dataframe['unused']
    gp2 = dataframe['gp2']
    logger.info("Generating report...")
    if not unused and not gp2:
        logger.warning("No data to create dataframe.")
        return None

    # Create a list of dictionaries for unused volumes
    ebs_volumes_list = []
    logger.info("Creating Unused Volumes dataframe...")
    total_savings = 0  # Initialize total savings
    for region, ebs_volumes in unused.items():
        logger.debug("Region: {}".format(region))
        logger.debug("Transforming data: {}...".format(ebs_volumes))
        for volume in ebs_volumes:
            ebs_volume_data = {
                "Region": region,
                "ResourceType": "EBS Volume",
                "VolumeId": volume['VolumeId'],
                "Findings": "Unused EBS Volume",
                "MonthlySavings": f"${volume['Savings']:.2f}"
            }
            logger.debug("Transformed data: {}".format(ebs_volume_data))
            ebs_volumes_list.append(ebs_volume_data)
            total_savings += volume['Savings'] # Add savings to the total

    # Create a list of dictionaries for gp2 to gp3 savings
    gp2_to_gp3_list = []
    logger.info("Creating GP2 to GP3 Savings dataframe...")
    for region, gp2_to_gp3_savings_dict in gp2.items():
        for volume_id, estimated_savings in gp2_to_gp3_savings_dict.items():
            logger.debug("Region: {}".format(region))
            logger.debug("Transforming data: {}...".format(gp2_to_gp3_savings_dict))
            gp2_to_gp3_data = {
                "Region": region,
                "ResourceType": "EBS Volume",
                "VolumeId": volume_id,
                "Findings": "GP2 to GP3 Savings",
                "MonthlySavings": f"${estimated_savings:.2f}"
            }
            logger.debug("Transformed data: {}".format(gp2_to_gp3_data))
            gp2_to_gp3_list.append(gp2_to_gp3_data)
            total_savings += estimated_savings # Add savings to the total

    # Combine the two lists
    logger.info("combining lists...")
    combined_list = ebs_volumes_list + gp2_to_gp3_list
    logger.debug('Combined list: {}'.format(combined_list))

    # Add a row for the total savings
    total_savings_row = {
        "Region": "Total Savings",
        "ResourceType": "EBS Volume",
        "VolumeId": "",
        "Findings": "",
        "MonthlySavings": f"${total_savings:.2f}"
    }
    logger.info("Adding total savings row...")
    logger.debug("Total savings row: {}".format(total_savings_row))
    combined_list.append(total_savings_row)

    logger.info("Transform data into dataframe...")
    ebs_volumes_dataframe = pd.DataFrame(combined_list)

    return ebs_volumes_dataframe