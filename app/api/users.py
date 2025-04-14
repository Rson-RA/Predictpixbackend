from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.deps import get_db, get_current_user
from app.models.models import User
from app.schemas.user import UserResponse, UserUpdate
from app.core.security import get_password_hash
import base64
from PIL import Image
import io
import os
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of users with pagination and search.
    Only admin users can access this endpoint.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    query = db.query(User)
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID.
    Admin users can access any user, regular users can only access their own profile.
    """
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user details.
    Admin users can update any user, regular users can only update their own profile.
    """
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only admin can change roles and active status
    if current_user.role != "admin":
        user_update.role = None
        user_update.is_active = None
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/{user_id}/avatar", response_model=UserResponse)
async def update_avatar(
    user_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user avatar using file upload.
    Accepts image files (JPEG, PNG, etc.)
    """
    # Validate user permissions
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )
        
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Resize image to standard size (e.g., 256x256)
        image.thumbnail((256, 256))
        
        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        
        # Create avatars directory if it doesn't exist
        avatar_dir = "static/avatars"
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Delete old avatar if exists
        if user.avatar_url:
            try:
                old_avatar_path = os.path.join("static", user.avatar_url.lstrip("/"))
                if os.path.exists(old_avatar_path):
                    os.remove(old_avatar_path)
            except Exception:
                # Log error but continue with new avatar upload
                pass
        
        # Save image
        avatar_filename = f"user_{user_id}_{int(datetime.utcnow().timestamp())}.jpg"
        avatar_path = os.path.join(avatar_dir, avatar_filename)
        
        # Save as JPEG
        image_rgb = image.convert('RGB')
        image_rgb.save(avatar_path, "JPEG", quality=85)
        
        # Update user avatar URL
        user.avatar_url = f"/static/avatars/{avatar_filename}"
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing image: {str(e)}"
        )
    finally:
        await file.close()

@router.delete("/{user_id}/avatar", response_model=UserResponse)
async def delete_avatar(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove user's avatar.
    """
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.avatar_url:
        try:
            # Remove the old avatar file
            avatar_path = os.path.join("static", user.avatar_url.lstrip("/"))
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
        except Exception:
            pass  # Ignore file deletion errors
        
        user.avatar_url = None
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    
    return user 