import boto3
import requests
import webbrowser
import time
import json
import random
import string
from botocore.exceptions import ClientError

ec2 = boto3.resource('ec2')
s3 = boto3.resource('s3')

random_char = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))

###Code for instances###

#Makes a new instance
try:
	new_instances = ec2.create_instances(
	 UserData="""#!/bin/bash
	 yum install httpd -y
	 systemctl enable httpd
	 systemctl start httpd
	 
	 instance_id=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
	 instance_type=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
	 availability_zone=$(curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone)
	 
	 echo "<html>
	  <head>
	    <title>Instance Information</title>
	  </head>
	  <body>
	    <h1>Instance Information</h1>
	    <p>Instance ID: <b>$instance_id</b></p>
	    <p>Instance Type: <b>$instance_type</b></p>
	    <p>Availability Zone: <b>$availability_zone</b></p>
	  </body>
	</html>" > /var/www/html/index.html""",
	 ImageId='ami-0bb4c991fa89d4b9b',
	 MinCount=1,
	 MaxCount=1,
	 KeyName='mykey',
	 SecurityGroupIds = ['sg-063b9a7bb15d1bde7'],
	 TagSpecifications = [
	 	{
		  'ResourceType':'instance',
		  'Tags' : [
		  	{'Key' : 'Name', 'Value' : 'Web server'}
		  ]
		}
	 ],
	 InstanceType='t2.nano')
	print('Instance has been created')
	 
except ClientError as e:
	 print(f"Error creating EC2 instance: {e}")


###Code for buckets###

bucket_name = random_char+'-astrymer'

#Makes a new bucket
try:
	new_bucket = s3.create_bucket (
	 Bucket = bucket_name
	)
	print('Bucket has been created')

except ClientError as e:
 if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
  print(f"Bucket {bucket_name} already exists and is owned by you.")
 else:
  print(f"Error creating bucket: {e}")

#Downloads the image from the URL
download = requests.get('http://devops.witdemo.net/logo.jpg')

#HTML for the S3 website
index_html_content = f"""<html>
<head>
    <title>My Website</title>
</head>
<body>
    <h1>Welcome to My Website!</h1>
    <img src="http://{bucket_name}.s3-website-us-east-1.amazonaws.com/logo.jpg" alt="Uploaded Image">
</body>
</html>
"""

#Places the image and HTML file inside the bucket
s3 = boto3.client('s3')
s3.put_object(Body=download.content, Bucket=bucket_name, Key='logo.jpg', ContentType='image/jpg')
s3.put_object(Body=index_html_content, Bucket=bucket_name, Key='index.html', ContentType='text/html')

#Makes the bucket public
s3.delete_public_access_block(Bucket=bucket_name)

bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:GetObject"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
                ]
}

s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))

#Configures the bucket for static website hosting
s3 = boto3.resource('s3')
website_configuration = {
 'ErrorDocument': {'Key': 'error.html'},
 'IndexDocument': {'Suffix': 'index.html'},
}

bucket_website = s3.BucketWebsite(bucket_name) 

response = bucket_website.put(WebsiteConfiguration=website_configuration)


###Code for dealing with instance and bucket URLs###

#Name of the file that the URLs will be written to
file_name = 'astrymer-websites.txt'

#Waits until the instance is running and then reloads the instance
new_instances[0].wait_until_running()
new_instances[0].reload()

#Gets the public IP address of the instance
ec2_ip = new_instances[0].public_ip_address

#URLs for EC2 and S3 web pages
ec2_url = f'http://{ec2_ip}'
s3_url = f'http://{bucket_name}.s3-website-us-east-1.amazonaws.com'

print('Instance running, URLs will open in 60 seconds')
time.sleep(60)

#Opens the two URLs in seperate browser tabs
webbrowser.open(ec2_url)
webbrowser.open(s3_url)
 
# Writes both URLs to a file
with open(file_name, 'w') as file:
    file.write(f'EC2 URL: {ec2_url}')
    file.write(f'S3 URL: {s3_url}')
    
print(f'EC2 and S3 URLs have been written to file {file_name}')
    
#Defines the DynamoDB resource
dynamodb = boto3.resource('dynamodb')

#Defines the table name and key schema
table_name = random_char+'-Table'
key_schema = [{'AttributeName': 'id', 'KeyType': 'HASH'}]

#Creates a DynamoDB table
try:
	table = dynamodb.create_table(
	    TableName=table_name,
	    KeySchema=key_schema,
	    AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'N'}],
	    ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
	)

	#Wait for the table to be created
	table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
	
	print('Table has been created')

except ClientError as e:
 if e.response['Error']['Code'] == 'ResourceInUseException':
  print(f"Table {table_name} already exists.")
 else:
  print(f"Error creating table: {e}")

#Prints information about the table
print(f"Table '{table_name}' created")

# Puts information about the EC2 instance into the table
instance_info = {
    'id': 1,
    'instance_id': new_instances[0].id,
    'instance_type': new_instances[0].instance_type,
    'availability_zone': new_instances[0].placement['AvailabilityZone'],
}

# Puts information about the S3 bucket into the table
bucket_info = {
    'id': 2,
    'bucket_name': bucket_name,
    'bucket_url': f'http://{bucket_name}.s3-website-us-east-1.amazonaws.com'
}

try:
	table.put_item(Item=instance_info)
	table.put_item(Item=bucket_info)
	print(f"Items added to the table.")
	
except ClientError as e:
	print(f"Error putting items into the table: {e}")

#Gets an item from the table
response = table.scan()
items = response.get('Items')

#Prints the retrieved items
print("Retrieved Items:")
for item in items:
    print(item)
