from fastapi import HTTPException, APIRouter
from fastapi.responses import FileResponse

from common_utils.env_config import FILES_PATH

from logs.config import api_logger

PATH = "/files"
router = APIRouter(
    prefix=PATH,
    tags=["files"],
    responses={404: {"description": "File not found"}},
)


@router.get("/{file_name}")
async def get_file(file_name: str) -> FileResponse:
    try:
        with open(FILES_PATH + file_name, 'rb'):
            pass
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="provided file name not found")
    except Exception:
        api_logger.error(
            "Error while execute get_file"
        )
        raise HTTPException(status_code=500, detail="Internal error.")
    return FileResponse(path=FILES_PATH + file_name, status_code=200)
