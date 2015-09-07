#! /usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import sys

LOG_LEVEL = logging.DEBUG

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)-8s %(threadName)s %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S')
# log.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(relativeCreated)d MUSE_EX: %(message)s")


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, handler, log_level=logging.INFO):
        self.logger = logging.getLogger(logger)
        self.log_level = log_level
        self.linebuf = ''
        self.logger.addHandler(handler)

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())


log = logging.getLogger('muse_ex')
log.setLevel(logging.DEBUG)

hdlr = logging.FileHandler("std_err_out.log", mode='a')
hdlr.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(threadName)s %(message)s'))

sys.stdout = StreamToLogger('STDOUT', hdlr, logging.INFO)
sys.stderr = StreamToLogger('STDERR', hdlr, logging.ERROR)
