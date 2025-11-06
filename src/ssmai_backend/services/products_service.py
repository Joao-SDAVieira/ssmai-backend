from http import HTTPStatus
from json import dumps, loads
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.document import Document
from ssmai_backend.models.produto import Estoque, Produto, Previsoes
from ssmai_backend.models.user import User
from ssmai_backend.schemas.products_schemas import ProductSchema
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.settings import Settings

# def get_text_extracted():
#     return """
#             NF-C
#         RECEBEMOS DE GROWTH SUPPLEMENTS PRODUTOS ALIMES neios TDA os PRODUTOS CONSTANTES DA NOTA FISCAL INDIC ADA AO LADO
#         N. 014041259
#         DATA DE RECEBIMENTO
#         SÉRIE 17
#         IDENTIFICAÇÃO ASSINA TURA DO RECEREDOR
#         N2
#         Identificação do emitente
#         DANFE
#         Growth
#         GROWTH SUPPL EMENTS PRO
#         DOCUMEN MIXILIAR DA
#         DUTOS ALIMENTIC LTDA
#         NOTA ELETRÓNICA
#         CHAVE DE ACESSO DA NF-E
#         AVENIDA WILSON LEMOS, Date
#         0-ENTILADA
#         4225 1010 8326 4400 0108 5501 7014 0412 5914 6788 6817
#         Complements: GALPADIS
#         USAIDA
#         SANTA LUZIA
#         N. 014041259
#         TUUCASSO
#         Consulta de autenticidade no portal nacional da NF-e
#         SUPPLEMENTS
#         SERIE 17
#         Fone: 1063394
#         fazenda gov br/portal ou no site da SEFAZ Autorizada
#         FOLHA 01/01
#         NATUREZA D.A. OPERAÇÃO
#         PROTOCOLO DE AUTORIZAÇÃO DE USO
#         VENDA DE PRODUTOS
#         242250391243919 06/10/2025
#         INSCRIÇÃO ESTADUAL
#         INSC.ESTADUAL DO SUBST TRIM.
#         CNPJ/CPF
#         253860009
#         824016127112
#         10.832.644/0001-08
#         DESTINATARIO/REMETENTE
#         NOME/RAZÃO SOCIAL
#         CARRIER
#         DATA DE EMISSÃO
#         ЮЛО VICTOR DE OLIVEIRA VIEIRA
#         535 467 668-14
#         06/10/2025
#         ENDEREÇO
#         BAIRRO/DISTRITO
#         DATA ENTRADA/SAIDA
#         CEP
#         RUA MARIA JOSE DA CONCEICAO, 95, COLEGIO MARIA ANTONIA DE
#         06/10/2025
#         VILA ANDRADE
#         05730-170
#         MUNICIPIO
#         HORA ENTRADA/SAIDA
#         FONE/FAX
#         LF
#         INSCRIÇÃO ESTADUAL
#         SAO PAULO
#         15:22:00
#         .........
#         SP
#         FATURA
#         CALCULO DO IMPOSTO
#         BASE DE CALCULO DO ICMS
#         VALOR DO ICMS
#         VALOR DO ICMS SUBSTITUIÇÃO
#         VALOR TOTAL DOS PRODUTOS
#         BASE DE CALCULO DO ICMS SUBSTITUIÇÃO
#         266,51
#         31,98
#         0,00
#         0,00
#         308,54
#         VALOR DO FRETE
#         VALOR TOTAL DA NOTA
#         VALOR DO SEGURO
#         DESCONTO
#         OUTRAS DESPESAS ACESSÓRIAS
#         VALOR DO IPI
#         0,00
#         0,00
#         266,51
#         0,00
#         42.03
#         0,00
#         TRANSPORTADOR/VOLUMES TRANSPORTADOS
#         RAZÃO SOCIAL
#         CÓDIGO ANTI
#         PLACA DO VEICULO
#         UF
#         CNPJ/CPF
#         FRETE FOR CONTA
#         40 675 366/0002-66
#         RI SERVICOS DE ENTREGA E LOGISTICA LTDA
#         I-DESTINATARIO
#         ENDEREÇO
#         MUNICIPIO
#         UF
#         INSCRIÇÃO ESTADUAL
#         AV PRESIDENTE WILSON
#         SAO PAULO
#         SP
#         131542250119
#         QUANTIDADE
#         ESPECIE
#         MARCA
#         NUMERAÇÃO
#         PESO BRUTO
#         PESO LIQUIDO
#         VOLUME
#         3,000
#         3,000
#         DADOS DO PRODU
#         COD. PROD
#         DESCRIÇÃO DO PROD/SERV.
#         CFOP
#         QUANT
#         V.UNITARIO
#         V.TOTAL
#         BC.ICMS
#         V.ICMS
#         V.IPI
#         A.ICMS
#         A.IPI
#         NCM/SH
#         CST
#         UN
#         10003
#         WHEY PROTEIN CONCENTRADO 80% IKG CHOCOLATE
#         21061000
#         500
#         6107
#         UN
#         2,0000
#         138,770000
#         277,54
#         239,73
#         28,77
#         0,00
#         12.00%
#         0.00%
#         10004
#         PASTA AMENDOIM IKG
#         20081100
#         000
#         6107
#         UN
#         1,0000
#         31,000000
#         31,00
#         26,78
#         3,21
#         0,00
#         12.00%
#         0.00%
#         LCULO DO ISSON
#         SCRIÇÃO MUNICIPAL
#         VALOR TOTAL DOS SERVIÇOS
#         BASE DE CÁLCULO DO ISSQN
#         VALOR DO ISSQN
#         os ADICIONAIS
#         RMAÇÕES COMPLEMENTARES
#         RESERV ADO AO FISCO
#         colo 242250391243919
#         do ICMS relativo ao Fundo de Combate a Pobreza FCP da UF de destino RS
#         or do ICMS Interestadual para a UF de destino: RS 15.99 Valor do ICMS
#         NF-C
#         RECEBEMOS
#         DE
#         GROWTH
#         SUPPLEMENTS
#         PRODUTOS
#         ALIMES
#         neios
#         TDA
#         os
#         PRODUTOS
#         CONSTANTES
#         DA
#         NOTA
#         FISCAL
#         INDIC
#         ADA
#         AO LADO
#         N.
#         014041259
#         DATA
#         DE
#         RECEBIMENTO
#         SÉRIE
#         17
#         IDENTIFICAÇÃO
#         ASSINA
#         TURA
#         DO
#         RECEREDOR
#         N2
#         Identificação
#         do
#         emitente
#         DANFE
#         Growth
#         GROWTH
#         SUPPL
#         EMENTS
#         PRO
#         DOCUMEN
#         MIXILIAR
#         DA
#         DUTOS
#         ALIMENTIC
#         LTDA
#         NOTA
#         ELETRÓNICA
#         CHAVE
#         DE
#         ACESSO
#         DA
#         NF-E
#         AVENIDA
#         WILSON
#         LEMOS,
#         Date
#         0-ENTILADA
#         4225
#         1010
#         8326
#         4400
#         0108
#         5501
#         7014
#         0412
#         5914
#         6788
#         6817
#         Complements:
#         GALPADIS
#         USAIDA
#         SANTA
#         LUZIA
#         N.
#         014041259
#         TUUCASSO
#         Consulta
#         de
#         autenticidade
#         no
#         portal
#         nacional
#         da
#         NF-e
#         SUPPLEMENTS
#         SERIE
#         17
#         Fone:
#         1063394
#         fazenda
#         gov
#         br/portal
#         ou
#         no
#         site
#         da
#         SEFAZ
#         Autorizada
#         FOLHA
#         01/01
#         NATUREZA
#         D.A.
#         OPERAÇÃO
#         PROTOCOLO
#         DE
#         AUTORIZAÇÃO
#         DE
#         USO
#         VENDA
#         DE
#         PRODUTOS
#         242250391243919
#         06/10/2025
#         INSCRIÇÃO
#         ESTADUAL
#         INSC.ESTADUAL
#         DO
#         SUBST
#         TRIM.
#         CNPJ/CPF
#         253860009
#         824016127112
#         10.832.644/0001-08
#         DESTINATARIO/REMETENTE
#         NOME/RAZÃO
#         SOCIAL
#         CARRIER
#         DATA
#         DE
#         EMISSÃO
#         ЮЛО
#         VICTOR
#         DE
#         OLIVEIRA
#         VIEIRA
#         535 467 668-14
#         06/10/2025
#         ENDEREÇO
#         BAIRRO/DISTRITO
#         DATA
#         ENTRADA/SAIDA
#         CEP
#         RUA
#         MARIA
#         JOSE
#         DA
#         CONCEICAO,
#         95,
#         COLEGIO
#         MARIA
#         ANTONIA
#         DE
#         06/10/2025
#         VILA
#         ANDRADE
#         05730-170
#         MUNICIPIO
#         HORA
#         ENTRADA/SAIDA
#         FONE/FAX
#         LF
#         INSCRIÇÃO
#         ESTADUAL
#         SAO
#         PAULO
#         15:22:00
#         .........
#         SP
#         FATURA
#         CALCULO
#         DO
#         IMPOSTO
#         BASE
#         DE
#         CALCULO
#         DO
#         ICMS
#         VALOR
#         DO
#         ICMS
#         VALOR
#         DO
#         ICMS
#         SUBSTITUIÇÃO
#         VALOR
#         TOTAL
#         DOS
#         PRODUTOS
#         BASE
#         DE
#         CALCULO
#         DO
#         ICMS
#         SUBSTITUIÇÃO
#         266,51
#         31,98
#         0,00
#         0,00
#         308,54
#         VALOR
#         DO
#         FRETE
#         VALOR
#         TOTAL
#         DA
#         NOTA
#         VALOR
#         DO
#         SEGURO
#         DESCONTO
#         OUTRAS
#         DESPESAS
#         ACESSÓRIAS
#         VALOR
#         DO
#         IPI
#         0,00
#         0,00
#         266,51
#         0,00
#         42.03
#         0,00
#         TRANSPORTADOR/VOLUMES
#         TRANSPORTADOS
#         RAZÃO
#         SOCIAL
#         CÓDIGO
#         ANTI
#         PLACA
#         DO
#         VEICULO
#         UF
#         CNPJ/CPF
#         FRETE
#         FOR
#         CONTA
#         40
#         675
#         366/0002-66
#         RI
#         SERVICOS
#         DE
#         ENTREGA
#         E
#         LOGISTICA
#         LTDA
#         I-DESTINATARIO
#         ENDEREÇO
#         MUNICIPIO
#         UF
#         INSCRIÇÃO
#         ESTADUAL
#         AV
#         PRESIDENTE
#         WILSON
#         SAO
#         PAULO
#         SP
#         131542250119
#         QUANTIDADE
#         ESPECIE
#         MARCA
#         NUMERAÇÃO
#         PESO
#         BRUTO
#         PESO
#         LIQUIDO
#         VOLUME
#         3,000
#         3,000
#         DADOS
#         DO
#         PRODU
#         COD.
#         PROD
#         DESCRIÇÃO
#         DO
#         PROD/SERV.
#         CFOP
#         QUANT
#         V.UNITARIO
#         V.TOTAL
#         BC.ICMS
#         V.ICMS
#         V.IPI
#         A.ICMS
#         A.IPI
#         NCM/SH
#         CST
#         UN
#         10003
#         WHEY
#         PROTEIN
#         CONCENTRADO
#         80%
#         IKG
#         CHOCOLATE
#         21061000
#         500
#         6107
#         UN
#         2,0000
#         138,770000
#         277,54
#         239,73
#         28,77
#         0,00
#         12.00%
#         0.00%
#         10004
#         PASTA
#         AMENDOIM
#         IKG
#         20081100
#         000
#         6107
#         UN
#         1,0000
#         31,000000
#         31,00
#         26,78
#         3,21
#         0,00
#         12.00%
#         0.00%
#         LCULO
#         DO
#         ISSON
#         SCRIÇÃO
#         MUNICIPAL
#         VALOR
#         TOTAL
#         DOS
#         SERVIÇOS
#         BASE
#         DE
#         CÁLCULO
#         DO
#         ISSQN
#         VALOR
#         DO
#         ISSQN
#         os
#         ADICIONAIS
#         RMAÇÕES
#         COMPLEMENTARES
#         RESERV
#         ADO
#         AO
#         FISCO
#         colo
#         242250391243919
#         do
#         ICMS
#         relativo
#         ao
#         Fundo
#         de
#         Combate
#         a
#         Pobreza
#         FCP
#         da
#         UF
#         de
#         destino
#         RS
#         or
#         do
#         ICMS
#         Interestadual
#         para
#         a
#         UF
#         de
#         destino:
#         RS
#         15.99
#         Valor
#         do
#         ICMS
#     """


