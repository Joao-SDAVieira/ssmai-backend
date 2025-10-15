from http import HTTPStatus
from uuid import uuid4
from json import dumps, loads

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.document import Document
from ssmai_backend.models.produto import Produto
from ssmai_backend.schemas.products_schemas import ProductSchema
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.settings import Settings

def get_bedrock_prompt(text_extracted: str):
    # TODO: adicionar preço
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
        "raw_text": "SACOS P/ LIXO Med. 63 cm X 80 cm Contém 10 unid. 50 50L JHIENE"
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


async def create_product_service(
    product: ProductSchema, session: AsyncSession
):
    db_product = await session.scalar(
        select(Produto).where(Produto.nome == product.nome)
    )

    if db_product:  # TODO: alterar para o mesmo user
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail="Product already exists!"
        )

    db_product = Produto(
        nome=product.nome,
        custo_und=product.custo_und,
        quantidade=product.quantidade,
        categoria=product.categoria,
    )

    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


async def read_all_products_service(session: AsyncSession, filter: FilterPage):
    return await session.scalars(
        select(Produto).offset(filter.offset).limit(filter.limit)
    )


# TODO: para endpoints de alteração, verificar se
#  o produto é do usuário que criou (perm)


async def delete_product_by_id_service(id: int, session: AsyncSession):
    product_db = await find_by_product_by_id(id, session)

    # TODO: se usuário é dono do produto
    await session.delete(product_db)
    await session.commit()
    return "Product deleted!"


async def update_product_by_id_service(
    id: int, product: ProductSchema, session: AsyncSession
):
    product_db: Produto = await find_by_product_by_id(id, session)
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
    product_db.preco = product.custo_und
    product_db.quantidade = product.quantidade
    await session.commit()
    await session.refresh(product_db)
    return product_db


async def find_by_product_by_id(id: int, session: AsyncSession):
    product_db = await session.scalar(select(Produto).where(Produto.id == id))
    if not product_db:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Product with id {id} not found!",
        )
    return product_db


async def create_product_by_document_service(
    document: UploadFile,
    session: AsyncSession,
    s3_client,
    textract_client
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

    document_db = Document(extracted=False,
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
    
    bedrock_response = await bedrock_client.invoke_model(
        modelId=Settings().CLOUDE_INFERENCE_PROFILE,
        body=dumps(get_bedrock_prompt(document_db.extract_result))
    )

    body_brute = await bedrock_response['body'].read()
    response_body:dict = loads(body_brute)
    response_ai_json = loads(response_body['content'][0]['text'])

    # response_ai_json = {
    #                 "tipo_produto": "Whey Protein",
    #                 "capacidade": 1,
    #                 "unidade_de_medida_capacidade": "kg",
    #                 "quantidade_individual": 1,
    #                 "quantidade_entrada": 2,
    #                 "marca": "Growth Supplements",
    #                 "tamanho": None,
    #                 "sabor": "Chocolate"
    #             }
    product_name = ''
    # capacity = ''
    # capacity_measureme = ''
    individual_quantity = 1
    product_type = ''
    # product_brand = ''
    quantidade_entrada = 1
    # size = ""
    
    
    if response_ai_json['tipo_produto']:
        product_name += response_ai_json['tipo_produto']
        product_type = response_ai_json['tipo_produto']

    if response_ai_json['capacidade']:
        product_name += f" | {response_ai_json['capacidade']}{
           response_ai_json['unidade_de_medida_capacidade'] if response_ai_json['unidade_de_medida_capacidade'] else ''
        }"
        # capacity = response_ai_json['capacidade']

    if response_ai_json['quantidade_individual']:
        product_name += f" | {response_ai_json['quantidade_individual'] }und"
        individual_quantity = response_ai_json['quantidade_individual']

    if response_ai_json['quantidade_entrada']:
        quantidade_entrada = response_ai_json['quantidade_entrada']
    
    if response_ai_json['marca']:
        product_name += f" | {response_ai_json['marca']}"
        # product_brand = response_ai_json['marca']

    if response_ai_json['tamanho']:
        product_name += f" | {response_ai_json['tamanho']}"
        # size = response_ai_json['marca']



    informations_values ={
        "document_id": document_db.id,
        "nome": product_name,
        "preco": 0.0,
        "quantidade": quantidade_entrada,
        "categoria": product_type, 
        "individual_quantity": individual_quantity,
    }
    
    document_db.ai_result = str(informations_values)

    await session.commit()

    return informations_values
    