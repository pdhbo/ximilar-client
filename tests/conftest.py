def pytest_addoption(parser):
    parser.addoption("--token", action="store", default="client", help="token to client the client")