def get_bedrock_prompt(text_extracted: str):
    # text_extracted = get_text_extracted()
    
    prompt = f"""
        Você é um extrator de produtos. Receberá um TEXTO CRU extraído por OCR. 
        Extrair e devolver **apenas JSON válido** com os campos:
        - tipo_produto (string)
        - capacidade (número, sem unidade)
        - unidade_de_medida_capacidade (litros, kg, unidades, etc)
        - quantidade_individual (int)  -> unidades por embalagem (ex: "Contém 10 unid." -> 10)
        - quantidade_entrada (int)     -> quantos pacotes/itens estão entrando (se presente)
        - marca (string)
        - tamanho (string)             -> formato "63 cm x 80 cm" se aplicável
        - custo_und (float)                -> custo unitário, se houver apenas o total, divida pela quantidade_entrada (ex: valor total: 100, quantidade_entrada: 2 -> 50)
        REGRAS:
        1) Sempre tente padronizar unidades: volumes → "litros", pesos → "kg". 
        Exemplos de conversão automática:
        - "50L", "50 L", "50 Litros" -> capacidade: 50, unidade_de_medida_capacidade: "litros"
        - "500 g", "500g" -> capacidade: 0.5, unidade_de_medida_capacidade: "kg"
        - "2000 ml" -> capacidade: 2.0, unidade_de_medida_capacidade: "litros"
        2) Se não encontrar um campo, coloque `null`.
        3) Se o texto contiver múltiplas indicações (ex: "Contém 10 unid." e "50 50L"), tente inferir:
        - quantidade_individual = unidades por pacote (ex: 10)
        - capacidade = volume/peso por unidade (ex: 50), unidade_de_medida_capacidade = "litros"
        4) Retorne apenas JSON puro **sem** explicações.

        Exemplos:

        INPUT: "SACOS P/ LIXO Med. 63 cm X 80 cm Contém 10 unid. 50 50L JHIENE"
        OUTPUT:
        {{
        "tipo_produto": "Saco para lixo",
        "capacidade": 50,
        "unidade_de_medida_capacidade": "litros",
        "quantidade_individual": 10,
        "quantidade_entrada": null,
        "marca": "JHIENE",
        "tamanho": "63 cm x 80 cm",
        }}

        Agora extraia do texto abaixo:
        ---INÍCIO DO TEXTO---
        {text_extracted}
        ---FIM DO TEXTO---
        """

    bedrock_request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                    {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                    }
            ],
            "max_tokens": 128,
            "temperature": 0.5
            }
    return bedrock_request_body


