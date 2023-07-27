import json
import boto3
from scanner.util.aws_functions import get_price

class EBSScanner:



    def __init__(self, profile, region):
        self.profile = profile
        self.region = region



    def get_ebs_snapshot_price(self):
        '''
        Fetch the pricing information for EBS snapshots

        Args:
            None

        Returns:
            float: Price per GB of EBS snapshots
        '''
        
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': "Storage Snapshot"},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.region},
            {'Type': 'TERM_MATCH', 'Field': 'storageMedia', 'Value': 'Amazon S3'}
        ]

        price = get_price(ServiceCode='AmazonEC2', Filters=filters)

        if len(price['PriceList']) > 0:
            price = json.loads(price['PriceList'][0])

            for on_demand in price['terms']['OnDemand'].values():
                for price_dimensions in on_demand['priceDimensions'].values():
                    price_value = price_dimensions['pricePerUnit']['USD']
                    
            return float(price_value)
        return None

