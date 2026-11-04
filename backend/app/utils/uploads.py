import io
import os
import uuid

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

from ..errors import ApiError

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_DIMENSION = 1600


def upload_root():
    folder = current_app.config["UPLOAD_FOLDER"]
    if not os.path.isabs(folder):
        folder = os.path.abspath(os.path.join(current_app.root_path, "..", folder))
    return folder


def resolve_path(relative_path):
    root = os.path.realpath(upload_root())
    full = os.path.realpath(os.path.join(root, relative_path))
    if os.path.commonpath([root, full]) != root:
        raise ApiError("Invalid file path", 400)
    return full


def save_image(file_storage, subfolder):
    if file_storage is None or not file_storage.filename:
        raise ApiError("No file uploaded", 400)
    extension = os.path.splitext(file_storage.filename)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ApiError("Only JPG, PNG or WEBP images are allowed", 400)

    data = file_storage.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        raise ApiError("Image must be 5 MB or smaller", 400)

    try:
        probe = Image.open(io.BytesIO(data))
        image_format = probe.format
        probe.verify()
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError):
        raise ApiError("File is not a valid image", 400)
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ApiError("Only JPG, PNG or WEBP images are allowed", 400)

    image = ImageOps.exif_transpose(image)
    image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
    if image.mode in ("RGBA", "LA", "P"):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        image = background
    else:
        image = image.convert("RGB")

    filename = f"{uuid.uuid4().hex}.jpg"
    folder = os.path.join(upload_root(), subfolder)
    os.makedirs(folder, exist_ok=True)
    image.save(os.path.join(folder, filename), "JPEG", quality=85, optimize=True)
    return f"{subfolder}/{filename}"


def delete_file(relative_path):
    if not relative_path:
        return
    try:
        os.remove(resolve_path(relative_path))
    except (FileNotFoundError, ApiError):
        pass
