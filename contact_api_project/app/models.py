# app/models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ContactFormData(BaseModel):
    customer_name: str = Field(..., min_length=1, description="Nombre del cliente que envía el formulario.")
    corporate_mail: EmailStr = Field(..., description="Correo electrónico del cliente.")
    requests: Optional[str] = Field(None, description="El mensaje o solicitud del cliente.")
    accept_policy: bool = Field(..., description="Indica si el cliente aceptó la política de tratamiento de datos.")
    class Config:
        json_schema_extra = {
            "example": {
                "customer_name": "Tu nombre o el de la compañia",
                "corporate_mail": "example@example.com",
                "requests": "Descripcion de lo que deseas solicitar",
                "accept_policy": True  
            }
        }