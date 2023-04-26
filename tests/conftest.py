from unittest import mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.db import SessionTest
from app.main import app
from config import settings

# TODO: Import Base class for models


TEST_DB_NAME = ''
TEST_DB_URL = f'{settings.postgres_url}/{TEST_DB_NAME}'


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True, scope='session')
def create_db():
    engine = create_engine(settings.postgres_url)
    connection = engine.connect()
    connection.execution_options(isolation_level="AUTOCOMMIT")

    connection.execute(text(f'DROP DATABASE IF EXISTS {TEST_DB_NAME};'))
    connection.execute(text(f'CREATE DATABASE {TEST_DB_NAME};'))

    try:
        yield
    finally:
        connection.execute(text(f'DROP DATABASE {TEST_DB_NAME};'))
    connection.close()


@pytest.fixture(scope='session')
def engine():
    _engine = create_engine(TEST_DB_URL)

    with _engine.begin() as conn:
        Base.metadata.create_all(bind=conn)
    SessionTest.configure(bind=_engine)
    yield _engine
    with _engine.begin() as conn:
        Base.metadata.drop_all(bind=conn)
    _engine.dispose()


@pytest.fixture(scope='session')
def prepare_db(engine):
    # SessionTest.configure(bind=engine)
    yield


@pytest.fixture(autouse=True)
def db_session(prepare_db):
    ses = SessionTest()
    ses.begin_nested()
    with mock.patch.object(ses, 'commit'):
        with mock.patch.object(ses, 'rollback'):
            with mock.patch.object(ses, 'close'):
                yield ses
    ses.rollback()
    ses.close()
