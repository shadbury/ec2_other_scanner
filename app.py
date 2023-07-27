import sys
from scanner.util.logger import configure_logger
from scanner.util.aws_functions import get_aws_session, get_all_regions
from scanner.util.ebs_volumes import get_all_volumes, get_unused_volume_savings, create_ebs_dataframe, get_gp2_to_gp3_savings
from scanner.util.os_functions import save_report_to_csv, open_files
from scanner.util.ebs_snapshots import get_aws_snapshot_cost
import time



# Configure the logger to send logs to the logger.py file
logger = configure_logger("app.log")


def main():
    """
    Main function
    """

    # Check if the AWS profile is provided
    if len(sys.argv) < 2:
        logger.error(
            "Error occurred: Please provide the AWS profile as the first command-line argument. Example: python3 app.py my_aws_profile"
        )
        return
    
    region = None
    profile = sys.argv[1]
    session = None
    if len(sys.argv) == 3:
        region = sys.argv[2]
    try:
        session = get_aws_session(profile)
        logger.info("Credentials loaded successfully")

    except Exception as e:
        if e == "ProfileNotFound":
            logger.error(f"Error Occurred: {str(e)}", exc_info=True)
        else:
            logger.error(
                f"Error occurred: AWS profile '{profile}' not found. Please check your credentials file (~/.aws/credentials)."
            )
        return

    try:
        # Get all available regions for the given profile
        if not region:
            regions = get_all_regions(profile)
        else:
            regions = [region]

        # Create the array of EbsVolumes objects and get potential savings
        region_potential_savings = get_unused_volume_savings(profile, regions)

        # Get the estimated gp2 to gp3 savings
        gp2_to_gp3_savings = {}
        snapshot_savings = {}
        for region in regions:
            ebs_volumes = get_all_volumes(profile, region)
            gp2_to_gp3_savings[region] = get_gp2_to_gp3_savings(ebs_volumes, region)
            snapshot_savings[region] = get_aws_snapshot_cost(profile, region)

        dataframe = {
            "unused" : region_potential_savings, 
            "gp2" : gp2_to_gp3_savings, 
            "snapshots" : snapshot_savings}


        # Create DataFrame from the results and save the report
        ebs_volumes_dataframe = create_ebs_dataframe(
            dataframe)
        time.sleep(5)

        # Save the CSV report
        if ebs_volumes_dataframe is not None:
            # Save the CSV report for resources
            save_report_to_csv(ebs_volumes_dataframe, "ebs_volumes_report.csv")

            # Open the CSV file with conditional formatting
            open_files("reports/ebs_volumes_report.csv")
        else:
            logger.warning("No data to save.")

    except Exception as e:
        # Include traceback information
        logger.error(f"Error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
