import scanner.util.logger as log
import os
import pandas as pd
import time
import subprocess

logger = log.get_logger()

def save_report_to_csv(input, output_file):
    """
    Function to save the report as a CSV file

    Args:
        ebs_volumes_dataframe (DataFrame): DataFrame of EBSVolumes objects
        output_file (str): Output file name

    Returns:
        None
    """
    logger.info("Saving report...")
    if input is None:
        logger.warning("No data to save.")
    else:
        report_folder = "reports"
        if not os.path.exists(report_folder):
            os.makedirs(report_folder)

        csv_filepath = os.path.join(report_folder, output_file)

        df = pd.DataFrame(input)
        df.to_csv(csv_filepath, index=False)
        logger.info(f"CSV report saved as {csv_filepath}")

        # Sleep for a few seconds before opening the CSV file
        time.sleep(5)

        # Open the CSV file with conditional formatting
        open_files(csv_filepath)

def open_files(csv_file_path):
    """
    Function to open files

    Args:
        csv_file_path (str): CSV file path

    Returns:
        None
    """
    logger.info("Opening Report...")
    try:
        subprocess.run(["open", csv_file_path])
    except Exception as e:
        logger.error(f"Error occurred while opening files: {str(e)}")