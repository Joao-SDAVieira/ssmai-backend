import io
from scipy.stats import norm
import numpy as np
from http import HTTPStatus

from ssmai_backend.models.user import User
from ssmai_backend.models.produto import MovimentacoesEstoque, Produto, Estoque, Previsoes
from ssmai_backend.settings import Settings

from sqlalchemy import func, select, case, delete, insert, ScalarResult, and_, Integer
from sqlalchemy.sql.expression import cast
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from prophet import Prophet
from fastapi import HTTPException


async def generate_dataset_moviments(session, id_produtos: int=None):
    subquery_stmt = (
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
    )
    if id_produtos is not None:
        subquery_stmt = subquery_stmt.where(MovimentacoesEstoque.id_produtos == id_produtos)
    subquery = subquery_stmt.subquery()

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
    moviments = dataset.all()
    if len(moviments) == 0:
        raise HTTPException(status_code=HTTPStatus.CONFLICT,
                            detail='Product without moviments')
    return moviments


async def generate_moviments_df(session, id_produtos: int=None):
    dataset = await generate_dataset_moviments(session, id_produtos)
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


async def prepare_dataframe_to_train(df_dataset: pd.DataFrame, product_id: int = None) -> pd.DataFrame:
    if product_id:
        df_dataset: pd.DataFrame = df_dataset[df_dataset['id_produto'] == product_id]
    df_prophet = df_dataset[["data", "quantidade_saida"]].rename(columns={"data": "ds", "quantidade_saida": "y"})
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


async def calculate_ideal_stock_by_df_forecast(df_forecast: pd.DataFrame):
    future_stock = df_forecast.tail(15)['saida_prevista']
    standart_deviation = future_stock.std()
    lead_time=7
    diary_average = future_stock.mean()
    service_level = 0.95,
    score = norm.ppf(service_level)
    demanda_leadtime = diary_average * lead_time
    safety_stock = score * standart_deviation * np.sqrt(lead_time)
    return demanda_leadtime + safety_stock


async def add_forecast_on_db_by_product_id(product_id: int,
                                           df_forecast: pd.DataFrame,
                                           session: AsyncSession):
    statement = delete(Previsoes).where(Previsoes.id_produtos == product_id)

    await session.execute(statement)
    df_forecast = df_forecast[['ds', 'yhat']].rename(
        columns={'ds': 'data', 'yhat': 'saida_prevista'}
        )
    df_forecast['id_produtos'] = product_id
    forecast_dict = df_forecast.to_dict(orient="records")
    await session.execute(insert(Previsoes), forecast_dict)
    stock_db = await session.scalar(select(Estoque).where(Estoque.id_produtos == product_id))
    estoque_ideal = await calculate_ideal_stock_by_df_forecast(df_forecast)  
    stock_db.estoque_ideal = float(estoque_ideal.item())


async def create_df_by_object_model_list(obj_list: list[ScalarResult]):
    data = [ 
    {key: value for key, value in obj.__dict__.items() if not key.startswith('_')} 
    for obj in obj_list
    ]
    return pd.DataFrame(data)


async def update_by_product_id_service(current_user, session, product_id):
    ai_model = Prophet()
    df_dataset = await generate_moviments_df(session, product_id)
    df_to_prophet = await prepare_dataframe_to_train(df_dataset)
    df_forecast = await create_forecast(df_to_prophet, ai_model)
    await add_forecast_on_db_by_product_id(product_id, df_forecast, session)
    await session.commit()
    return {"message": 'Coleta realizada'}


async def update_ai_predictions_to_enterpryse_service(
    current_user: User,
    session: AsyncSession
):
    df_dataset = await generate_moviments_df(session)
    product_ids = df_dataset['id_produto'].unique()
    for product_id in product_ids:
        ai_model = Prophet()
        df_to_prophet = await prepare_dataframe_to_train(df_dataset, product_id)
        df_forecast = await create_forecast(df_to_prophet, ai_model)
        await add_forecast_on_db_by_product_id(product_id, df_forecast, session)
    await session.commit()
    return {"message": 'Coleta realizada'}


