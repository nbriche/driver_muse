# -*- coding: utf-8 -*-

__author__ = 'Nicolas Briche'
__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'

"""
Device driver for Bookeen's Cybook Odyssey/Muse/Ocean (extended functionality)
"""
from calibre import prints, isbytestring, fsync
from calibre.devices.cybook.driver import MUSE
from calibre.devices.usbms.books import BookList
from books import BookeenShelf
from books import BookeenDatabase
from books import BookeenBook
from calibre.library import db
from calibre.utils.config import prefs

# from calibre.devices.usbms.books import Book

import logging
import sqlite3
import time

from calibre.constants import filesystem_encoding, DEBUG

logging.basicConfig(level=logging.DEBUG)

BASE_TIME = None


def debug_print(*args):
    global BASE_TIME
    if BASE_TIME is None:
        BASE_TIME = time.time()
    if DEBUG:
        prints('DEBUG: %6.1f'%(time.time()-BASE_TIME), *args)


class MUSE_EX(MUSE):
    name = 'Cybook Muse Ex Device Interface'
    gui_name = 'Muse Ex'
    description = _('Communicate with the Cybook Odyssey / Muse / Ocean eBook reader.')
    author = 'Nicolas Briche'
    version = (0, 0, 3)

    booklist_class = BookList
    book_class = BookeenBook

    FORMATS = ['epub', 'html', 'fb2', 'txt', 'pdf', 'djvu']

    VENDOR_ID = [0x0525]
    PRODUCT_ID = [0xa4a5]
    BCD = [0x0230]

    VENDOR_NAME = 'USB_2.0'
    WINDOWS_MAIN_MEM = WINDOWS_CARD_A_MEM = 'USB_FLASH_DRIVER'

    EBOOK_DIR_MAIN = 'Digital Editions'
    EBOOK_DIR_CARD_A = 'Digital Editions'

    update_fields = {'closed': "#museclosed"}

    EXTRA_CUSTOMIZATION_MESSAGE = [
        _('Card A folder') + ':::<p>' +
        _('Enter the folder where the books are to be stored when sent to the '
          'memory card. This folder is prepended to any send to device template') + '</p>',
        _('"Read" custom field') + ':::<p>' +
        _('Select which field to update to \'Yes\' when a closed book is detected.') + '</p>',
    ]
    EXTRA_CUSTOMIZATION_DEFAULT = [EBOOK_DIR_CARD_A, update_fields['closed']]

    SCAN_FROM_ROOT = False

    bookeen_database = None



    def books(self, oncard=None, end_session=True):

        if self.bookeen_database is None:
            debug_print("MUSE_EX: Looking for device databases")

            main_lib = "{}/system/library".format(self.driveinfo['main']['prefix'])
            carda_lib = None
            if 'A' in self.driveinfo.keys():
                carda_lib = "{}/system/library".format(self.driveinfo['A']['prefix'])

            debug_print("MUSE_EX: device databases: ", main_lib, carda_lib)
            self.bookeen_database = BookeenDatabase(main_lib, carda_lib, self.update_fields)

        debug_print("MUSE_EX: reading {}".format(oncard))

        bl = super(MUSE, self).books(oncard, end_session)

        logging.debug("Matching books for {}...".format(oncard))
        self.bookeen_database.match(oncard, bl)

        return bl
