import base64
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import email_verified_user_permission
from app.db.session import get_db
from app.db.schemas import UserDB
from app.utils.stt_helpers import ALLOWED_CONTENT_TYPES, invoke_stt_endpoint, generate_unique_key, hash_unique_key, save_transcription_to_s3

router = APIRouter()

@router.post("/generate-api-key")
async def generate_api_key(
    current_user: UserDB = Depends(email_verified_user_permission),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Generate a new API key
    api_key = generate_unique_key(email=current_user.email)

    # Hash the API key before storing it
    hashed_api_key = hash_unique_key(api_key)

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
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    # Check that the content type of the file is allowed
    content_type = file.content_type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only mp3, wav, and webm are allowed.")
    
    # Hash the provided API key
    hashed_api_key = hash_unique_key(api_key)

    # Retrieve the user by the hashed API key
    user_in_db = await db["users"].find_one({"api_key": hashed_api_key})
    
    if not user_in_db:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Read the file content
    file_bytes = await file.read()

    if user_in_db["balance"] <= 0:
        raise HTTPException(status_code=400, detail="Insufficient balance. Please refill.")
    
    # Convert audio file to base64 for API call
    wav_bs64 = base64.b64encode(file_bytes).decode("utf-8")
    
    # Call the transcription endpoint
    try:
        transcription_result = invoke_stt_endpoint(wav_bs64)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription service failed: {str(e)}")
    
    # Extract duration from the result (assuming the transcription result contains duration in seconds)
    transcription_duration_seconds = transcription_result.get("duration", 1)
    
    # Update the user's total transcription time and balance in the database
    await db["users"].update_one(
        {"email": user_in_db["email"]},
        {
            "$inc": {
                "total_transcription_duration_seconds": transcription_duration_seconds,
                "balance": -transcription_duration_seconds * 0.001
            }
        }
    )
    
    transcription_result = transcription_result.get("prediction", "").strip()
    save_transcription_to_s3(file_bytes, content_type, transcription_result, user_in_db["email"])

    return {"transcription": transcription_result}
