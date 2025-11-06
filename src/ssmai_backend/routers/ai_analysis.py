from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.database import get_session
from ssmai_backend.models.user import User
from ssmai_backend.routers.users import fastapi_users
from ssmai_backend.schemas.ai_analysis_schemas import (
    AnalysisSchema,
    IdealStockSchema,
    PrevisoesResponse,
)
from ssmai_backend.schemas.root_schemas import Message
from ssmai_backend.services.ai_analysis_service import (
    get_analysis_by_product_id_service,
    get_graph_data_by_product_id_service,
    get_worst_stock_deviation_service,
    update_ai_predictions_to_enterpryse_service,
    update_by_product_id_service,
)

router = APIRouter(prefix="/ai_analysis", tags=["ai_analysis"])


T_CurrentUser = Annotated[User, Depends(fastapi_users.current_user())]
T_Session = Annotated[AsyncSession, Depends(get_session)]


@router.put("/all", response_model=Message)
async def update_batch(
    current_user: T_CurrentUser,
    session: T_Session,

):
    return await update_ai_predictions_to_enterpryse_service(current_user, session)


@router.put("/{product_id}", response_model=Message)
async def update_by_product_id(
    current_user: T_CurrentUser,
    session: T_Session,
    product_id: int,
):
    return await update_by_product_id_service(current_user, session, product_id)


@router.get("/{product_id}", response_model=AnalysisSchema)
async def get_analysis_by_product_id(
    current_user: T_CurrentUser,
    session: T_Session,
    product_id: int,
    service_level: float = 0.95,
    lead_time: int = 7
):
    return await get_analysis_by_product_id_service(product_id, session, service_level, lead_time)


@router.get("/{product_id}/graph", response_model=PrevisoesResponse)
async def get_grath_data_by_product_id(
    current_user: T_CurrentUser,
    session: T_Session,
    product_id: int
):
    return await get_graph_data_by_product_id_service(product_id, session)


@router.get("/worst_stocks/", response_model=list[IdealStockSchema])
async def get_wors_stocks(
    current_user: T_CurrentUser,
    session: T_Session,
):
    return await get_worst_stock_deviation_service(session, current_user)