async def find_product_by_id_if_same_enterpryse(id: int, session: AsyncSession, current_user: User):
    product_db = await session.scalar(select(Produto).where(Produto.id == id))
    if not product_db:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Product or Stock not found!",
        )
    if product_db.id_empresas != current_user.id_empresas:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Unauthorized'
        )

    return product_db


async def create_product_service(
    product: ProductSchema,
    session: AsyncSession,
    current_user: User,
    is_batch=False
):
    db_product = await session.scalar(
        select(Produto).where(
            and_(
                Produto.nome == product.nome,
                Produto.id_empresas == current_user.id_empresas
            )
            )
    )

    if db_product:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Product already exists!"
        )

    db_product = Produto(
        nome=product.nome,
        categoria=product.categoria,
        id_empresas=current_user.id_empresas
    )

    session.add(db_product)

    await session.commit()
    await session.refresh(db_product)
    estoque_db = Estoque(
        id_produtos=db_product.id,
        quantidade_disponivel=0,
        custo_medio=0
        )
    session.add(estoque_db)
    await session.commit()

    return db_product


async def read_all_products_service(session: AsyncSession,
                                    filter: FilterPage):
    return await session.scalars(
        select(Produto).offset(filter.offset).limit(filter.limit)
    )


async def read_all_products_by_user_enterpryse_service(
        session: AsyncSession,
        filter: FilterPage,
        current_user: User
):
    return await session.scalars(
        select(Produto).where(
            Produto.id_empresas == current_user.id_empresas
            ).offset(filter.offset).limit(filter.limit)
    )


