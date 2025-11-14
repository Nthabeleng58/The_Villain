
from app import app  # FIXED: your project does not use create_app()



def client():
    app.config['TESTING'] = True

    # Override DB settings for tests (no real DB connection)
    app.config['DB_HOST'] = 'localhost'
    app.config['DB_USER'] = ''
    app.config['DB_PASSWORD'] = ''
    app.config['DB_NAME'] = ':memory:'  # mock DB

    with app.test_client() as client:
        yield client


def test_index(client):
    """Test the home page loads correctly"""
    rv = client.get('/')
    assert rv.status_code in (200, 302)
