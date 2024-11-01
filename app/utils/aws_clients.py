import aioboto3

region = 'eu-north-1'

session = aioboto3.Session()

# Initialize clients as asynchronous with aioboto3
async def get_sagemaker_runtime():
    async with session.client('runtime.sagemaker', region_name=region) as client:
        yield client

async def get_s3_client():
    async with session.client('s3', region_name=region) as client:
        yield client