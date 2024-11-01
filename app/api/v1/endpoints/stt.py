import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import email_verified_user_permission
from app.db.session import get_db
from app.db.schemas import UserDB
from app.utils.aws_clients import get_s3_client, get_sagemaker_runtime
from app.utils.stt_helpers import ALLOWED_CONTENT_TYPES, invoke_stt_endpoint, generate_unique_key, hash_unique_key, save_transcription_to_s3

router = APIRouter()

@router.post("/generate-api-key")
async def generate_api_key(
    current_user: UserDB = Depends(email_verified_user_permission),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Generate a new API key
    api_key = await generate_unique_key(email=current_user.email)

    # Hash the API key before storing it
    hashed_api_key = await hash_unique_key(api_key)

    # Store the hashed API key in the database for the user
    await db["users"].update_one(
        {"email": current_user.email},
        {"$set": {"api_key": hashed_api_key}}
    )

    return {"api_key": api_key}

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    api_key: str = Header(None, alias="x-api-key"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    sagemaker_runtime=Depends(get_sagemaker_runtime),
    s3_client=Depends(get_s3_client)
):
    # Check file content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only mp3, wav, and webm are allowed.")
    
    # Verify API key and get user
    hashed_api_key = await hash_unique_key(api_key)
    user_in_db = await db["users"].find_one({"api_key": hashed_api_key})
    
    if not user_in_db:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if user_in_db["balance"] <= 0:
        raise HTTPException(status_code=400, detail="Insufficient balance. Please refill.")
    
    # Pass the file to the SageMaker endpoint and handle any exceptions
    try:
        transcription_result = await invoke_stt_endpoint(file, sagemaker_runtime)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription service failed: {str(e)}")
    
    # Update user's transcription duration and balance in the database
    transcription_duration_seconds = transcription_result.get("duration", 1)
    await db["users"].update_one(
        {"email": user_in_db["email"]},
        {
            "$inc": {
                "total_transcription_duration_seconds": transcription_duration_seconds,
                "balance": -transcription_duration_seconds * 0.001
            }
        }
    )

    transcription_result_text = transcription_result.get("prediction", "").strip()

    # Save transcription and audio to S3
    # await save_transcription_to_s3(file, transcription_result_text, user_in_db["email"], s3_client)

    return {"transcription": transcription_result_text}