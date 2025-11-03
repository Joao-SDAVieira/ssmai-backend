import io
from scipy.stats import norm
import numpy as np

from ssmai_backend.models.user import User
from ssmai_backend.models.produto import MovimentacoesEstoque, Produto, Estoque, Previsoes
from ssmai_backend.settings import Settings

from sqlalchemy import func, select, case, delete, insert, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from prophet import Prophet


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


async def prepare_dataframe_to_train(df_dataset: pd.DataFrame, product_id: int) -> pd.DataFrame:
    df_prod: pd.DataFrame = df_dataset[df_dataset['id_produto'] == product_id]
    df_prophet = df_prod[["data", "quantidade_saida"]].rename(columns={"data": "ds", "quantidade_saida": "y"})
    df_prophet["ds"] = pd.to_datetime(df_prophet["ds"])
    df_prophet = df_prophet.sort_values("ds")
    full_range = pd.date_range(df_prophet["ds"].min(), df_prophet["ds"].max(), freq="D")
    df_prophet = df_prophet.set_index("ds").reindex(full_range).fillna(0).rename_axis("ds").reset_index()
    return df_prophet


async def create_forecast(df_to_prophet: pd.DataFrame, ai_model: Prophet) -> pd.DataFrame:
    ai_model.fit(df_to_prophet)

    df_future = ai_model.make_future_dataframe(periods=15)

    df_forecast = ai_model.predict(df_future)

    df_forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(15)

    return df_forecast


async def add_forecast_on_db_by_product_id(product_id: int,
                                           df_forecast: pd.DataFrame,
                                           session: AsyncSession):
    statement = delete(Previsoes).where(Previsoes.id_produtos == product_id)

    await session.execute(statement)
    df_forecast = df_forecast[['ds', 'yhat']].rename(
        columns={'ds': 'data', 'yhat': 'estoque_previsto'}
        )
    df_forecast['id_produtos'] = product_id
    forecast_dict = df_forecast.to_dict(orient="records")
    await session.execute(insert(Previsoes), forecast_dict)


async def create_df_by_object_model_list(obj_list: list[ScalarResult]):
    data = [ 
    {key: value for key, value in obj.__dict__.items() if not key.startswith('_')} 
    for obj in obj_list
    ]
    return pd.DataFrame(data)


async def update_ai_predictions_to_enterpryse_service(
    current_user: User,
    s3_client,
    session: AsyncSession
):
    SETTINGS = Settings()
    filename_with_ext = (
        f'uploads/{current_user.id_empresas}/files_to_ai/moviments_dataset.csv'
    )
    """
    ds, yhat, 
    """
    df_dataset = await generate_moviments_df(session)
    product_ids = df_dataset['id_produto'].unique()
    for product_id in product_ids:
        ai_model = Prophet()
        df_to_prophet = await prepare_dataframe_to_train(df_dataset, product_id)
        df_forecast = await create_forecast(df_to_prophet, ai_model)
        print(df_forecast)
        await add_forecast_on_db_by_product_id(product_id, df_forecast, session)
    await session.commit()


    # csv_buffer = io.BytesIO()
    # df_dataset.to_csv(csv_buffer, index=False)
    # csv_buffer.seek(0)
    # await s3_client.upload_fileobj(
    #         csv_buffer,
    #         SETTINGS.S3_BUCKET,
    #         filename_with_ext,
    #     )

    return {"message": 'Coleta realizada'}


async def get_analysis_by_product_id_service(
    product_id: int,
    session: AsyncSession,
    service_level: float=0.95,
    lead_time=2
):
    forecasts_db = await session.scalars(select(Previsoes).where(Previsoes.id_produtos == product_id))

    df_forecast = await create_df_by_object_model_list(forecasts_db.all())

    stock_db = await session.scalar(select(Estoque).where(Estoque.id_produtos == product_id))

    future_stock = df_forecast.tail(15)['estoque_previsto']

    score = norm.ppf(service_level)

    diary_average = future_stock.mean()
    standart_deviation = future_stock.std()
    demanda_leadtime = diary_average * lead_time
    safety_stock = score * standart_deviation * np.sqrt(lead_time)

    ideal_stock = demanda_leadtime + safety_stock
    faltante = ideal_stock - stock_db.quantidade_disponivel
    print(faltante)
    return {
        "diary_average": diary_average,
        "demanda_leadtime": demanda_leadtime, #saida até reposição
        "safety_stock": safety_stock, # estoque de sgurança, incrementa o stock ideal
        "estoque_ideal": ideal_stock, # estoque ideal
        "pedir": faltante if faltante > 0 else 0
    }


async def get_graph_data_by_product_id_service(
    product_id: int,
    session: AsyncSession,
):
    print()
    movimento_case = case(
    (MovimentacoesEstoque.tipo == "entrada", MovimentacoesEstoque.quantidade),
    else_=-MovimentacoesEstoque.quantidade
    )

    saldo_cumulativo = func.sum(movimento_case).over(
        order_by=MovimentacoesEstoque.date
    )

    stmt_hist = (
        select(
            MovimentacoesEstoque.date.label("data"),
            saldo_cumulativo.label("estoque")
        )
        .where(MovimentacoesEstoque.id_produtos == product_id)
        .order_by(MovimentacoesEstoque.date.asc())
    )

    result_hist = await session.execute(stmt_hist)
    breakpoint()
    historico = [{"data": r.data, "estoque": r.estoque} for r in result_hist]

    stmt_prev = (
        select(
            Previsoes.data,
            Previsoes.estoque_previsto
        )
        .where(Previsoes.id_produtos == product_id)
        .order_by(Previsoes.data.asc())
    )
    result_prev = await session.execute(stmt_prev)
    previsoes = [{"data": r.data, "estoque_previsto": r.estoque_previsto} for r in result_prev]
    breakpoint()
    return {
        "historico": historico,
        "previsoes": previsoes
    }
