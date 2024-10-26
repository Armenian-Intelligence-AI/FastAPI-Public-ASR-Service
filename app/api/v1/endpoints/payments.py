
from fastapi import APIRouter, Depends, Request, HTTPException
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.session import get_db
import stripe

router = APIRouter()

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']

        # Retrieve the user based on the payment intent metadata
        user_email = payment_intent['metadata']['email']

        # Get the amount received from Stripe (Stripe returns amount in cents, so convert to dollars)
        amount_received = payment_intent['amount_received'] / 100.0

        # Increment the user's balance by the received amount
        await db["users"].update_one(
            {"email": user_email},
            {"$inc": {"balance": amount_received}}  # Use $inc to increase the balance
        )

    elif event['type'] == 'payment_intent.payment_failed':
        # Handle failed payment here, if needed
        payment_intent = event['data']['object']
        print(f"Payment for {payment_intent['id']} failed")

    return {"status": "success"}
