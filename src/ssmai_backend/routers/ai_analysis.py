from typing import Annotated

from fastapi import APIRouter, Depends
from ssmai_backend.database import get_s3_client, get_session
from sqlalchemy.ext.asyncio import AsyncSession



from ssmai_backend.models.user import User
from ssmai_backend.routers.users import fastapi_users

from ssmai_backend.schemas.root_schemas import Message
from ssmai_backend.services.ai_analysis_service import update_ai_predictions_to_enterpryse_service


router = APIRouter(prefix="/ai_analysis", tags=["ai_analysis"])


T_CurrentUser = Annotated[User, Depends(fastapi_users.current_user())]
T_Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/", response_model=Message)
async def update_ai_predictions_to_enterpryse(
    current_user: T_CurrentUser,
    session: T_Session,
    s3_client=Depends(get_s3_client)
    
):
    return await update_ai_predictions_to_enterpryse_service(current_user, s3_client, session)
