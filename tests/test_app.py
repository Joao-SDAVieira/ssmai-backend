from http import HTTPStatus


def test_read_root_should_return_welcome_message(client):
    response = client.get("/")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "message": "Smart Stock management AI, "
        "Gerencie seu estoque de forma eficaz"
    }
