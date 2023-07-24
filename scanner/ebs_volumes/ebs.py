import boto3
import json
from logger import get_logger

logger = get_logger()


class EbsVolumes:
    '''
    EBS volumes
    '''

    def __init__(self, profile, region):
        '''
        Initialise the class
        '''
        self.profile = profile
        self.region = region
        self.volumes = None
        self.volume_pricing = {}
        self.get_pricing_info()
        self.get_volumes()

    def get_pricing_info(self):
        '''
        Fetch the pricing information for EBS volumes
        '''

        logger.info("Getting Pricing Information...")

        ebs_name_map = {
            'standard': 'Magnetic',
            'gp2': 'General Purpose',
            'gp3': 'General Purpose',
            'io1': 'Provisioned IOPS',
            'st1': 'Throughput Optimized HDD',
            'sc1': 'Cold HDD'
        }

        logger.info("EBS name map: {}".format(ebs_name_map))

        try:
            #check if cache file exits, if it does, throw exception to force to use cache file
            pricing_region = 'us-east-1'
            logger.info("switch to us-east-1 to access pricing API...")
            session = boto3.Session(
                profile_name=self.profile, region_name=pricing_region)
            pricing = session.client('pricing')
            json_dump = {}
            for ebs_code in ebs_name_map:
                logger.info("Getting pricing for {}...".format(ebs_code))
                response = pricing.get_products(
                    ServiceCode='AmazonEC2',
                    Filters=[{
                        'Type': 'TERM_MATCH',
                        'Field': 'volumeType',
                        'Value': ebs_name_map[ebs_code]
                    },
                        {
                        'Type': 'TERM_MATCH',
                        'Field': 'location',
                        'Value': 'US East (N. Virginia)'
                    }])
                
                for product in response['PriceList']:
                    product_json = json.loads(product)
                    json_dump[product] = product
                    product_attributes = product_json['product']['attributes']
                    volume_type = product_attributes.get('volumeApiName')
                    if volume_type:
                        price_dimensions = product_json['terms']['OnDemand'].values()
                        price_per_unit = list(price_dimensions)[
                            0]['priceDimensions']
                        for price_dimension_key in price_per_unit:
                            price = price_per_unit[price_dimension_key]['pricePerUnit']['USD']
                            self.set_volume_pricing(volume_type, float(price))
                            logger.info("Pricing for {}: {}".format(volume_type, price))
                        continue
            with open(__file__+"products.json", "w") as outfile:
                        json.dump(json_dump, outfile)


        except Exception as e:
            logger.error(
                f"Error occurred while fetching pricing information: {str(e)}")
            logger.info("Looking for pricing information in local file...")
            try:
                with open(__file__+"products.json", "r") as infile:
                    products = json.load(infile)
                    for product in products:
                        product_json = json.loads(product)
                        product_attributes = product_json['product']['attributes']
                        volume_type = product_attributes.get('volumeApiName')
                        if volume_type:
                            price_dimensions = product_json['terms']['OnDemand'].values()
                            price_per_unit = list(price_dimensions)[
                                0]['priceDimensions']
                            for price_dimension_key in price_per_unit:
                                price = price_per_unit[price_dimension_key]['pricePerUnit']['USD']
                                self.set_volume_pricing(
                                    volume_type, float(price))
                                logger.info(
                                    "Pricing for {}: {}".format(volume_type, price))
                            continue
            except Exception as e:
                logger.error(
                    f"Error occurred while fetching pricing information from local file: {str(e)}", exc_info=True)

    def get_unused_volumes(self):
        '''
        Get a dictionary of unused EBS volumes and their potential savings
        '''
        unused_volumes = {}
        if self.volumes:
            logger.warning("Unused volumes found. Calculating potential savings...")
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
            logger.info("No volumes found. Skipping...")
            return None

    def set_volume_pricing(self, volume_type, price):
        '''
        Set the pricing for the given volume type
        '''
        self.volume_pricing[volume_type] = price

    def get_volumes(self):
        '''
        Get the EBS volumes for the given region
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
