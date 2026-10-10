from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from financial_ai.api.schemas import CompanyCreate, CompanyResponse
from financial_ai.db.models import Company
from financial_ai.db.session import get_db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
) -> Company:
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=list[CompanyResponse])
def list_companies(
    db: Session = Depends(get_db),
) -> list[Company]:
    return list(db.scalars(select(Company).order_by(Company.ticker)).all())
