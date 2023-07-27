from scanner.ebs_snapshots.snapshot import EBSSnapshots
import pandas as pd
from datetime import datetime, timezone
import scanner.util.logger as log

logger = log.get_logger()

def get_all_snapshots(profile, region):
    '''
    Function to get all EBS snapshots for the given region

    Args:
        profile (str): AWS profile name
        region (str): AWS region

    Returns:
        EBSSnapshots: EBSSnapshots object
    '''

    snapshots = EBSSnapshots(profile, region)

    return snapshots


def get_snapshot_age(snapshot):
    '''
    Function to get the age of the given snapshot

    Args:
        snapshot (dict): Snapshot details

    Returns:
        int: Age of the snapshot in days
    '''
    create_time = snapshot['StartTime']
    logger.debug("Snapshot creation time: {}".format(create_time))
    current_time = datetime.now(timezone.utc)
    logger.debug("Current time: {}".format(current_time))
    age = (current_time - create_time).days
    logger.debug("Snapshot age: {}".format(age))
    return age


def get_aws_snapshot_cost(profile, region):
    '''
    Function to get the cost of EBS snapshots for the given region

    Args:
        profile (str): AWS profile name
        region (str): AWS region

    Returns:
        list: List of EBS snapshots and their costs
        float: Total cost of EBS snapshots
    '''

    # Get the list of all snapshots in the region
    logger.info("Getting all snapshots...")
    snapshot_object = get_all_snapshots(profile, region)
    logger.debug("Snapshot object: {}".format(snapshot_object))
    snapshots = snapshot_object.get_snapshots(region)
    logger.debug("Snapshots: {}".format(snapshots))
    snapshot_price_per_gb_month = snapshot_object.snapshot_pricing
    logger.debug("Snapshot price per GB per month: {}".format(snapshot_price_per_gb_month))
    # Collect information about snapshots and their costs
    snapshots_info = []

    logger.info("Calculating the cost of snapshots...")
    for snapshot in snapshots['Snapshots']:
        snapshot_age = get_snapshot_age(snapshot)
        if snapshot_age > 365:
            logger.debug("Snapshot age is greater than 365 days ({}). Adding to the list...".format(snapshot_age))
            volume_size_gb = snapshot['VolumeSize']
            snapshot_cost = volume_size_gb * snapshot_price_per_gb_month

            snapshot_info = {
                'SnapshotId': snapshot['SnapshotId'],
                'VolumeId': snapshot['VolumeId'],
                'VolumeSize': snapshot['VolumeSize'],
                'AgeDays': snapshot_age,
                'CostUSD': snapshot_cost,
                'description': snapshot['Description']
            }
            snapshots_info.append(snapshot_info)
            logger.debug("Snapshot info: {}".format(snapshot_info))
        else:
            logger.debug("Snapshot: {} age is less than 365 days.({}) Skipping...".format(snapshot['SnapshotId'], snapshot_age))

    return snapshots_info

def create_snapshot_dataframe(snapshot_data):
    """
    Function to create the dataframe of snapshot data
    """

    # Create a list of dictionaries for snapshot data
    snapshot_list = []
    total_savings = 0

    logger.info("Generating the snapshot dataframe...")

    for region, snapshot_savings_dict in snapshot_data.items():
        for snapshot in snapshot_savings_dict:
            logger.debug("Snapshot: {}".format(snapshot))
            snapshot_cost = snapshot['CostUSD']
            volume_id = snapshot.get('VolumeId', '')
            snapshot_id = snapshot.get('SnapshotId', '')
            age_days = snapshot.get('AgeDays', '')
            snapshot_size = snapshot.get('VolumeSize', '')
            description = snapshot.get('description', '')

            snapshot_data = {
                "Region": region,
                "ResourceType": "EBS Snapshot",
                "VolumeId": volume_id,
                "SnapshotId": snapshot_id,
                "AgeDays": age_days,
                "SnapshotSizeGB": snapshot_size,  # Including the snapshot size in GB
                "Findings": "Snapshot Cost",
                "MonthlySavings": f"${snapshot_cost:.2f}",
                "Description": description
            }
            logger.debug('Snapshot data: {}'.format(snapshot_data))
            snapshot_list.append(snapshot_data)
            total_savings += snapshot_cost

    # Add a row for the total savings from snapshots
    total_savings_row = {
        "Region": "Total Savings",
        "ResourceType": "EBS Snapshot",
        "VolumeId": "",
        "SnapshotId": "",
        "AgeDays": "",
        "SnapshotSizeGB": "",
        "Findings": "",
        "MonthlySavings": f"${total_savings:.2f}"
    }
    logger.debug("Total savings row: {}".format(total_savings_row))
    snapshot_list.append(total_savings_row)

    # Create a DataFrame for snapshots
    snapshot_dataframe = pd.DataFrame(snapshot_list)

    return snapshot_dataframe