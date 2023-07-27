from scanner.ebs_snapshots.snapshot import EBSSnapshots
from scanner.util.aws_functions import get_price
import json
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
    # Get the age of the snapshot in days
    create_time = snapshot['StartTime']
    current_time = datetime.now(timezone.utc)
    age = (current_time - create_time).days
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
    snapshot_object = get_all_snapshots(profile, region)
    snapshots = snapshot_object.get_snapshots(region)
    snapshot_price_per_gb_month = snapshot_object.snapshot_pricing
    # Collect information about snapshots and their costs
    snapshots_info = []

    logger.info("Calculating the cost of EBS snapshots...")
    for snapshot in snapshots['Snapshots']:
        snapshot_age = get_snapshot_age(snapshot)
        if snapshot_age > 365:
            volume_size_gb = snapshot['VolumeSize']
            snapshot_cost = volume_size_gb * snapshot_price_per_gb_month

            snapshot_info = {
                'SnapshotId': snapshot['SnapshotId'],
                'VolumeId': snapshot['VolumeId'],
                'AgeDays': snapshot_age,
                'CostUSD': snapshot_cost
            }
            snapshots_info.append(snapshot_info)

    return snapshots_info