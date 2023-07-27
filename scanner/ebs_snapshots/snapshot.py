import json
from scanner.util.aws_functions import get_price, get_ebs_snapshots
import scanner.util.logger as log
import os

logger = log.get_logger()

class EBSSnapshots:



    def __init__(self, profile, region):
        self.profile = profile
        self.region = region
        self.snapshots = None
        self.snapshot_pricing = None
        if not self.snapshot_pricing:
            self.get_ebs_snapshot_price()




    def get_ebs_snapshot_price(self):
        '''
        Fetch the pricing information for EBS snapshots

        Args:
            None

        Returns:
            float: Price per GB of EBS snapshots
        '''
        logger.info("Getting EBS snapshot cost...")
        region_code_map = {
            'eu-central-1': 'EUC1',
            'eu-west-1': 'EU',
            'eu-west-2': 'EUW2',
            'eu-west-3': 'EUW3',
            'us-east-1': 'USE1',
            'us-east-2': 'USE2',
            'us-west-1': 'USW1',
            'us-west-2': 'USW2',
            'ap-south-1': 'APS3',
            'ap-northeast-1': 'APN1',
            'ap-northeast-2': 'APN2',
            'ap-southeast-1': 'APS1',
            'ap-southeast-2': 'APS2',
            'ap-east-1': 'APE1',
            'sa-east-1': 'SAE1',
            'ca-central-1': 'CAN1',
            'cn-north-1': 'CNN1',
            'cn-northwest-1': 'CNN2',
            'me-south-1': 'MES1',
            'af-south-1': 'AFS1',
            'eu-south-1': 'EUS1',
            'us-gov-east-1': 'UGW1',
            'us-gov-west-1': 'UGW2',
            'us-iso-east-1': 'UIE1',
            'us-isob-east-1': 'UIE2',
        }

        filters=[
                {
                    "Type": "TERM_MATCH",
                    "Field": "usagetype",
                    "Value": (region_code_map[self.region] + "-EBS:SnapshotUsage")
                }
            ]
        
        service_code='AmazonEC2'
        
        logger.debug("Mapping region to region: {} to code: {}".format(self.region, region_code_map[self.region]))
        logger.debug("Setting up filters: {}".format(filters))
        logger.debug("Getting price for service code: {} and filters: {}".format(service_code, filters))




        try:
            # Get the pricing information for the Amazon Elastic Block Store (EBS) snapshots
            logger.info("Getting pricing information for AmazonElasticBlockStore...")
            response = get_price(self.profile, service_code, filters)
            logger.debug("Snapshot pricing response: {}".format(response))
            json_dump = response
            cache_file_path = os.path.join(os.path.dirname(__file__), "products.json")
            with open(cache_file_path, "w") as outfile:
                json.dump(json_dump, outfile)
        except:
            logger.error("Pricing information for AmazonElasticBlockStore is not available. Using cached data...")

            cache_file_path = os.path.join(os.path.dirname(__file__), "products.json")

            logger.info("Opening cached pricing data from {}".format(cache_file_path))
            with open(cache_file_path, "r") as infile:
                    response = json.load(infile)
            logger.debug("Cached pricing data: {}".format(response))


        # Check if pricing data is available
        if not response['PriceList']:
            logger.warning(f"Pricing information for snapshots in {self.region} is not available.")
            return None

        # Parse the pricing details from the JSON string in the PriceList
        pricing_data = json.loads(response['PriceList'][0])
        logger.info("Converting pricing data to JSON...")
        logger.debug("Pricing data: {}".format(pricing_data))
        if not pricing_data['terms']['OnDemand']:
            logger.warning(f"Pricing information for AmazonElasticBlockStore in {self.region} is not available.")
            return None

        pricing_details = pricing_data['terms']['OnDemand']
        logger.debug("Pricing details: {}".format(pricing_details))

        # Find the correct price per unit for AmazonElasticBlockStore
        pricing_code = None
        price_dimensions_code = None

        logger.info("Finding the correct price per unit for AmazonElasticBlockStore...")
        for code in pricing_details.keys():
            pricing_code = code
            logger.debug("Pricing code: {}".format(pricing_code))

        for code in pricing_details[pricing_code]['priceDimensions'].keys():
            price_dimensions_code = code
            logger.debug("Price dimensions code: {}".format(price_dimensions_code))
        
        
        snapshot_price_per_gb_month_str = pricing_details[pricing_code]['priceDimensions'][price_dimensions_code]['pricePerUnit']['USD']
        snapshot_price_per_gb_month = float(snapshot_price_per_gb_month_str)

        logger.info("Snapshot price per GB per month: {}".format(snapshot_price_per_gb_month))
        self.snapshot_pricing = snapshot_price_per_gb_month

    
    
    def get_snapshots(self, region):
        '''
        Function to get the EBS snapshots for the given region

        Args:
            region (str): AWS region

        Returns:
            list: List of EBS snapshots
        '''

        if self.snapshots is None:
            self.snapshots = get_ebs_snapshots(self.profile, region)

        return self.snapshots

