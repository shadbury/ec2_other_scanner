import boto3
import json
from scanner.logger import get_logger
import os

logger = get_logger()

class EbsVolumes:
    '''
    EBS volumes
    '''

    pricing_info = {}

    ebs_name_map = {
        'standard': 'Magnetic',
        'gp2': 'General Purpose',
        'gp3': 'General Purpose',
        'io1': 'Provisioned IOPS',
        'st1': 'Throughput Optimized HDD',
        'sc1': 'Cold HDD'
    }

    def __init__(self, profile, region):
        '''
        Initialise the class

        Args:
            profile (str): AWS profile name
            region (str): AWS region

        Returns:
            None
        '''
        self.profile = profile
        self.region = region
        self.volumes = None
        self.volume_pricing = {}
        if not EbsVolumes.pricing_info:
            self.get_pricing_info()
        else:
            logger.debug("Price list already exists. Skipping...")
            self.volume_pricing = EbsVolumes.pricing_info
        self.get_volumes()

    @staticmethod
    def get_pricing_info():
        '''
        Fetch the pricing information for EBS volumes

        Args:
            None

        Returns:
            None
        '''
        logger.info("Getting Pricing Information...")

        try:
            # Check if cache file exists, if it does, throw an exception to force using the cache file
            pricing_region = 'us-east-1'
            logger.info("Switching to us-east-1 to access pricing API...")
            session = boto3.Session(profile_name=None, region_name=pricing_region)
            pricing = session.client('pricing')
            json_dump = {}

            for ebs_code in EbsVolumes.ebs_name_map:
                logger.info("Getting pricing for {}...".format(ebs_code))
                response = pricing.get_products(
                    ServiceCode='AmazonEC2',
                    Filters=[
                        {
                            'Type': 'TERM_MATCH',
                            'Field': 'volumeType',
                            'Value': EbsVolumes.ebs_name_map[ebs_code]
                        },
                        {
                            'Type': 'TERM_MATCH',
                            'Field': 'location',
                            'Value': 'US East (N. Virginia)'
                        }
                    ]
                )
                
                for product in response['PriceList']:
                    product_json = json.loads(product)
                    json_dump[product] = product
                    product_attributes = product_json['product']['attributes']
                    volume_type = product_attributes.get('volumeApiName')
                    if volume_type:
                        price_dimensions = product_json['terms']['OnDemand'].values()
                        price_per_unit = list(price_dimensions)[0]['priceDimensions']
                        for price_dimension_key in price_per_unit:
                            price = price_per_unit[price_dimension_key]['pricePerUnit']['USD']
                            EbsVolumes.set_volume_pricing(volume_type, float(price))
                            logger.info("Pricing for {}: {}".format(volume_type, price))
                        continue

            cache_file_path = os.path.join(os.path.dirname(__file__), "products.json")
            with open(cache_file_path, "w") as outfile:
                json.dump(json_dump, outfile)

        except Exception as e:
            logger.error(
                f"Error occurred while fetching pricing information: {str(e)}")
            logger.info("Looking for pricing information in the local file...")
            try:
                cache_file_path = os.path.join(os.path.dirname(__file__), "products.json")
                with open(cache_file_path, "r") as infile:
                    products = json.load(infile)
                    for product in products:
                        product_json = json.loads(product)
                        product_attributes = product_json['product']['attributes']
                        volume_type = product_attributes.get('volumeApiName')
                        if volume_type:
                            price_dimensions = product_json['terms']['OnDemand'].values()
                            price_per_unit = list(price_dimensions)[0]['priceDimensions']
                            for price_dimension_key in price_per_unit:
                                price = price_per_unit[price_dimension_key]['pricePerUnit']['USD']
                                EbsVolumes.set_volume_pricing(volume_type, float(price))
                                logger.info(
                                    "Pricing for {}: {}".format(volume_type, price))
                            continue
            except Exception as e:
                logger.error(
                    f"Error occurred while fetching pricing information from the local file: {str(e)}", exc_info=True)

    def get_unused_volumes(self):
        '''
        Get a dictionary of unused EBS volumes and their potential savings

        Args:
            None

        Returns:
            dict: Dictionary of unused EBS volumes and their potential savings
        '''
        unused_volumes = {}
        if self.volumes:
            for volume in self.volumes:
                if not volume['Attachments']:
                    volume_type = volume['VolumeType']
                    volume_size = volume['Size']
                    # Default to 0.1 USD per GB if price not found
                    price_per_gb = self.volume_pricing.get(volume_type, 0.1)
                    savings = volume_size * price_per_gb
                    unused_volumes[volume['VolumeId']] = savings
            return unused_volumes
        else:
            return None

    @staticmethod
    def set_volume_pricing(volume_type, price):
        '''
        Set the pricing for the given volume type

        Args:
            volume_type (str): Volume type
            price (float): Price per GB

        Returns:
            None
        '''
        EbsVolumes.pricing_info[volume_type] = price

    def get_volumes(self):
        '''
        Get the EBS volumes for the given region

        Args:
            None

        Returns:
            list: List of EBS volumes
        '''
        try:
            session = boto3.Session(
                profile_name=self.profile, region_name=self.region)
            ec2 = session.client('ec2')
            response = ec2.describe_volumes()
            self.volumes = response['Volumes']
            self.volumes_fetched = True
            return self.volumes
        except Exception as e:
            pass

    def get_gp2_to_gp3_savings(self):
        """
        Calculate the estimated gp2 to gp3 savings for each gp2 volume

        Args:
            None

        Returns:
            dict: Dictionary of gp2 to gp3 savings
        """
        gp2_to_gp3_savings = {}
        if self.volumes:
            for volume in self.volumes:
                if volume['VolumeType'] == 'gp2':
                    logger.warning("GP2 volumes found. Calculating potential savings...")
                    volume_size = volume['Size']
                    gp2_price_per_gb = self.volume_pricing.get('gp2', 0.1)
                    gp3_price_per_gb = self.volume_pricing.get('gp3', 0.08)
                    gp2_savings = volume_size * gp2_price_per_gb
                    gp3_savings = volume_size * gp3_price_per_gb
                    gp2_to_gp3_savings[volume['VolumeId']] = gp2_savings - gp3_savings
        return gp2_to_gp3_savings

    def get_volume_by_id(self, volume_id):
        '''
        Get the EBS volume by its ID

        Args:
            volume_id (str): Volume ID

        Returns:
            dict: EBS volume
        '''
        if self.volumes:
            for volume in self.volumes:
                if volume['VolumeId'] == volume_id:
                    return volume
        return None
