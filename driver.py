# -*- coding: utf-8 -*-

__author__ = 'Nicolas Briche'
__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'

"""
Device driver for Bookeen's Cybook Odyssey/Muse/Ocean (extended functionality)
"""

class MUSE_EX(USBMS):
    name = 'Cybook Muse Ex Device Interface'
    gui_name = 'Muse Ex'
    description = _('Communicate with the Cybook Odyssey / Muse / Ocean eBook reader.')
    author = 'Nicolas Briche'

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
    ]
    EXTRA_CUSTOMIZATION_DEFAULT = [EBOOK_DIR_CARD_A]

    SCAN_FROM_ROOT = False

