# AWSAutomation

## Overview
This Python script automates various tasks on Amazon Web Services (AWS). It uses the boto3 library to interact with AWS services like EC2 (Elastic Compute Cloud) and S3 (Simple Storage Service). Key functionalities include creating and managing EC2 instances, handling S3 resources, and dealing with DynamoDB tables..

## Requirements
+ Python 3.x
+ boto3 library
+ AWS account and configured AWS CLI with appropriate permissions

## Setup
+ Ensure Python 3.x is installed on your system.
+ Install the boto3 library using pip:
  pip install boto3
+ Configure your AWS CLI with the required credentials and permissions:
  aws configure

## Usage
+ Before running the script, ensure your AWS credentials are set up correctly.
+ Run the script using Python:
  python AWSAutomation.py

## Features
+ EC2 Management: The script can create new EC2 instances with specified configurations, including installing and starting a web server.
+ S3 Interaction: Handles operations related to S3, such as uploading, downloading, and managing S3 resources as well as static website hosting.
+ DynamoDB Tables: Places information about the S3 buckets and EC2 instances into a table.
