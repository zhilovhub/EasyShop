import os

from ..main import db_engine, app, logger
from fastapi import HTTPException
from pydantic import ValidationError
from fastapi.responses import FileResponse

from dotenv import load_dotenv

from urllib.parse import unquote


load_dotenv()
PATH = "/files/"
FILES_ROOT = os.getenv("FILES_PATH")


@app.get(PATH + "{file_name}", tags=['files'])
async def get_file(file_name: str) -> FileResponse:
    file_name = unquote(file_name)
    try:
        with open(FILES_ROOT + file_name) as file:
            pass
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="provided file name not found")
    return FileResponse(path=FILES_ROOT + file_name, status_code=200)
