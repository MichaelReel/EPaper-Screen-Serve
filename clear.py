#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
from lib.waveshare_epd import epd4in0e

logging.basicConfig(level=logging.DEBUG)

try:
    logging.info("Clearing Demo")

    epd = epd4in0e.EPD()
    logging.info("init and Clear")
    epd.init()
    epd.Clear()
    
    logging.info("Goto Sleep...")
    epd.sleep()
        
except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    epd4in0e.epdconfig.module_exit(cleanup=True)
    exit()
