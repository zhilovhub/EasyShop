import os
import datetime
import secrets
from starlette.status import HTTP_401_UNAUTHORIZED

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from api.files.router import router as files_router
from api.orders.router import router as order_router
from api.products.router import router as product_router
from api.settings.router import router as settings_router
from api.categories.router import router as category_router

from common_utils.config import common_settings, api_settings

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

security = HTTPBasic()

_app_title = "FastApi"
_app_version = "0.1.2"
_root_prefix = "/api"

app = FastAPI(
    title=_app_title,
    version=_app_version,
    openapi_tags=tags_metadata,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(settings_router, prefix=_root_prefix)
app.include_router(order_router, prefix=_root_prefix)
app.include_router(category_router, prefix=_root_prefix)
app.include_router(product_router, prefix=_root_prefix)
app.include_router(files_router, prefix=_root_prefix)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    for developer in api_settings.DEVELOPERS:
        correct_username = secrets.compare_digest(credentials.username, developer[0])
        correct_password = secrets.compare_digest(credentials.password, developer[1])
        if correct_username and correct_password:
            break
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get(f"{_root_prefix}/docs", include_in_schema=False, dependencies=[Depends(_get_current_username)])
async def get_swagger_documentation():
    return get_swagger_ui_html(openapi_url=f"{_root_prefix}/openapi.json", title="docs")


@app.get(f"{_root_prefix}/openapi.json", include_in_schema=False, dependencies=[Depends(_get_current_username)])
async def get_open_api():
    return get_openapi(title=_app_title, version=_app_version, routes=app.routes)


if __name__ == "__main__":
    import uvicorn

    try:
        os.mkdir(common_settings.LOGS_PATH)
    except Exception as e:  # noqa
        pass

    for log_file in ("all.log", "err.log"):
        with open(common_settings.LOGS_PATH + log_file, "a") as log:
            log.write(
                f"=============================\n"
                f"New api session\n"
                f"[{datetime.datetime.now()}]\n"
                f"=============================\n"
            )

    if api_settings.API_PROTOCOL == "http":
        uvicorn.run(
            "api.main:app",
            host=api_settings.API_HOST,
            port=api_settings.API_PORT,
            log_level="info",
            uds=api_settings.UDS_PATH,
            log_config=logger_configuration,
        )
    elif api_settings.API_PROTOCOL == "https":
        uvicorn.run(
            "api.main:app",
            host=api_settings.API_HOST,
            port=api_settings.API_PORT,
            log_level="info",
            uds=api_settings.UDS_PATH,
            ssl_keyfile=api_settings.SSL_KEY_PATH,
            ssl_certfile=api_settings.SSL_CERT_PATH,
            log_config=logger_configuration,
        )

# Start uvicorn from cli (no logs)
if __name__ == "api.main":
    import api.products  # noqa
    import api.orders  # noqa
    import api.files  # noqa
