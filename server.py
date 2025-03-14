#!/usr/bin/python
from datetime import datetime
from flask import Flask, current_app, request, Response, jsonify
from PIL import Image, ImagePalette

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

UPLOADS_DIR: str = "uploads"
FORM_FILE: str = "index.html"

app = Flask(__name__)

@app.route("/")
def hello_world():
    # TODO: Will make a templare later
    return current_app.send_static_file(FORM_FILE)

@app.route("/im_submit", methods=["POST"])
def process_image() -> Response:
    file = request.files["image"]
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

    store_image: Image = cropped_image.quantize(colors=len(PALETTE_SEQUENCE) // 3, palette=palette_image)

    timestamp: str = datetime.now().strftime("%y%m%d_%H%M%S")
    store_image.save(f"{UPLOADS_DIR}/{timestamp}.bmp")

    return jsonify(
        {
            "msg": "success",
            "timestamp": timestamp,
            "size": [palette_image.width, palette_image.height],
        }
    )


# def get_ip():
#     from socket import socket
# 
#     socket_test: socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
#     socket_test.settimeout(0)
#     ip: str = "no network"
#     try:
#         socket_test.connect(("", 1))
#         ip = socket_test.getsockname()[0]
#     finally:
#         socket_test.close()
#     return ip


if __name__ == "__main__":
    from waitress import serve

    serve(app, port=8080)
