from sqlalchemy.orm import Session
from app.models.models import User, UserRole
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.base import Base
from app.db.session import engine
import logging

logger = logging.getLogger(__name__)

def drop_all_tables():
    """Drop all tables in the database"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}")
        raise

def create_admin_user(db: Session) -> User:
    """
    Create an admin user if it doesn't exist.
    Uses environment variables for admin credentials.
    """
    try:
        # Check if admin user exists
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin:
            logger.info("Admin user already exists")
            return admin

        # Create new admin user
        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            pi_user_id="admin",  # Special case for admin
            role=UserRole.ADMIN,
            is_active=True,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD)
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        logger.info("Created new admin user")
        return admin
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        db.rollback()
        raise

def init_db(db: Session) -> None:
    """
    Initialize database with required initial data.
    Currently only creates admin user.
    """
    try:
        # Drop all existing tables
        drop_all_tables()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create admin user
        create_admin_user(db)
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise 