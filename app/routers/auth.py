from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, AuditLog, AuditAction
from app.schemas.schemas import Token, UserCreate, UserOut, LoginResponse
from app.utils.auth import verify_password, hash_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        phone=user_in.phone,
        role=user_in.role,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    db.add(AuditLog(
        user_id=user.id, action=AuditAction.create,
        entity_type="user", entity_id=user.id,
        details=f"User registered: {user.email}"
    ))
    db.commit()

    return user


@router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    token = create_access_token({"sub": user.email, "role": user.role})

    # Audit log
    db.add(AuditLog(
        user_id=user.id, action=AuditAction.login,
        entity_type="user", entity_id=user.id,
        details=f"User logged in: {user.email}"
    ))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }
