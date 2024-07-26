from fastapi import APIRouter
from fastapi.responses import FileResponse

from api.utils import RESPONSES_DICT, HTTPFileNotFoundError, HTTPInternalError

from common_utils.env_config import FILES_PATH

from logs.config import api_logger

PATH = "/files"
router = APIRouter(
    prefix=PATH,
    tags=["files"],
    responses=RESPONSES_DICT,
)


@router.get("/{file_name}")
async def get_file(file_name: str) -> FileResponse:
    """
    :param file_name: the name of the requiring file on server
    :return: File in bytes

    :raises HTTPFileNotFound:
    :raises HTTPInternalError:
    """
    try:
        with open(FILES_PATH + file_name, 'rb'):
            pass
    except FileNotFoundError:
        raise HTTPFileNotFoundError(file_name=file_name)
    except Exception as e:
        api_logger.error(
            "Error while execute get_file",
            exc_info=e
        )
        raise HTTPInternalError
    return FileResponse(path=FILES_PATH + file_name, status_code=200)
