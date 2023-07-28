import json
import scanner.util.logger as log
from scanner.util.aws_functions import get_price, get_ebs_volumes
import os
import mmap

logger = log.get_logger()

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

    def get_pricing_info(self):
        '''
        Fetch the pricing information for EBS volumes

        Args:
            None

        Returns:
            None
        '''
        json_dump = {}
        cache_file_path = os.path.join(os.path.dirname(__file__), "products.json")
        if not os.path.exists(cache_file_path):
            for ebs_code in self.ebs_name_map:
            

                filters=[
                    {
                    'Type': 'TERM_MATCH',
                    'Field': 'volumeType',
                    'Value': self.ebs_name_map[ebs_code]
                    },
                    {
                        'Type': 'TERM_MATCH',
                        'Field': 'location',
                        'Value': 'US East (N. Virginia)'
                    }
                    ]
                service_code='AmazonEC2'
                price = None

                try:
                    
                    price = get_price(self.profile, service_code, filters)
                    with open(cache_file_path, "w") as outfile:
                        json.dump(json_dump, outfile)

                except Exception as e:
                    logger.error(
                        f"Error occurred while fetching pricing information: {str(e)}", exc_info=True)
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
                            self.set_volume_pricing(volume_type, float(price))
                            logger.info(
                                "Pricing for {}: {}".format(volume_type, price))
                            continue
        except Exception as e:
            logger.error(
                f"Error occurred while fetching pricing information from the local file: {str(e)}. Try removing the file and re-running the app", exc_info=True)


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

    def get_volumes(self, region):
        '''
        Get the EBS volumes for the given region

        Args:
            None

        Returns:
            list: List of EBS volumes
        '''
        try:
            

            self.volumes = get_ebs_volumes(self.profile, region)
            self.volumes_fetched = True
            return self.volumes
        except Exception as e:
            logger.error('Error occurred while fetching EBS volumes: {}'.format(str(e)), exc_info=True)