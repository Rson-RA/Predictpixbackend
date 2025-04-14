from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.pi_auth import pi_auth
from app.core.security import create_access_token, verify_password, get_password_hash, oauth2_scheme, SECRET_KEY, ALGORITHM
from app.db.session import get_db
from app.models.models import User, UserRole
from app.schemas.auth import (
    AuthResponse,
    EmailLoginRequest,
    AdminLoginRequest,
    UpdateUserRequest,
    SignupRequest,
    PiLoginRequest
)
from app.core.security import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import logging
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=AuthResponse)
async def register(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user with email and password
    """
    logger.debug(f"Attempting to register user with email: {request.email}")
    
    # Check if email already exists
    if db.query(User).filter(User.email == request.email).first():
        logger.warning(f"Registration failed: Email {request.email} already exists")
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Generate username if not provided
    username = request.username or f"user_{request.email.split('@')[0]}"
    
    # Check if username already exists
    if db.query(User).filter(User.username == username).first():
        logger.warning(f"Registration failed: Username {username} already exists")
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create new user
    user = User(
        email=request.email,
        username=username,
        hashed_password=get_password_hash(request.password),
        role=UserRole.USER,
        is_active=True
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"User {user.username} registered successfully")
        
        # Create access token
        access_token = create_access_token(subject=str(user.id))
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user account"
        )

@router.post("/email/login", response_model=AuthResponse)
async def email_login(credentials: EmailLoginRequest, db: Session = Depends(get_db)):
    """
    Login using email and password
    """
    logger.debug(f"Attempting login with email: {credentials.email}")
    
    user = db.query(User).filter(User.email == credentials.email).first()
    logger.debug(f"Found user: {user.username if user else None}")
    
    if not user:
        logger.warning(f"Login attempt failed: User not found for email {credentials.email}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
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
    logger.info(f"User {user.username} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
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
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
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
    
    return {
        "access_token": access_token,
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