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


import boto3
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_all_snapshots(profile, region):
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client('ec2')

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
        list: List of dictionaries containing information about each EBS snapshot:
            - 'SnapshotId': str
            - 'VolumeId': str
            - 'VolumeSize': int (in GB)
            - 'AgeDays': int
            - 'CostUSD': float (snapshot cost)
            - 'description': str (snapshot description)
            - 'RetentionPolicy': str (e.g., 'Keep Forever', '7 days', etc.)
            - 'SnapshotFrequency': str (e.g., 'Daily', 'Weekly', etc.)
            - 'SnapshotSizeChange': float (size change from the previous snapshot in GB)
            - 'IsUnused': bool (True if snapshot is not associated with any AMI, False otherwise)
        float: Total cost of EBS snapshots
    '''

    # Get all snapshots for the given region
    logger.info("Getting all snapshots...")
    snapshot_object = get_all_snapshots(profile, region)
    logger.debug("Snapshot object: {}".format(snapshot_object))
    snapshots = snapshot_object.describe_snapshots(OwnerIds=['self'])
    snapshot_price_per_gb_month = 0.05  # Set the appropriate snapshot price per GB per month
    logger.debug("Snapshot price per GB per month: {}".format(snapshot_price_per_gb_month))

    # Collect information about snapshots and their costs
    snapshots_info = []

    logger.info("Sorting snapshots by creation time...")
    sorted_snapshots = sorted(snapshots['Snapshots'], key=lambda s: s['StartTime'])

    logger.info("Calculating the cost of snapshots...")
    previous_snapshot = None

    for snapshot in sorted_snapshots:
        snapshot_age = get_snapshot_age(snapshot)
        volume_id = snapshot['VolumeId']

        if snapshot_age >= 365:
            # If the snapshot is within 365 days and snapshot_age is not None, calculate its cost
            if previous_snapshot is not None:
                size_difference_gb = snapshot['VolumeSize'] - previous_snapshot['VolumeSize']
                snapshot_cost = abs(size_difference_gb) * snapshot_price_per_gb_month
                snapshot_cost = snapshot_cost/2

                logger.info(f"SnapshotId: {snapshot['SnapshotId']}, "
                            f"VolumeId: {volume_id}, "
                            f"VolumeSize: {snapshot['VolumeSize']} GB, "
                            f"AgeDays: {snapshot_age}, "
                            f"SizeDifferenceGB: {size_difference_gb} GB, "
                            f"CostUSD: {snapshot_cost} USD, "
                            f"RetentionPolicy: Keep Forever, "  # Set the retention policy here
                            f"SnapshotFrequency: Daily, "  # Set the snapshot frequency here
                            f"SnapshotSizeChange: {size_difference_gb} GB, "
                            f"IsUnused: True")  # Set the unused status here (True if unused)

                snapshot_info = {
                    'SnapshotId': snapshot['SnapshotId'],
                    'VolumeId': volume_id,
                    'VolumeSize': snapshot['VolumeSize'],
                    'AgeDays': snapshot_age,
                    'CostUSD': snapshot_cost,
                    'description': snapshot.get('Description', ''),
                    'RetentionPolicy': 'Keep Forever',  # You can set the retention policy here
                    'SnapshotFrequency': 'Daily',  # You can set the snapshot frequency here
                    'SnapshotSizeChange': size_difference_gb,
                    'IsUnused': True,  # You can check if the snapshot is unused and set this flag accordingly
                }
                snapshots_info.append(snapshot_info)

            # Update the previous_snapshot with the current snapshot
            previous_snapshot = snapshot



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