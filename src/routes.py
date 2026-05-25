from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT

from fastapi_jwt_auth.exceptions import MissingTokenError
import jwt

# Router for organizing routes
base_routes = APIRouter()

# Central function to handle token validation
def validate_token(authjwt: AuthJWT = Depends()):
    try:
        authjwt.jwt_required()
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Token expired. Please log in again."
        )
    except MissingTokenError:
        raise HTTPException(
            status_code=401,
            detail="No token found. Please create an account and log in.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating token: {str(e)}")


# ROOT ROUTE
@base_routes.get("/")
def home():
    return {
        "message": "Welcome to Swap Pro Backend!",
        "description": "Barter exchange API with credit wallet, prepaid fees, and hub scheduling.",
        "default endpoints": [
            "Authentication",
            "Listings & Search",
            "Swap Requests & Payments",
            "Credit Wallet",
            "Swap Hubs",
            "Admin Dashboard",
            "Notifications",
            "File Storage",
        ],
        "docs": "/docs",
    }