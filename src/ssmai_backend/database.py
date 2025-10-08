import aioboto3

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from ssmai_backend.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL)
boto_session = aioboto3.Session()

async def get_session():  # pragma: no cover
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def get_s3_client():
    
    async with boto_session.client(
        's3',
        region_name=Settings().REGION,
        aws_access_key_id=Settings().AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Settings().AWS_SECRET_ACCESS_KEY,
    ) as s3_client:
        yield s3_client


async def get_textract_client():
    async with boto_session.client(
        'textract',
        region_name=Settings().REGION,
        aws_access_key_id=Settings().AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Settings().AWS_SECRET_ACCESS_KEY,
    ) as textract_client:
        yield textract_client
