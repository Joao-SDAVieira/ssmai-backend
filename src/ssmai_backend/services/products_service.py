from http import HTTPStatus
from uuid import uuid4
from json import dumps, loads

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ssmai_backend.models.document import Document
from ssmai_backend.models.produto import Produto, Estoque
from ssmai_backend.schemas.products_schemas import ProductSchema
from ssmai_backend.schemas.root_schemas import FilterPage
from ssmai_backend.settings import Settings

def get_bedrock_prompt(text_extracted: str):

    # text_extracted = """
    #         NF-C
    #     RECEBEMOS DE GROWTH SUPPLEMENTS PRODUTOS ALIMES neios TDA os PRODUTOS CONSTANTES DA NOTA FISCAL INDIC ADA AO LADO
    #     N. 014041259
    #     DATA DE RECEBIMENTO
    #     SÉRIE 17
    #     IDENTIFICAÇÃO ASSINA TURA DO RECEREDOR
    #     N2
    #     Identificação do emitente
    #     DANFE
    #     Growth
    #     GROWTH SUPPL EMENTS PRO
    #     DOCUMEN MIXILIAR DA
    #     DUTOS ALIMENTIC LTDA
    #     NOTA ELETRÓNICA
    #     CHAVE DE ACESSO DA NF-E
    #     AVENIDA WILSON LEMOS, Date
    #     0-ENTILADA
    #     4225 1010 8326 4400 0108 5501 7014 0412 5914 6788 6817
    #     Complements: GALPADIS
    #     USAIDA
    #     SANTA LUZIA
    #     N. 014041259
    #     TUUCASSO
    #     Consulta de autenticidade no portal nacional da NF-e
    #     SUPPLEMENTS
    #     SERIE 17
    #     Fone: 1063394
    #     fazenda gov br/portal ou no site da SEFAZ Autorizada
    #     FOLHA 01/01
    #     NATUREZA D.A. OPERAÇÃO
    #     PROTOCOLO DE AUTORIZAÇÃO DE USO
    #     VENDA DE PRODUTOS
    #     242250391243919 06/10/2025
    #     INSCRIÇÃO ESTADUAL
    #     INSC.ESTADUAL DO SUBST TRIM.
    #     CNPJ/CPF
    #     253860009
    #     824016127112
    #     10.832.644/0001-08
    #     DESTINATARIO/REMETENTE
    #     NOME/RAZÃO SOCIAL
    #     CARRIER
    #     DATA DE EMISSÃO
    #     ЮЛО VICTOR DE OLIVEIRA VIEIRA
    #     535 467 668-14
    #     06/10/2025
    #     ENDEREÇO
    #     BAIRRO/DISTRITO
    #     DATA ENTRADA/SAIDA
    #     CEP
    #     RUA MARIA JOSE DA CONCEICAO, 95, COLEGIO MARIA ANTONIA DE
    #     06/10/2025
    #     VILA ANDRADE
    #     05730-170
    #     MUNICIPIO
    #     HORA ENTRADA/SAIDA
    #     FONE/FAX
    #     LF
    #     INSCRIÇÃO ESTADUAL
    #     SAO PAULO
    #     15:22:00
    #     .........
    #     SP
    #     FATURA
    #     CALCULO DO IMPOSTO
    #     BASE DE CALCULO DO ICMS
    #     VALOR DO ICMS
    #     VALOR DO ICMS SUBSTITUIÇÃO
    #     VALOR TOTAL DOS PRODUTOS
    #     BASE DE CALCULO DO ICMS SUBSTITUIÇÃO
    #     266,51
    #     31,98
    #     0,00
    #     0,00
    #     308,54
    #     VALOR DO FRETE
    #     VALOR TOTAL DA NOTA
    #     VALOR DO SEGURO
    #     DESCONTO
    #     OUTRAS DESPESAS ACESSÓRIAS
    #     VALOR DO IPI
    #     0,00
    #     0,00
    #     266,51
    #     0,00
    #     42.03
    #     0,00
    #     TRANSPORTADOR/VOLUMES TRANSPORTADOS
    #     RAZÃO SOCIAL
    #     CÓDIGO ANTI
    #     PLACA DO VEICULO
    #     UF
    #     CNPJ/CPF
    #     FRETE FOR CONTA
    #     40 675 366/0002-66
    #     RI SERVICOS DE ENTREGA E LOGISTICA LTDA
    #     I-DESTINATARIO
    #     ENDEREÇO
    #     MUNICIPIO
    #     UF
    #     INSCRIÇÃO ESTADUAL
    #     AV PRESIDENTE WILSON
    #     SAO PAULO
    #     SP
    #     131542250119
    #     QUANTIDADE
    #     ESPECIE
    #     MARCA
    #     NUMERAÇÃO
    #     PESO BRUTO
    #     PESO LIQUIDO
    #     VOLUME
    #     3,000
    #     3,000
    #     DADOS DO PRODU
    #     COD. PROD
    #     DESCRIÇÃO DO PROD/SERV.
    #     CFOP
    #     QUANT
    #     V.UNITARIO
    #     V.TOTAL
    #     BC.ICMS
    #     V.ICMS
    #     V.IPI
    #     A.ICMS
    #     A.IPI
    #     NCM/SH
    #     CST
    #     UN
    #     10003
    #     WHEY PROTEIN CONCENTRADO 80% IKG CHOCOLATE
    #     21061000
    #     500
    #     6107
    #     UN
    #     2,0000
    #     138,770000
    #     277,54
    #     239,73
    #     28,77
    #     0,00
    #     12.00%
    #     0.00%
    #     10004
    #     PASTA AMENDOIM IKG
    #     20081100
    #     000
    #     6107
    #     UN
    #     1,0000
    #     31,000000
    #     31,00
    #     26,78
    #     3,21
    #     0,00
    #     12.00%
    #     0.00%
    #     LCULO DO ISSON
    #     SCRIÇÃO MUNICIPAL
    #     VALOR TOTAL DOS SERVIÇOS
    #     BASE DE CÁLCULO DO ISSQN
    #     VALOR DO ISSQN
    #     os ADICIONAIS
    #     RMAÇÕES COMPLEMENTARES
    #     RESERV ADO AO FISCO
    #     colo 242250391243919
    #     do ICMS relativo ao Fundo de Combate a Pobreza FCP da UF de destino RS
    #     or do ICMS Interestadual para a UF de destino: RS 15.99 Valor do ICMS
    #     NF-C
    #     RECEBEMOS
    #     DE
    #     GROWTH
    #     SUPPLEMENTS
    #     PRODUTOS
    #     ALIMES
    #     neios
    #     TDA
    #     os
    #     PRODUTOS
    #     CONSTANTES
    #     DA
    #     NOTA
    #     FISCAL
    #     INDIC
    #     ADA
    #     AO LADO
    #     N.
    #     014041259
    #     DATA
    #     DE
    #     RECEBIMENTO
    #     SÉRIE
    #     17
    #     IDENTIFICAÇÃO
    #     ASSINA
    #     TURA
    #     DO
    #     RECEREDOR
    #     N2
    #     Identificação
    #     do
    #     emitente
    #     DANFE
    #     Growth
    #     GROWTH
    #     SUPPL
    #     EMENTS
    #     PRO
    #     DOCUMEN
    #     MIXILIAR
    #     DA
    #     DUTOS
    #     ALIMENTIC
    #     LTDA
    #     NOTA
    #     ELETRÓNICA
    #     CHAVE
    #     DE
    #     ACESSO
    #     DA
    #     NF-E
    #     AVENIDA
    #     WILSON
    #     LEMOS,
    #     Date
    #     0-ENTILADA
    #     4225
    #     1010
    #     8326
    #     4400
    #     0108
    #     5501
    #     7014
    #     0412
    #     5914
    #     6788
    #     6817
    #     Complements:
    #     GALPADIS
    #     USAIDA
    #     SANTA
    #     LUZIA
    #     N.
    #     014041259
    #     TUUCASSO
    #     Consulta
    #     de
    #     autenticidade
    #     no
    #     portal
    #     nacional
    #     da
    #     NF-e
    #     SUPPLEMENTS
    #     SERIE
    #     17
    #     Fone:
    #     1063394
    #     fazenda
    #     gov
    #     br/portal
    #     ou
    #     no
    #     site
    #     da
    #     SEFAZ
    #     Autorizada
    #     FOLHA
    #     01/01
    #     NATUREZA
    #     D.A.
    #     OPERAÇÃO
    #     PROTOCOLO
    #     DE
    #     AUTORIZAÇÃO
    #     DE
    #     USO
    #     VENDA
    #     DE
    #     PRODUTOS
    #     242250391243919
    #     06/10/2025
    #     INSCRIÇÃO
    #     ESTADUAL
    #     INSC.ESTADUAL
    #     DO
    #     SUBST
    #     TRIM.
    #     CNPJ/CPF
    #     253860009
    #     824016127112
    #     10.832.644/0001-08
    #     DESTINATARIO/REMETENTE
    #     NOME/RAZÃO
    #     SOCIAL
    #     CARRIER
    #     DATA
    #     DE
    #     EMISSÃO
    #     ЮЛО
    #     VICTOR
    #     DE
    #     OLIVEIRA
    #     VIEIRA
    #     535 467 668-14
    #     06/10/2025
    #     ENDEREÇO
    #     BAIRRO/DISTRITO
    #     DATA
    #     ENTRADA/SAIDA
    #     CEP
    #     RUA
    #     MARIA
    #     JOSE
    #     DA
    #     CONCEICAO,
    #     95,
    #     COLEGIO
    #     MARIA
    #     ANTONIA
    #     DE
    #     06/10/2025
    #     VILA
    #     ANDRADE
    #     05730-170
    #     MUNICIPIO
    #     HORA
    #     ENTRADA/SAIDA
    #     FONE/FAX
    #     LF
    #     INSCRIÇÃO
    #     ESTADUAL
    #     SAO
    #     PAULO
    #     15:22:00
    #     .........
    #     SP
    #     FATURA
    #     CALCULO
    #     DO
    #     IMPOSTO
    #     BASE
    #     DE
    #     CALCULO
    #     DO
    #     ICMS
    #     VALOR
    #     DO
    #     ICMS
    #     VALOR
    #     DO
    #     ICMS
    #     SUBSTITUIÇÃO
    #     VALOR
    #     TOTAL
    #     DOS
    #     PRODUTOS
    #     BASE
    #     DE
    #     CALCULO
    #     DO
    #     ICMS
    #     SUBSTITUIÇÃO
    #     266,51
    #     31,98
    #     0,00
    #     0,00
    #     308,54
    #     VALOR
    #     DO
    #     FRETE
    #     VALOR
    #     TOTAL
    #     DA
    #     NOTA
    #     VALOR
    #     DO
    #     SEGURO
    #     DESCONTO
    #     OUTRAS
    #     DESPESAS
    #     ACESSÓRIAS
    #     VALOR
    #     DO
    #     IPI
    #     0,00
    #     0,00
    #     266,51
    #     0,00
    #     42.03
    #     0,00
    #     TRANSPORTADOR/VOLUMES
    #     TRANSPORTADOS
    #     RAZÃO
    #     SOCIAL
    #     CÓDIGO
    #     ANTI
    #     PLACA
    #     DO
    #     VEICULO
    #     UF
    #     CNPJ/CPF
    #     FRETE
    #     FOR
    #     CONTA
    #     40
    #     675
    #     366/0002-66
    #     RI
    #     SERVICOS
    #     DE
    #     ENTREGA
    #     E
    #     LOGISTICA
    #     LTDA
    #     I-DESTINATARIO
    #     ENDEREÇO
    #     MUNICIPIO
    #     UF
    #     INSCRIÇÃO
    #     ESTADUAL
    #     AV
    #     PRESIDENTE
    #     WILSON
    #     SAO
    #     PAULO
    #     SP
    #     131542250119
    #     QUANTIDADE
    #     ESPECIE
    #     MARCA
    #     NUMERAÇÃO
    #     PESO
    #     BRUTO
    #     PESO
    #     LIQUIDO
    #     VOLUME
    #     3,000
    #     3,000
    #     DADOS
    #     DO
    #     PRODU
    #     COD.
    #     PROD
    #     DESCRIÇÃO
    #     DO
    #     PROD/SERV.
    #     CFOP
    #     QUANT
    #     V.UNITARIO
    #     V.TOTAL
    #     BC.ICMS
    #     V.ICMS
    #     V.IPI
    #     A.ICMS
    #     A.IPI
    #     NCM/SH
    #     CST
    #     UN
    #     10003
    #     WHEY
    #     PROTEIN
    #     CONCENTRADO
    #     80%
    #     IKG
    #     CHOCOLATE
    #     21061000
    #     500
    #     6107
    #     UN
    #     2,0000
    #     138,770000
    #     277,54
    #     239,73
    #     28,77
    #     0,00
    #     12.00%
    #     0.00%
    #     10004
    #     PASTA
    #     AMENDOIM
    #     IKG
    #     20081100
    #     000
    #     6107
    #     UN
    #     1,0000
    #     31,000000
    #     31,00
    #     26,78
    #     3,21
    #     0,00
    #     12.00%
    #     0.00%
    #     LCULO
    #     DO
    #     ISSON
    #     SCRIÇÃO
    #     MUNICIPAL
    #     VALOR
    #     TOTAL
    #     DOS
    #     SERVIÇOS
    #     BASE
    #     DE
    #     CÁLCULO
    #     DO
    #     ISSQN
    #     VALOR
    #     DO
    #     ISSQN
    #     os
    #     ADICIONAIS
    #     RMAÇÕES
    #     COMPLEMENTARES
    #     RESERV
    #     ADO
    #     AO
    #     FISCO
    #     colo
    #     242250391243919
    #     do
    #     ICMS
    #     relativo
    #     ao
    #     Fundo
    #     de
    #     Combate
    #     a
    #     Pobreza
    #     FCP
    #     da
    #     UF
    #     de
    #     destino
    #     RS
    #     or
    #     do
    #     ICMS
    #     Interestadual
    #     para
    #     a
    #     UF
    #     de
    #     destino:
    #     RS
    #     15.99
    #     Valor
    #     do
    #     ICMS
    # """
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
        categoria=product.categoria,
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
    # colher de chá, comente daqui ate
    bedrock_response = await bedrock_client.invoke_model(
        modelId=Settings().CLOUDE_INFERENCE_PROFILE,
        body=dumps(get_bedrock_prompt(document_db.extract_result))
    )

    body_brute = await bedrock_response['body'].read()
    response_body:dict = loads(body_brute)
    response_ai_json = loads(response_body['content'][0]['text'])
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
    product_name = ''
    # capacity = ''
    # capacity_measureme = ''
    individual_quantity = 1
    product_type = ''
    # product_brand = ''
    quantidade_entrada = 1
    # size = ""
    custo_und = 0.0
    
    
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
    if response_ai_json['custo_und']:
        custo_und = response_ai_json['custo_und']



    informations_values ={
        "document_id": document_db.id,
        "nome": product_name,
        "custo_und": custo_und,
        "quantidade": quantidade_entrada,
        "categoria": product_type, 
    }
    
    document_db.ai_result = str(informations_values)
    breakpoint()
    await session.commit()

    return informations_values
    