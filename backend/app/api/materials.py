from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.material import MaterialCreate, MaterialResponse
from backend.app.database import get_db
from backend.app.services import material_service

router = APIRouter(tags=["materials"])


@router.post("", response_model=MaterialResponse, status_code=201)
async def create_material(body: MaterialCreate, db: AsyncSession = Depends(get_db)):
    return await material_service.create_material(db, body)


@router.get("", response_model=list[MaterialResponse])
async def list_materials(db: AsyncSession = Depends(get_db)):
    return await material_service.list_materials(db)

@router.post("/upload", response_model=MaterialResponse, status_code=201)
async def upload_material(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await material_service.create_pdf_material(db, name, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: str, db: AsyncSession = Depends(get_db)):
    result = await material_service.get_material(db, material_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return result
