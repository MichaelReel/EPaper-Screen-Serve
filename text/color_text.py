import os
import logging
import random
from lib.waveshare_epd import epd4in0e
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.DEBUG)

class ColorText:
    picdir: str = "pic"
    epd: epd4in0e.EPD
    font64: ImageFont
    font192: ImageFont

    def setup(self) -> None:
        logging.info("setup")

        self.font64 = ImageFont.truetype(os.path.join(self.picdir, 'Font.ttc'), 64)
        self.font192 = ImageFont.truetype(os.path.join(self.picdir, "Font.ttc"), 192)

        self.epd = epd4in0e.EPD()

    def draw_status(self, msg: str) -> None:
        try:
            logging.info("init & clear")
            self.epd.init()
            self.epd.Clear()

            # Drawing on the image
            logging.info("Drawing the landscape image...")

            # Create rotated (landscape) image first
            rot_image: Image = Image.new('RGB', (self.epd.height, self.epd.width), self.epd.WHITE)
            draw: ImageDraw = ImageDraw.Draw(rot_image)

            color_list: list = [
                self.epd.BLACK,
                self.epd.BLUE,
                self.epd.YELLOW,
                self.epd.RED,
                self.epd.WHITE,
                self.epd.GREEN,
            ]
            random.shuffle(color_list)

            block_width: int = self.epd.height // 3
            block_height: int = self.epd.width // 2

            for col in [0, 1, 2]:
                for row in [0, 1]:
                    x: int = block_width * col
                    y: int = block_height * row
                    color: int = color_list.pop()
                    draw.rectangle((x, y, x + block_width, y + block_height), fill = color)

            self.draw_outlined_text(
                draw=draw,
                pos=(50, 8),
                msg=msg,
                font=self.font64,
                inside_color=self.epd.BLACK,
                outline_color=self.epd.WHITE,
                outline_width=3,
            )

            self.epd.display(self.epd.getbuffer(rot_image))

            logging.info("Goto Sleep...")
            self.epd.sleep()

        except IOError as e:
            logging.info(e)

    def draw_outlined_text(
        self,
        draw: ImageDraw,
        pos: tuple[int, int],
        msg: str,
        font: ImageFont,
        inside_color: int,
        outline_color: int,
        outline_width: int,
    ) -> None:
        x_diff: int
        y_diff: int
        for x_diff in [pos[0] - outline_width, pos[0] + outline_width]:
            for y_diff in [pos[1] - outline_width, pos[1] + outline_width]:
                draw.text((x_diff, y_diff), msg, font=font, fill=outline_color)

        draw.text(pos, msg, font=font, fill=inside_color)
