import boto3

region = 'eu-north-1'

sagemaker_runtime = boto3.client('runtime.sagemaker', region_name=region)
s3_client = boto3.client('s3', region_name=region)