# AWS EBS Volumes Analysis Tool

The AWS EBS Volumes Analysis Tool is a Python application that allows you to analyze and identify potential cost savings from unused Amazon Elastic Block Store (EBS) volumes in your AWS account. The tool retrieves information about EBS volumes from multiple regions and generates a report indicating the potential savings for each unused volume or gp2 volume.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Output](#output)
- [License](#license)

## Requirements

- Python 3.x
- AWS CLI with appropriate credentials and configurations
- Required Python packages (specified in requirements.txt)

## Installation

1. Clone the repository to your local machine:

```bash
git clone https://github.com/shadbury/ebs_other_scanner.git
cd ebs_other_scanner

```

2. Create and activate a virtual environment (recommended):

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS and Linux
python3 -m venv venv
source venv/bin/activate

```


3. Install the required Python packages using pip:

```bash
pip install -r requirements.txt


```

## Usage

To run the AWS EBS Volumes Analysis Tool, execute the app.py script with your AWS profile as the first command-line argument:
```bash
python app.py your_aws_profile [optional_region]
```

<b>Note:</b> Ensure that you have the AWS CLI configured with valid credentials and that your profile is accessible.

## Configuration

The application uses the boto3 library to interact with AWS services. Before running the tool, make sure you have set up the AWS CLI and configured your credentials and default region using the following command:
```bash
aws configure
```

## Output

The application generates a CSV report named `ebs_volumes_report.csv` in the `reports folder`. The report provides information about unused EBS volumes in each region, including their unique IDs, volume types, and potential monthly savings.

## License

This project is licensed under the MIT License