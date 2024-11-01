import hashlib
import json
import time
import uuid
from fastapi import HTTPException, UploadFile
from app.core.config import settings
import secrets
import string

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/webm": "webm"
}

async def generate_unique_key(email: str, length: int = 32):
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

async def hash_unique_key(api_key: str) -> str:
    """Hash the API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def get_file_extension(content_type: str) -> str:
    if content_type in ALLOWED_CONTENT_TYPES:
        return ALLOWED_CONTENT_TYPES[content_type]
    raise HTTPException(status_code=400, detail="Unsupported file format")

import io

async def invoke_stt_endpoint(file: UploadFile, sagemaker_runtime):
    endpoint_name = settings.SAGEMAKER_ENDPOINT_NAME

    # Create a boundary for multipart encoding
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    multipart_header = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{file.filename}"\r\n'
        f'Content-Type: {file.content_type or "application/octet-stream"}\r\n\r\n'
    ).encode()

    boundary_footer = f'\r\n--{boundary}--\r\n'.encode()

    # Use a BytesIO object to concatenate and stream the body
    body_stream = io.BytesIO()
    body_stream.write(multipart_header)
    file.file.seek(0)  # Ensure the file pointer is at the start
    body_stream.write(file.file.read())  # Write the file content directly to the stream
    body_stream.write(boundary_footer)
    
    # Reset the stream pointer to the beginning
    body_stream.seek(0)

    # Set the correct Content-Type header
    content_type = f'multipart/form-data; boundary={boundary}'

    # Pass the BytesIO stream directly to the SageMaker endpoint
    response = await sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType=content_type,
        Body=body_stream.getvalue()  # Use the content of the stream as bytes
    )

    result = json.loads(await response['Body'].read())
    return result

# Async function to save transcription to S3 using dependency
async def save_transcription_to_s3(file: UploadFile, transcription_text: str, user_email: str, s3_client):
    file_extension = await get_file_extension(file.content_type)
    random_name = str(uuid.uuid4())
    bucket_name = settings.STT_S3_PAIRS_BUCKET_NAME

    # File paths with appropriate extension
    audio_file_key = f"{user_email}/{random_name}.{file_extension}"
    text_file_key = f"{user_email}/{random_name}.txt"

    # Upload audio file directly from UploadFile stream to S3
    await s3_client.put_object(
        Bucket=bucket_name,
        Key=audio_file_key,
        Body=file.file,
        ContentType=file.content_type
    )

    # Upload the transcription text file to S3
    await s3_client.put_object(
        Bucket=bucket_name,
        Key=text_file_key,
        Body=transcription_text,
        ContentType='text/plain'
    )
