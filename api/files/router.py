import os

from dotenv import load_dotenv

from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse

from logs.config import api_logger

load_dotenv()
PATH = "/files"
router = APIRouter(
    prefix=PATH,
    tags=["files"],
    responses={404: {"description": "File not found"}},
)
FILES_ROOT = os.getenv("FILES_PATH")


@router.get("/{file_name}")
async def get_file(file_name: str) -> FileResponse:
    try:
        with open(FILES_ROOT + file_name, 'rb'):
            pass
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="provided file name not found")
    except Exception as e:
        api_logger.error(
            "Error while execute get_file",
            exc_info=e
        )
        raise HTTPException(status_code=500, detail="Internal error.")
    return FileResponse(path=FILES_ROOT + file_name, status_code=200)
