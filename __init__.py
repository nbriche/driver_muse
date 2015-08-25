# -*- coding: utf-8 -*-

__author__ = 'Nicolas Briche'
__license__ = 'GPL v3'
__docformat__ = 'restructuredtext en'

"""
Device driver for Bookeen's Cybook Odyssey/Muse/Ocean (extended functionality)
"""
from calibre.devices.cybook.driver import MUSE
from calibre.devices.usbms.books import BookList
from books import BookeenDatabase, BookeenDatabaseException, BookeenBook

import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(relativeCreated)d MUSE_EX: %(message)s")


class MuseEx(MUSE):
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

    EXTRA_CUSTOMIZATION_MESSAGE = [
        _('Card A folder') + ':::<p>' +
        _('Enter the folder where the books are to be stored when sent to the '
          'memory card. This folder is prepended to any send to device template') + '</p>',
        _('"Read" custom field') + ':::<p>' +
        _('Select which field to update to \'Yes\' when a read book is detected.') + '</p>',
        _('Current page threshold for closing a book') + ':::<p>' +
        _('If you open a book, the device considers it as "currently reading", even if you only read the cover.  Calibre will close any book whose current page is under this field\'s value, and reset it to "New".  Set to 0 to disable.') + '</p>',

    ]
    EXTRA_CUSTOMIZATION_DEFAULT = [EBOOK_DIR_CARD_A, "", "0"]

    OPT_UPDATE_FIELD_READ = 1
    OPT_CLOSE_THRESHOLD = 2

    SCAN_FROM_ROOT = False

    bookeen_database = None
    can_set_as_read = False
    to_set_as_read = []
    set_as_read_fields = []

    def books(self, oncard=None, end_session=True):

        logging.debug("Reading {}".format(oncard))

        bl = super(MUSE, self).books(oncard, end_session)

        if self.bookeen_database is None:
            logging.debug("Looking for device databases")

            main_lib = "{}/system/library".format(self.driveinfo['main']['prefix'])
            carda_lib = None
            if 'A' in self.driveinfo.keys():
                carda_lib = "{}/system/library".format(self.driveinfo['A']['prefix'])

            logging.debug("device databases: {}, {}".format(main_lib, carda_lib))
            self.bookeen_database = BookeenDatabase(main_lib, carda_lib)

        try:
            to_close, self.to_set_as_read = self.bookeen_database.match(oncard, bl, int(self.settings().extra_customization[self.OPT_CLOSE_THRESHOLD]))

            if int(self.settings().extra_customization[self.OPT_CLOSE_THRESHOLD]) > 0:
                if to_close:
                    logging.debug("to close: {}".format(to_close))
                else:
                    logging.debug("Nothing to close")
            else:
                logging.debug("Threshold is zero: disabled closing books")
        except BookeenDatabaseException, e:
            logging.debug(e)

        return bl

    def synchronize_with_db(self, db, id_, book, first_call):
        changed = None

        if first_call:
            set_as_read_fields = list(set(self.settings().extra_customization[self.OPT_UPDATE_FIELD_READ]) & db.fields.keys())
            logging.debug("Calculated update fields: {}".format(set_as_read_fields))
            if set_as_read_fields:
                curated_fields = list(set(set_as_read_fields) & db().new_api.fields.keys())
                if set_as_read_fields and curated_fields:
                    self.can_set_as_read = True
                    self.set_as_read_fields = curated_fields
                    logging.debug("We can update the 'read' fields {}".format(curated_fields))
                else:
                    logging.debug("No valid field found.")

        if self.can_set_as_read:
            if self.to_set_as_read:
                if id_ in self.to_set_as_read:
                    logging.debug("Updating book: {}".format(id_))
                    for field in self.set_as_read_fields:
                        logging.debug("Set to read, field {}: {}".format(field, (id_, str(book))))
                        changed |= db.new_api.set_field(field, {id_: True})
                    logging.debug("Changed: {}".format(changed))
            elif first_call:
                logging.debug("Nothing to set as read")
        elif first_call:
            logging.debug("No target field: disabled set as read")

        return changed, (None, False)
