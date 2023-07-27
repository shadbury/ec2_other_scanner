import boto3
import scanner.util.logger as log
import pandas as pd


logger = log.get_logger()

def get_all_regions(profile, session):
    '''
    Function to get all available regions for the given profile

    Args:
        profile (str): AWS profile name

    Returns:
        list: List of regions
    '''
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



def get_aws_session(profile):
    '''
    Function to get the AWS session

    Args:
        profile (str): AWS profile name

    Returns:
        boto3.session.Session: AWS session
    '''
    return boto3.session.Session(profile_name=profile)


def get_price(profile, service_code, filters):
    '''
    Function to get the price for the given service code and filters
    
    Args:
        service_code (str): AWS service code
        filters (list): List of filters

    Returns:
        float: Price
    '''
    session = get_aws_session(profile)
    pricing_client = session.client('pricing', region_name='us-east-1')

    response = pricing_client.get_products(ServiceCode=service_code, Filters=filters, MaxResults=1)
    return response



def get_ebs_volumes(profile, region):
    '''
    Function to get the EBS volumes for the given region

    Args:
        None

    Returns:
        list: List of EBS volumes
    '''
    session = get_aws_session(profile)
    ec2 = session.client('ec2', region_name=region)
    response = ec2.describe_volumes()

    return response

def get_ebs_snapshots(profile, region):
    '''
    Function to get the EBS snapshots for the given region

    Args:
        region (str): AWS region

    Returns:
        list: List of EBS snapshots
    '''
    session = get_aws_session(profile)
    ec2 = session.client('ec2', region_name=region)
    response = ec2.describe_snapshots(OwnerIds=['self'])

    return response
