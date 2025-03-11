#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
import os
import logging
from lib.waveshare_epd import epd4in0e
import time
from PIL import Image, ImageDraw, ImageFont
import traceback

logging.basicConfig(level=logging.DEBUG)

picdir: str = "pic"
bmpfile: str = "02.bmp"

try:
    logging.info("Starting Demo")

    epd = epd4in0e.EPD()   
    logging.info("init")
    epd.init()

    # read bmp file 
    logging.info("read bmp file")
    Himage = Image.open(os.path.join(picdir, bmpfile))
    epd.display(epd.getbuffer(Himage))
    time.sleep(3)
    
    logging.info("Goto Sleep...")
    epd.sleep()
        
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd4in0e.epdconfig.module_exit(cleanup=True)
    exit()
