from http import HTTPStatus

from ssmai_backend.schemas.products_schemas import PublicProductSchema


def test_read_products(client):
    response = client.get("/products/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"products": []}


def test_read_products_with_product(client, product):
    user_schema = PublicProductSchema.model_validate(product).model_dump(
        mode="json"
    )

    response = client.get("/products/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"products": [user_schema]}
