from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    UserId: int
    Username: str
    Role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UploadSummary(BaseModel):
    accepted: int
    rejected: int
    errors: list[str] = []


class PredictionRequest(BaseModel):
    transaction_id: int


class PredictionResponse(BaseModel):
    transaction_id: int
    fraud_score: float
    top_features: str


class ForgotPasswordRequest(BaseModel):
    username: str


class ForgotPasswordResponse(BaseModel):
    message: str
    temporary_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str