async def delete_product_by_id_service(id: int, session: AsyncSession, current_user: User):
    product_db = await find_product_by_id_if_same_enterpryse(id, session, current_user)

    await session.delete(product_db)
    await session.commit()
    return "Product deleted!"


async def update_product_by_id_service(
    id: int, product: ProductSchema, session: AsyncSession, current_user: User
):
    product_db = await find_product_by_id_if_same_enterpryse(id, session, current_user)
    product_with_same_name = await session.scalar(
        select(Produto).where(Produto.nome == product.nome)
    )
    if (
        product_with_same_name
        and product_with_same_name.id != product_db.id
    ):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Product already exists!"
        )

    product_db.nome = product.nome
    product_db.categoria = product.categoria
    await session.commit()
    await session.refresh(product_db)
    return product_db


async def create_product_by_document_service(
    document: UploadFile,
    session: AsyncSession,
    s3_client,
    textract_client,
    current_user: User
):
    SETTINGS = Settings()
    IMAGE_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
    ext = document.filename.split('.')[-1]

    EMPRESA_DEFAULT_ID = 1  # TODO: Ajustar

    filename_with_ext = (
        f'uploads/{EMPRESA_DEFAULT_ID}/documents_to_extract/{uuid4()}.{ext}'
    )

    if document.content_type in IMAGE_MIME_TYPES:
        await s3_client.upload_fileobj(
            document.file,
            SETTINGS.S3_BUCKET,
            filename_with_ext,
            ExtraArgs={'ContentType': 'image/jpeg'},
        )

    document_db = Document(extracted=False, id_empresas= current_user.id_empresas,
             document_path=f'https://{SETTINGS.S3_BUCKET}.s3.{SETTINGS.REGION}.amazonaws.com/{filename_with_ext}')
    session.add(document_db)
    await session.commit()

    response = await textract_client.detect_document_text(
        Document={
            "S3Object": {
                "Bucket": SETTINGS.S3_BUCKET,
                "Name": filename_with_ext
            }
        }
    )
    text_clean = "\n".join(
        block["Text"]
        for block in response["Blocks"] if block["BlockType"] in ("LINE", "WORD")
    )
    document_db.extract_result = text_clean
    document_db.extracted = True
    await session.commit()
    await session.refresh(document_db)

    return document_db


