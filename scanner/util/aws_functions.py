import boto3
import scanner.util.logger as log
import pandas as pd


logger = log.get_logger()

def get_all_regions(profile):
    '''
    Function to get all available regions for the given profile

    Args:
        profile (str): AWS profile name

    Returns:
        list: List of regions
    '''
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



def get_aws_session(profile):
    '''
    Function to get the AWS session

    Args:
        profile (str): AWS profile name

    Returns:
        boto3.session.Session: AWS session
    '''
    return boto3.session.Session(profile_name=profile)


def get_price(service_code, filters):
    '''
    Function to get the price for the given service code and filters
    
    Args:
        service_code (str): AWS service code
        filters (list): List of filters

    Returns:
        float: Price
    '''
    pricing_client = boto3.client('pricing', region_name='us-east-1')

    response = pricing_client.get_products(ServiceCode=service_code, Filters=filters, MaxResults=1)
    return response



def get_ebs_volumes():
    '''
    Function to get the EBS volumes for the given region

    Args:
        None

    Returns:
        list: List of EBS volumes
    '''

    ec2 = boto3.client('ec2')
    response = ec2.describe_volumes()

    return response