async def get_analysis_by_product_id_service(
    product_id: int,
    session: AsyncSession,
    service_level: float=0.95,
    lead_time=2
):
    forecasts_db = await session.scalars(select(Previsoes).where(Previsoes.id_produtos == product_id))
    if not forecasts_db.first():
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail='Forecast not found to this product')
    df_forecast = await create_df_by_object_model_list(forecasts_db.all())

    stock_db = await session.scalar(select(Estoque).where(Estoque.id_produtos == product_id))

    future_stock = df_forecast.tail(15)['saida_prevista']

    score = norm.ppf(service_level)

    diary_average = future_stock.mean()
    standart_deviation = future_stock.std()
    demanda_leadtime = diary_average * lead_time
    safety_stock = score * standart_deviation * np.sqrt(lead_time)

    ideal_stock = demanda_leadtime + safety_stock
    faltante = ideal_stock - stock_db.quantidade_disponivel
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

    stmt_hist = (
        select(
            func.date(MovimentacoesEstoque.date).label("data"),
            func.sum(
                case((MovimentacoesEstoque.tipo == "saida", MovimentacoesEstoque.quantidade), else_=0)
            ).label("saida_dia")
        )
        .where(MovimentacoesEstoque.id_produtos == product_id)
        .group_by(func.date(MovimentacoesEstoque.date))
        .order_by(func.date(MovimentacoesEstoque.date).asc())
    )

    result_hist = await session.execute(stmt_hist)
    historico = [{"data": r.data, "estoque": r.saida_dia} for r in result_hist]
    if len(historico) == 0:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Without moviments to this product')

    ultima_data = historico[-1]["data"] if historico else None
    
    stmt_prev = (
        select(
            Previsoes.data,
            Previsoes.saida_prevista
        )
        .where(
            and_(
                Previsoes.id_produtos == product_id,
                Previsoes.data > ultima_data
            )
        )
        .order_by(Previsoes.data.asc())
    )
    result_prev = await session.execute(stmt_prev)
    
    previsoes = [{"data": r.data, "saida_prevista": int(r.saida_prevista)} for r in result_prev]
    return {
        "historico": historico,
        "previsoes": previsoes
    }


async def get_worst_stock_deviation_service(session: AsyncSession, current_user: User):
    
    difference_percent_schema = case(
        (Estoque.estoque_ideal == 0, None),
        else_ = (
            (Estoque.quantidade_disponivel - Estoque.estoque_ideal) / Estoque.estoque_ideal
        ) * 100.0
    ).label("difference_percent")

    abs_difference_percent = case(
        (
            (Estoque.estoque_ideal == 0) & (Estoque.quantidade_disponivel > 0),
            9999999.0
        ),
        (
            (Estoque.estoque_ideal == 0) & (Estoque.quantidade_disponivel <= 0),
            0.0
        ),
        else_=func.abs(
            (Estoque.quantidade_disponivel - Estoque.estoque_ideal) / Estoque.estoque_ideal
        ) * 100.0
    ).label("abs_difference_percent")

    difference_quantity = cast(
        (Estoque.quantidade_disponivel - Estoque.estoque_ideal), Integer
    ).label("difference_quantity")
    bigger_than_expected = case(
        ((Estoque.quantidade_disponivel - Estoque.estoque_ideal) > 0, True),
        else_=False
    ).label("bigger_than_expected")

    cash_loss = ((Estoque.quantidade_disponivel - Estoque.estoque_ideal) * Estoque.custo_medio).label("cash_loss")

    stmt = (
        select(
            Estoque.id,
            Estoque.id_produtos,
            Estoque.quantidade_disponivel,
            Estoque.custo_medio,
            Estoque.estoque_ideal,
            Estoque.created_at,
            Estoque.updated_at,
            
            difference_percent_schema,
            difference_quantity,
            bigger_than_expected,
            cash_loss,
            abs_difference_percent
        )
        .join(Produto, Estoque.id_produtos == Produto.id) 
        .where(
            and_(
                Estoque.estoque_ideal.isnot(None),
                Produto.id_empresas == current_user.id_empresas 
            )
        )
        .order_by(
            abs_difference_percent.desc()
        )
        .limit(10)
    )

    result = await session.execute(stmt)
    
    df = pd.DataFrame(result.all())
    

    if df.empty:
        return []

    df['difference_percent'] = df['difference_percent'].fillna(0.0)

    df = df.drop(columns=['abs_difference_percent'], errors='ignore')
    stock_cols = [
        "id", "id_produtos", "quantidade_disponivel", "custo_medio", 
        "estoque_ideal", "created_at", "updated_at"
    ]
    
    indicator_cols = [
        "difference_percent", "difference_quantity", 
        "bigger_than_expected", "cash_loss"
    ]

    response_data = []
    
    for _, row in df.iterrows():
        stock_data = row[stock_cols].to_dict()
        indicator_data = row[indicator_cols].to_dict()
        
        response_data.append({
            "indicators": indicator_data,
            "stock": stock_data
        })
        
    return response_data
    return df.to_dict(orient="records")