async def generate_product_info_from_docs_pre_extracted_service(
    session: AsyncSession,
    bedrock_client,
    id_text_extract: int
):
    document_db = await session.scalar(
        select(Document).where(Document.id == id_text_extract)
    )
    if not document_db or not document_db.extract_result:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Extract with id {id_text_extract} not found!",
        )
    # colher de chá, comente daqui ate
    bedrock_response = await bedrock_client.invoke_model(
        modelId=Settings().CLOUDE_INFERENCE_PROFILE,
        body=dumps(get_bedrock_prompt(document_db.extract_result))
    )

    body_brute = await bedrock_response['body'].read()
    response_body: dict = loads(body_brute)
    response_ai_json: dict = loads(response_body['content'][0]['text'])
    # aqui. Depois descomente o json debaixo
    # response_ai_json = {
    #                 "tipo_produto": "Whey Protein",
    #                 "capacidade": 1,
    #                 "unidade_de_medida_capacidade": "kg",
    #                 "quantidade_individual": 1,
    #                 "quantidade_entrada": 2,
    #                 "marca": "Growth Supplements",
    #                 "tamanho": None,
    #                 "custo_und": 138.77
    #             }

    # se não funcionar comenta o bedrock_client dessa função e da chamada/depends dela na rota generate_product_info_from_docs_pre_extracted
    product_name = ''
    product_type = ''
    quantidade_entrada = 1
    custo_und = 0.0

    if response_ai_json['tipo_produto']:
        product_name += response_ai_json['tipo_produto']
        product_type = response_ai_json['tipo_produto']

    if response_ai_json['capacidade']:
        product_name += f" | {response_ai_json['capacidade']}{
           response_ai_json['unidade_de_medida_capacidade'] if response_ai_json['unidade_de_medida_capacidade'] else ''
        }"

    if response_ai_json['quantidade_individual']:
        product_name += f" | {response_ai_json['quantidade_individual'] }und"

    if response_ai_json['quantidade_entrada']:
        quantidade_entrada = response_ai_json['quantidade_entrada']

    if response_ai_json['marca']:
        product_name += f" | {response_ai_json['marca']}"

    if response_ai_json['tamanho']:
        product_name += f" | {response_ai_json['tamanho']}"

    if response_ai_json['custo_und']:
        custo_und = response_ai_json['custo_und']

    informations_values = {
        "document_id": document_db.id,
        "nome": product_name,
        "custo_und": custo_und,
        "quantidade": quantidade_entrada,
        "categoria": product_type,
    }

    document_db.ai_result = str(informations_values)
    await session.commit()

    return informations_values


