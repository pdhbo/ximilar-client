def pytest_addoption(parser):
    parser.addoption(
        "--token", action="store", default="test", help="token to test the api"
    )
