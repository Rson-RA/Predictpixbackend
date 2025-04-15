from typing import Optional
import requests
from fastapi import HTTPException
from app.core.config import settings

class PiNetworkAuth:
    def __init__(self):
        self.api_key = settings.PI_API_KEY
        self.base_url = settings.PI_NETWORK_URL
        self.sandbox_mode = settings.PI_SANDBOX_MODE

    async def verify_auth_token(self, auth_token: str) -> dict:
        """Verify Pi Network authentication token and get user info."""
        try:
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/v2/me",
                headers=headers,
                json={"auth_token": auth_token}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Pi Network authentication"
                )
            
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Pi Network authentication error: {str(e)}"
            )

    async def verify_payment(self, payment_id: str) -> dict:
        """Verify a Pi payment transaction."""
        try:
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/v2/payments/{payment_id}/complete",
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid payment verification"
                )
            
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Payment verification error: {str(e)}"
            )

    async def create_payment(self, amount: float, memo: str, user_uid: str) -> dict:
        """Create a new payment request."""
        try:
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "amount": amount,
                "memo": memo,
                "metadata": {"user_uid": user_uid},
                "uid": user_uid
            }
            
            response = requests.post(
                f"{self.base_url}/v2/payments",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 201:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to create payment"
                )
            
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Payment creation error: {str(e)}"
            )

    async def approve_payment(self, payment_id: str) -> dict:
        """Approve a Pi payment transaction."""
        try:
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/v2/payments/{payment_id}/approve",
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to approve payment"
                )
            
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Payment approval error: {str(e)}"
            )

    async def cancel_payment(self, payment_id: str, reason: Optional[str] = None) -> dict:
        """Cancel a Pi payment transaction."""
        try:
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {"reason": reason} if reason else {}
            
            response = requests.post(
                f"{self.base_url}/v2/payments/{payment_id}/cancel",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to cancel payment"
                )
            
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Payment cancellation error: {str(e)}"
            )

pi_auth = PiNetworkAuth() 