import hashlib
import hmac
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    salt = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))


def hash_password(password: str, salt: str) -> str:
    raw = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return raw.hex()


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email or len(email) < 5:
        raise HTTPException(400, "Enter a valid email.")
    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    if not body.name.strip():
        raise HTTPException(400, "Enter your name.")
    if db.query(Account).filter_by(email=email).first():
        raise HTTPException(400, "That email is already registered. Try logging in.")

    user = User(name=body.name.strip())
    db.add(user)
    db.commit()
    db.refresh(user)

    salt = os.urandom(16).hex()
    db.add(Account(
        email=email,
        salt=salt,
        password_hash=hash_password(body.password, salt),
        user_id=user.id,
    ))
    db.commit()
    return {"user_id": user.id, "name": user.name}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    acc = db.query(Account).filter_by(email=email).first()
    if acc is None:
        raise HTTPException(400, "Wrong email or password.")
    attempt = hash_password(body.password, acc.salt)
    if not hmac.compare_digest(attempt, acc.password_hash):
        raise HTTPException(400, "Wrong email or password.")
    user = db.get(User, acc.user_id)
    return {"user_id": user.id, "name": user.name}