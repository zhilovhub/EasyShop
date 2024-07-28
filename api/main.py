import os
import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.files.router import router as files_router
from api.orders.router import router as order_router
from api.products.router import router as product_router
from api.settings.router import router as settings_router
from api.categories.router import router as category_router

from common_utils.env_config import LOGS_PATH, API_PROTOCOL, API_HOST, SSL_KEY_PATH, SSL_CERT_PATH, API_PORT, UDS_PATH

from logs.config import logger_configuration

tags_metadata = [
    {
        "name": "products",
        "description": "Operations with products.",
    },
    {
        "name": "categories",
        "description": "Operations with product categories.",
    },
    {
        "name": "orders",
        "description": "Operations with orders.",
    },
    {
        "name": "files",
        "description": "Operations with project files.",
    },
    {
        "name": "settings",
        "description": "Operations with bot user settings.",
    },
]
app = FastAPI(openapi_tags=tags_metadata)
app.include_router(settings_router)
app.include_router(order_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(files_router)

ROOT_PATH = "/api/"

origins = ["*"]
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{ROOT_PATH}")
async def read_root():
    return "You can see all available methods in rest api docs"


if __name__ == "__main__":
    import uvicorn

    try:
        os.mkdir(LOGS_PATH)
    except Exception as e:  # noqa
        pass

    for log_file in ('all.log', 'err.log'):
        with open(LOGS_PATH + log_file, 'a') as log:
            log.write(f'=============================\n'
                      f'New api session\n'
                      f'[{datetime.datetime.now()}]\n'
                      f'=============================\n')

    if API_PROTOCOL == "http":
        uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, log_level="info", uds=UDS_PATH,
                    log_config=logger_configuration)
    elif API_PROTOCOL == "https":
        uvicorn.run("api.main:app", host=API_HOST, port=API_PORT, log_level="info", uds=UDS_PATH,
                    ssl_keyfile=SSL_KEY_PATH, ssl_certfile=SSL_CERT_PATH,
                    log_config=logger_configuration)

# Start uvicorn from cli (no logs)
if __name__ == "api.main":
    import api.products  # noqa
    import api.orders  # noqa
    import api.files  # noqa
