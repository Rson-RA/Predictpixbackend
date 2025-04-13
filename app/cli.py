import typer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.models import User, UserRole
from app.core.security import get_password_hash
import click

cli = typer.Typer()

@cli.command()
def create_admin(
    username: str = typer.Option(..., prompt=True),
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
    pi_user_id: str = typer.Option(..., prompt=True)
):
    """
    Create a new admin user.
    """
    db = SessionLocal()
    try:
        # Check if user already exists
        user = db.query(User).filter(User.username == username).first()
        if user:
            typer.echo(f"User {username} already exists!")
            raise typer.Exit(1)
        
        # Create new admin user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            pi_user_id=pi_user_id,
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        typer.echo(f"Admin user {username} created successfully!")
    
    finally:
        db.close()

if __name__ == "__main__":
    cli()
else:
    # This ensures the CLI is properly registered when run as a module
    app = cli 