async def insert_products_with_csv_service(
    session: AsyncSession,
    current_user: User,
    csv_file: UploadFile
):
    if not csv_file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Unexpected format"
        )
    contents = await csv_file.read()
    try:
        df_produtos = pd.read_csv(pd.io.common.BytesIO(contents))
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Unable to read CSV"
        )
    required_columns = {"id", "nome", "categoria", "created_at", "updated_at"}
    if not required_columns.issubset(df_produtos.columns):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"CSV deve conter as colunas: {', '.join(required_columns)}"
        )

    df_produtos["id_empresas"] = current_user.id_empresas

    products_dict = df_produtos.to_dict(orient="records")
    df_estoque = pd.DataFrame({
        "id": df_produtos["id"],
        "id_produtos": df_produtos["id"],
        "quantidade_disponivel": 0,
        "custo_medio": 0.0,
        "created_at": df_produtos['created_at'],
        "updated_at": df_produtos['updated_at']
        })

    estoque_dict = df_estoque.to_dict(orient="records")
    try:
        await session.execute(insert(Produto), products_dict)
        await session.execute(insert(Estoque), estoque_dict)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao inserir dados: {e}")

    return {'message': 'success'}


async def delete_all_products_by_enterpryse_id_service(
    session: AsyncSession,
    enterpryse_id: int,
):
    await session.execute(
        delete(Produto)
        .where(Produto.id_empresas == enterpryse_id)
        )
    
    await session.commit()
    return {'message': 'deleted!'}


async def create_product_by_document_service_fake(current_user: User,document, session: AsyncSession):
    document =  Document(extracted=False,
             document_path=f'https://fake.s3.fake.amazonaws.com/fake.com')
    document.extract_result = 'get_text_extracted()'
    document.extracted = True
    document.id_empresas = current_user.id_empresas
    session.add(document)
    await session.commit()
    await session.refresh(document)

    return document


async def get_all_products_with_analysis_service(
        session: AsyncSession,
        filter: FilterPage,
        current_user: User
):
    
    stmt_join = (
    select(Produto)
    .join(Previsoes, Produto.id == Previsoes.id_produtos)
    .where(Produto.id_empresas == current_user.id_empresas)
    .distinct().limit(filter.limit).offset(filter.offset)
    )
    products_db = await session.scalars(stmt_join)
    return products_db.all()


async def update_product_image_service(
    image: UploadFile,
    session: AsyncSession,
    current_user: User,
    s3_client,
    product_id):
    settings = Settings()
    if not image:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='No image file was uploaded.',
        )
    ALOOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
    ext = image.filename.split('.')[-1]
    if image.content_type not in ALOOWED_MIME_TYPES:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Unsupported file type'
        )
    filename_with_ext = f'uploads/{current_user.id_empresas}/product/{product_id}/image.{ext}'
    
    product_db = await session.scalar(select(Produto).where(
        and_(Produto.id_empresas == current_user.id_empresas,Produto.id == product_id)
        ))
    
    if not product_db:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Product not found!')

    await s3_client.upload_fileobj(
        image.file,
        settings.S3_BUCKET,
        filename_with_ext,
        ExtraArgs={'ContentType': 'image/jpeg'},
    )

    
    product_db.image = f'https://{settings.S3_BUCKET}.s3.{settings.REGION}.amazonaws.com/{filename_with_ext}'
    await session.commit()

    return product_db