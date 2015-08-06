# -*- coding: utf-8 -*-

'''
Device driver for Bookeen's Cybook Odyssey/Muse/Ocean (extended functionality) 
'''


from calibre.devices.cybook.driver import ORIZON

class MUSE_EX(ORIZON):
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


