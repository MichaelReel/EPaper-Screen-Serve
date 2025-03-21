#!/usr/bin/python
from dataclasses import dataclass
from datetime import datetime
from flask import Flask, request, Response, render_template, redirect, url_for
from pathlib import Path
from PIL import Image, ImagePalette
import time

SCREEN_AVAILABLE: bool = False
# TODO: Maybe put this onto the index page:
POWER_ON_TOP: bool = True
try:
    from lib.waveshare_epd import epd4in0e
    SCREEN_AVAILABLE = True
except OSError as ose:
    print(f"OSError \"{ose}\" while trying to initialise E-ink Screen")

PALETTE_SEQUENCE = [
    0x00, 0x00, 0x00,
    0xff, 0xff, 0xff,
    0xff, 0xff, 0x00,
    0x00, 0x00, 0xff,
    0xff, 0x00, 0x00,
    0x00, 0xff, 0x00,
]
PALETTE: ImagePalette = ImagePalette.ImagePalette(
    mode="RGB", palette=PALETTE_SEQUENCE
)
TARGET_RESOLUTION: tuple[int, int] = (600, 400)
TARGET_ASPECT_RATIO: float = TARGET_RESOLUTION[0] / TARGET_RESOLUTION[1]
ALPHA_REPLACE_COLOR: tuple[int, int, int] = (0xFF, 0xFF, 0xFF)

UPLOADS_DIR: str = "static/uploads"
DELETE_DIR: str = "static/deletes"
FILE_TYPE: str = ".bmp"
FORM_FILE: str = "index.html"


@dataclass
class UploadedImage:
    name: str
    location: str


app = Flask(__name__)


@app.route("/")
def index():
    return render_template(FORM_FILE, upload_images=get_uploaded_images())


def get_uploaded_images() -> list[UploadedImage]:
    # Get contents of uploads
    uploads_path: Path = Path(UPLOADS_DIR)
    return [
        UploadedImage(
            name=str(location).split("/")[-1].split(".")[0],
            location=str(location)
        )
        for location in list(uploads_path.rglob(f"*{FILE_TYPE}"))
    ]


# TODO: Find a way to accept larger images files so we dont' get 413
@app.route("/im_submit", methods=["POST"])
def process_image() -> Response:
    file = request.files["image"]

    if not file:
        print("No file submitted")
        return redirect(url_for('index'))

    upload_image: Image = Image.open(file.stream)

    aspect_ratio: float = upload_image.width / upload_image.height

    cropped_image: Image
    if upload_image.width == TARGET_RESOLUTION[0] and upload_image.height == TARGET_RESOLUTION[1]:
        # Don't need to resize this image
        cropped_image = upload_image

    elif aspect_ratio > TARGET_ASPECT_RATIO:
        # Uploaded file is too wide, scale to height and crop the sides
        scale: float = TARGET_RESOLUTION[1] / upload_image.height
        scaled_image = upload_image.resize((int(upload_image.width * scale), TARGET_RESOLUTION[1]), Image.Resampling.LANCZOS)

        left_pad: int = (scaled_image.width - TARGET_RESOLUTION[0]) // 2
        cropped_image = scaled_image.crop((left_pad, 0, left_pad + TARGET_RESOLUTION[0], TARGET_RESOLUTION[1]))

    elif aspect_ratio < TARGET_ASPECT_RATIO:
        # Upload file is too tall, scale to width and crop top and bottom
        scale: float = TARGET_RESOLUTION[0] / upload_image.width
        scaled_image = upload_image.resize((TARGET_RESOLUTION[0], int(upload_image.height * scale)), Image.Resampling.LANCZOS)

        top_pad: int = (scaled_image.height - TARGET_RESOLUTION[1]) // 2
        cropped_image = scaled_image.crop((0, top_pad, TARGET_RESOLUTION[0], top_pad + TARGET_RESOLUTION[1]))

    else:
        # Aspect ratio to spot on, just need to scale
        cropped_image = upload_image.resize((TARGET_RESOLUTION[0], TARGET_RESOLUTION[1]), Image.Resampling.LANCZOS)

    palette_image: Image = Image.new("P", (1, 6))
    palette_image.putpalette(PALETTE_SEQUENCE)

    if cropped_image.mode == "RGBA":
        # Convert images with alpha channel to flat RGB before quantize
        cropped_image.load()  # needed for split()
        background = Image.new(mode='RGB', size=cropped_image.size, color=ALPHA_REPLACE_COLOR)
        background.paste(cropped_image, mask=cropped_image.split()[3])  # 3 is the alpha channel
        cropped_image = background

    store_image: Image = cropped_image.quantize(colors=len(PALETTE_SEQUENCE) // 3, palette=palette_image)

    timestamp: str = datetime.now().strftime("%y%m%d_%H%M%S")
    store_image.save(f"{UPLOADS_DIR}/{timestamp}{FILE_TYPE}")

    return redirect(url_for('index'))


@app.route("/im_delete", methods=["POST"])
def delete_image() -> Response:

    file_name: str = request.form["file"] + FILE_TYPE
    src_file: Path = Path(f"{UPLOADS_DIR}/{file_name}")
    dst_file: Path = Path(f"{DELETE_DIR}/{file_name}")
    src_file.rename(dst_file)

    return redirect(url_for('index'))


@app.route("/im_clear", methods=["GET"])
def clear_image() -> Response:
    if SCREEN_AVAILABLE:
        try:
            epd = epd4in0e.EPD()
            epd.init()
            epd.Clear()
            epd.sleep()
        except Exception as exc:
            print(f"Issue \"{exc}\" occurred trying to clear screen")
    else:
        print("Skipping clear as screen not initialised")
        time.sleep(2) # Simulate the delayed response due to E-Ink time

    return redirect(url_for('index'))


@app.route("/im_display", methods=["POST"])
def display_image() -> Response:
    file_name: str = UPLOADS_DIR + "/" + request.form["file"] + FILE_TYPE
    file: Path = Path(file_name)

    if not file.is_file():
        print(f"Selected file for display doesn't exist: {file_name}")
        return redirect(url_for('index'))

    if SCREEN_AVAILABLE:
        try:
            epd = epd4in0e.EPD()
            epd.init()

            # read bmp file 
            image: Image = Image.open(file)

            if POWER_ON_TOP:
                image = image.transpose(Image.ROTATE_180)

            epd.display(epd.getbuffer(image))
            time.sleep(3)

            epd.sleep()

        except Exception as exc:
            print(f"Issue \"{exc}\" occurred trying to display {file_name}")
    else:
        print(f"Skipping display of {file_name} as screen not initialised")
        time.sleep(2) # Simulate the delayed response due to E-Ink time

    return redirect(url_for('index'))


if __name__ == "__main__":
    try:
        app.run(host="127.0.0.1", port=8080)
    finally:
        if SCREEN_AVAILABLE:
            epd4in0e.epdconfig.module_exit(cleanup=True)
