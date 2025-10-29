import io

from ssmai_backend.models.user import User
from ssmai_backend.models.produto import MovimentacoesEstoque, Produto, Estoque
from ssmai_backend.settings import Settings

from sqlalchemy import func, select, case
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from sklearn.preprocessing import LabelEncoder


async def generate_dataset_moviments(session):
    subquery = (
        select(
            MovimentacoesEstoque.id_produtos.label("id_produto"),
            func.date(MovimentacoesEstoque.date).label("data"),
            func.sum(
                case((MovimentacoesEstoque.tipo == "saida", MovimentacoesEstoque.quantidade), else_=0)
            ).label("quantidade_saida"),
            func.sum(
                case((MovimentacoesEstoque.tipo == "entrada", MovimentacoesEstoque.quantidade), else_=0)
            ).label("quantidade_entrada"),
            func.avg(MovimentacoesEstoque.preco_und).label("preco_und_medio"),
            func.sum(MovimentacoesEstoque.total).label("valor_total")
        )
        .group_by(MovimentacoesEstoque.id_produtos, func.date(MovimentacoesEstoque.date))
        .subquery()
    )

    query = (
        select(
            subquery.c.id_produto,
            Produto.categoria,
            Estoque.custo_medio,
            subquery.c.data,
            subquery.c.quantidade_saida,
            subquery.c.quantidade_entrada,
            subquery.c.preco_und_medio,
            subquery.c.valor_total,
        )
        .join(Produto, Produto.id == subquery.c.id_produto)
        .join(Estoque, Estoque.id_produtos == Produto.id)
        .order_by(subquery.c.id_produto, subquery.c.data)
    )

    dataset = await session.execute(query)
    return dataset.all()


async def generate_moviments_df(session):
    dataset = await generate_dataset_moviments(session)
    df = pd.DataFrame(dataset, columns=[
        "id_produto",
        "categoria",
        "custo_medio",
        "data",
        "quantidade_saida",
        "quantidade_entrada",
        "preco_und_medio",
        "valor_total",
    ])

    df["data"] = pd.to_datetime(df["data"])
    df["dia_semana"] = df["data"].dt.dayofweek
    df["mes"] = df["data"].dt.month
    df["is_weekend"] = df["dia_semana"].isin([5, 6]).astype(int)
    df["semana_do_ano"] = df["data"].dt.isocalendar().week.astype(int)
    df["saldo_dia"] = df.groupby("id_produto")["quantidade_saida"].cumsum()
    le = LabelEncoder()
    df["categoria_encoded"] = le.fit_transform(df["categoria"])
    
    df.drop(columns=['categoria'])

    return df


async def update_ai_predictions_to_enterpryse_service(
    current_user: User,
    s3_client,
    session: AsyncSession
):
    SETTINGS = Settings()
    filename_with_ext = (
        f'uploads/{current_user.id_empresas}/files_to_ai/moviments_dataset.csv'
    )

    df = await generate_moviments_df(session)
    print(df)

    csv_buffer = io.BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    await s3_client.upload_fileobj(
            csv_buffer,
            SETTINGS.S3_BUCKET,
            filename_with_ext,
        )

    return {"message": 'Coleta realizada'}
