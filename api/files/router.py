from fastapi import APIRouter
from fastapi.responses import FileResponse

from api.utils import RESPONSES_DICT, HTTPFileNotFoundError, HTTPInternalError

from common_utils.env_config import FILES_PATH

from logs.config import api_logger

from PIL import Image

PATH = "/files"
router = APIRouter(
    prefix=PATH,
    tags=["files"],
    responses=RESPONSES_DICT,
)


def _get_file_thumbnail_path(file_path: str) -> str:
    ext = file_path.split('.')[-1]
    thumbnail_path = file_path.replace(f'.{ext}', f'_thumbnail.{ext}')
    return thumbnail_path


def _compress_file_to_thumbnail(file_path: str):
    base_width = 300
    img = Image.open(file_path)
    width_percent = (base_width / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(width_percent)))
    img = img.resize((base_width, hsize), Image.Resampling.LANCZOS)
    img.save(_get_file_thumbnail_path(file_path))


@router.get("/get_file/{file_name}")
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


# @router.get("/get_product_thumbnail/{product_id}")  TODO pictures for inline photos
# async def get_product_thumbnail(product_id: int) -> FileResponse:
#     try:
#         product = await product_db.get_product(product_id)
#     except ProductNotFoundError:
#         raise HTTPProductNotFound(product_id=product_id)
#
#     if not product.picture:
#         raise HTTPBadRequest(detail_message="product dont have photos")
#
#     file_name = product.picture[0]
#
#     file_ext = product.picture[0].split('.')[-1]
#     thumbnail_path = _get_file_thumbnail_path(FILES_PATH + file_name)
#
#     headers = {
#         "accept-ranges": "bytes",
#         "strict-transport-security": "max-age=63072000"
#     }
#
#     try:
#         with open(thumbnail_path, "rb"):
#             pass
#         return FileResponse(path=thumbnail_path, status_code=200, headers=headers)
#     except FileNotFoundError:
#         pass
#
#     try:
#         with open(FILES_PATH + file_name, 'rb'):
#             pass
#         _compress_file_to_thumbnail(FILES_PATH + file_name)
#     except FileNotFoundError:
#         raise HTTPFileNotFound(file_name=file_name)
#     except Exception as ex:
#         api_logger.error("error while formatting photo", exc_info=True)
#         raise ex
#
#     return FileResponse(path=thumbnail_path, status_code=200, headers=headers)
