import hashlib
import json
import time
import uuid

from fastapi import HTTPException, UploadFile
from app.utils.aws_clients import sagemaker_runtime , s3_client
from app.core.config import settings
import secrets
import string

# Function to call SageMaker endpoint
def invoke_stt_endpoint(wav_bs64):
    endpoint_name = settings.SAGEMAKER_ENDPOINT_NAME
    
    # Define the payload
    payload = {
        "audio": wav_bs64
    }
    
    # Convert the payload to JSON format
    payload_json = json.dumps(payload)
    
    # Invoke the SageMaker endpoint
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=payload_json
    )
    
    # Parse the response
    result = json.loads(response['Body'].read().decode())
    return result

def generate_unique_key(email: str, length: int = 32):
    # Hash the email to make it secure and unique
    email_hash = hashlib.sha256(email.encode()).hexdigest()[:10]
    
    timestamp_part = str(int(time.time()))[:10]
    
    # Define the character set: uppercase letters, digits, and limited symbols
    characters = string.ascii_uppercase + string.digits + "-_"
    
    # Generate the random part of the API key
    random_part = ''.join(secrets.choice(characters) for _ in range(length))
    
    # Combine the prefix, timestamp, email hash, and random part for the API key
    prefix = "FBASR"
    api_key = f"{prefix}-{timestamp_part}-{email_hash}-{random_part}"
    
    return api_key

def hash_unique_key(api_key: str) -> str:
    """Hash the API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/webm": "webm"
}

def get_file_extension(content_type: str) -> str:
    if content_type in ALLOWED_CONTENT_TYPES:
        return ALLOWED_CONTENT_TYPES[content_type]
    raise HTTPException(status_code=400, detail="Unsupported file format")

def save_transcription_to_s3(file_bytes: bytes, content_type: str, transcription_text: str, user_email: str):
    file_extension = get_file_extension(content_type)

    # Generate a random UUID for the file name
    random_name = str(uuid.uuid4())
    
    # Define the bucket name
    bucket_name = settings.STT_S3_PAIRS_BUCKET_NAME

    # Define the file paths with the correct extension based on content type
    audio_file_key = f"{user_email}/{random_name}.{file_extension}"
    text_file_key = f"{user_email}/{random_name}.txt"

    # Upload the audio file to S3 with the original content type
    s3_client.put_object(
        Bucket=bucket_name,
        Key=audio_file_key,
        Body=file_bytes,
        ContentType=content_type
    )

    # Upload the transcription text file to S3
    s3_client.put_object(
        Bucket=bucket_name,
        Key=text_file_key,
        Body=transcription_text,
        ContentType='text/plain'
    )
    