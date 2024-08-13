from fastapi import UploadFile

from magic import from_buffer
from mimetypes import guess_extension

from api.utils import HTTPUnacceptedError


ACCEPTED_PHOTO_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
)


async def detect_fastapi_file_mime_type(file: UploadFile) -> str:
    file_bytes = await file.read()
    await file.seek(0)
    file_type = from_buffer(file_bytes, mime=True)
    return file_type


async def get_bytes_file_extension(file_bytes: str | bytes) -> str | None:
    mime = from_buffer(file_bytes, mime=True)
    file_ext = guess_extension(mime, strict=False)
    return file_ext


async def get_fastapi_file_extension(file: UploadFile) -> str:
    mime = await detect_fastapi_file_mime_type(file)
    file_ext = guess_extension(mime, strict=False)
    if not file_ext:
        raise HTTPUnacceptedError(file_name=file.filename, header_content_type=file.content_type)
    return file_ext
