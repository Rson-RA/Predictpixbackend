from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.pi_auth import pi_auth
from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash, oauth2_scheme, SECRET_KEY, ALGORITHM, verify_refresh_token
from app.db.session import get_db
from app.models.models import User, UserRole
from app.schemas.auth import (
    AuthResponse,
    EmailLoginRequest,
    AdminLoginRequest,
    UpdateUserRequest,
    SignupRequest,
    PiLoginRequest,
    LoginRequest,
    RefreshTokenRequest
)
from app.core.security import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import logging
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: SignupRequest,
    referral_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if user exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check referral code if provided
    referrer = None
    if referral_code:
        referrer = db.query(User).filter(User.referral_code == referral_code).first()
        if not referrer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid referral code"
            )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        **user_data.dict(exclude={'password'}),
        hashed_password=hashed_password,
        referred_by_id=referrer.id if referrer else None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Process referral if applicable
    if referrer:
        await process_referral(db, db_user, referrer)

    # Create access token
    access_token = create_access_token(subject=db_user.email)
    refresh_token = create_refresh_token(subject=db_user.email)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at
    }

@router.post("/email/login", response_model=AuthResponse)
async def email_login(credentials: EmailLoginRequest | LoginRequest, db: Session = Depends(get_db)):
    """
    Login using email and password
    """
    logger.debug(f"Attempting login with email: {credentials.email}")
    
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        logger.warning(f"Login attempt failed: User not found for email {credentials.email}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    logger.debug(f"Found user: {user.username}")
    
    if not user.hashed_password:
        logger.warning(f"Login attempt failed: User {user.username} has no password set")
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Login attempt failed: Invalid password for user {user.username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt failed: User {user.username} is inactive")
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )
    
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    logger.info(f"User {user.username} logged in successfully")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "id": user.id,
        "username": user.username,
        "first_name": user.firstname,
        "last_name": user.lastname,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "balance": user.balance,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.post("/login", response_model=AuthResponse)
async def login(auth_token: str, db: Session = Depends(get_db)):
    """
    Login using Pi Network authentication token.
    """
    try:
        # Verify the auth token with Pi Network
        pi_user_info = await pi_auth.verify_auth_token(auth_token)
        
        # Check if user exists
        user = db.query(User).filter(User.pi_user_id == pi_user_info["uid"]).first()
        
        if not user:
            # Create new user if not exists
            user = User(
                pi_user_id=pi_user_info["uid"],
                username=pi_user_info.get("username", f"user_{pi_user_info['uid']}"),
                role=UserRole.USER,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token = create_access_token(subject=user.pi_user_id)
        refresh_token = create_refresh_token(subject=user.pi_user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
            "phone_number": user.phone_number,
            "avatar_url": user.avatar_url,
            "username": user.username,
            "first_name": user.firstname,
            "last_name": user.lastname,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/verify-payment")
async def verify_payment(payment_id: str):
    """
    Verify a Pi Network payment.
    """
    try:
        payment_info = await pi_auth.verify_payment(payment_id)
        return payment_info
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Payment verification failed: {str(e)}"
        )

@router.post("/admin/login", response_model=AuthResponse)
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Admin login using username and password.
    """
    user = db.query(User).filter(
        User.username == form_data.username,
        User.role == UserRole.ADMIN
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive admin user"
        )
    
    access_token = create_access_token(subject=user.pi_user_id)
    refresh_token = create_refresh_token(subject=user.pi_user_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role
    }

@router.put("/profile", response_model=AuthResponse)
async def update_profile(
    update_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    """
    # Check if email is being updated and is not already taken
    if update_data.email and update_data.email != current_user.email:
        if db.query(User).filter(User.email == update_data.email).first():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        current_user.email = update_data.email

    # Check if phone number is being updated and is not already taken
    if update_data.phone_number and update_data.phone_number != current_user.phone_number:
        if db.query(User).filter(User.phone_number == update_data.phone_number).first():
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered"
            )
        current_user.phone_number = update_data.phone_number

    # Update password if provided
    if update_data.password:
        current_user.hashed_password = get_password_hash(update_data.password)

    db.commit()
    db.refresh(current_user)

    return {
        "access_token": create_access_token(subject=str(current_user.id)),
        "token_type": "bearer",
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "role": current_user.role,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

@router.get("/validate")
async def validate_token(token: str = Depends(oauth2_scheme)):
    """
    Validate the authentication token
    """
    try:
        # Attempt to decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
            
        return {"status": "valid", "user_id": user_id}
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token_endpoint(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    """
    user_id = verify_refresh_token(request.refresh_token)
    user = db.query(User).filter((User.id == user_id) | (User.email == user_id) | (User.pi_user_id == user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "id": user.id,
        "username": user.username,
        "first_name": user.firstname,
        "last_name": user.lastname,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "balance": getattr(user, "balance", None),
        "avatar_url": getattr(user, "avatar_url", None),
        "created_at": user.created_at,
        "updated_at": user.updated_at
    } 