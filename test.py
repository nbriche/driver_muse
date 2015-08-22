# -*- coding: utf-8 -*-

__author__ = 'Aleyx'

import logging
import os
from calibre.ebooks.metadata import title_sort
from calibre.devices.usbms.books import Book as _Book
from calibre.devices.usbms.books import BookList
from calibre.devices.usbms.books import CollectionsBookList
import sqlite3
from contextlib import closing
from calibre.ebooks.metadata import author_to_author_sort

logging.basicConfig(level=logging.DEBUG)


def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d


class BookeenDatabase(object):
	def __init__(self, path_main, path_card=None):
		logging.debug("init db")

		self.databases = {'main': {'uuid': '', 'path': path_main}, 'card': {'uuid': '', 'path': path_card}}
		self.collections = {}
		self.shelves_links = {}
		self.books = {}

		self.init_db('main')
		if self.databases['card']['path']:
			self.init_db('card')

	def init_db(self, database):

		self.databases[database]['uuid'] = ''

		with closing(sqlite3.connect(self.databases[database]['path'])) as connection:
			logging.debug("connect to db")
			connection.row_factory = dict_factory
			cursor = connection.cursor()
			cursor.execute('SELECT f_db_uuid FROM T_UUIDDB')
			self.databases[database]['uuid'] = cursor.fetchone()['f_db_uuid']
			logging.debug("dbuuid: {}".format(self.databases[database]['uuid']))
			if database == 'main':
				logging.debug("this is the main db")

				cursor.execute('SELECT * FROM T_SHELF')
				for shelf in cursor.fetchall():
					self.collections[shelf['f_id_shelf']] = BookeenShelf(shelf)

				cursor.execute('SELECT * FROM T_SHELF_LINK')
				for link in cursor.fetchall():
					self.shelves_links[link['f_item_id']] = (link['f_shelf_id'], link['f_db_uuid'])

			logging.debug("finding books")
			cursor.execute('SELECT * FROM T_ITEM WHERE f_item_filetype=2')
			for book_row in cursor.fetchall():
				finished = True if book_row['f_islastpage'] else False

				book = Book('', '', book_row['f_title'], finished=finished, current_page=book_row['f_current_page'])
				if book_row['f_id_item'] in self.shelves_links.keys():
					self.collections[self.shelves_links[book_row['f_id_item']][0]].add_book(book)

				self.books[(self.databases[database]['uuid'], book_row['f_id_item'])] = book

	def close_book(self, book_id):

		uuid, bookid = book_id

		with closing(sqlite3.connect(self.get_database_path(uuid))) as connection:
			logging.debug("connect to db")
			connection.row_factory = dict_factory
			cursor = connection.cursor()
			cursor.execute('UPDATE T_ITEM SET f_current_page = -1, f_last_read = NULL WHERE f_id_item = {}'.format(bookid))
			connection.commit()
			print "Closed {} ({})".format(book_id, self.books[book_id])

	def get_database_path(self, uuid):
		for database in self.databases.values():
			if uuid == database['uuid']:
				return database['path']

class Descriptions(object):
	filetype = {
		1: "Directory",
		2: "File"
	}

	fileformat = {
		0: "Directory",
		1: "EPUB",
		3: "JPEG"
	}


class BookeenShelf(object):
	def __init__(self, data):
		self.name = data['f_name']
		self.id = data['f_id_shelf']
		self.readonly = True if data['f_readonly'] == 1 else False
		self.books = []
		logging.debug("init'ed shelf {}".format(self.id))

	def __str__(self):
		return "{} -  {} ({})".format(self.name, self.id, [book.title for book in self.books])

	def add_book(self, book):
		self.books.append(book)

	def get_books(self):
		return self.books


class Book(_Book):
	def __init__(self, prefix, lpath, title=None, authors=None, date=None, finished=False, current_page=None, size=None, other=None):

		_Book.__init__(self, prefix, lpath, size, other)

		self.current_page = current_page
		self.finished = finished

		assert isinstance(size, int)
		self.size = size
		if title is not None and len(title) > 0:
			self.title = title
		else:
			self.title = "No title"

		if authors is not None and len(authors) > 0:
			self.authors_from_string(authors)
			if self.author_sort is None or self.author_sort == "Unknown":
				self.author_sort = author_to_author_sort(authors)

		self.date = date
		self._new_book = False
		self.device_collections = []
		self.path = os.path.join(prefix, lpath)
		if os.sep == '\\':
			self.path = self.path.replace('/', '\\')
			self.lpath = lpath.replace('\\', '/')
		else:
			self.lpath = lpath

	def __str__(self):
		return "{} - {}{}".format(self.title, self.current_page if self.current_page > 0 else "Not opened", " - Finished" if self.finished else "")

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description='Manage Muse.')
	parser.add_argument("--main", default='library.main.sqlite')
	parser.add_argument("--card")
	parser.add_argument("--to_close", type=int)
	args = parser.parse_args()
	print args.main, args.card

	db = BookeenDatabase(args.main, args.card)
	for c in db.collections.values():
		logging.debug(c)
		pass

	for b in db.books.values():
		logging.debug(b)
		pass

	if args.to_close:
		print "Books to close (limit set to {}):".format(args.to_close)
		for i, b in db.books.items():
			if not b.finished and 0 <= b.current_page <= args.to_close:
				db.close_book(i)
				#print "closing {}".format(i)
