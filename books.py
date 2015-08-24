# -*- coding: utf-8 -*-

__author__ = 'Nicolas Briche'
__license__ = 'GPL v3'
__docformat__ = 'restructuredtext en'

import logging
import os
import sqlite3
from contextlib import closing

from calibre.devices.usbms.books import Book
from calibre.ebooks.metadata import author_to_author_sort
from calibre.library import db
from calibre.utils.config import prefs


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class BookeenDatabase(object):
    def __init__(self, path_main, path_card=None, update_field=None):
        logging.debug("init db")

        self.databases = {'main': {'uuid': '', 'path': path_main, 'prefix_fs': '/mnt/fat/', 'books': {}}, 'carda': {'uuid': '', 'path': path_card, 'prefix_fs': '/mnt/sd/', 'books': {}}}
        self.collections = {}
        self.shelves_links = {}
        self.books = {}
        self.can_set_as_read = False
        self.to_close = []
        self.to_set_as_read = []
        self.set_as_read_field = None

        self.init_db('main')
        if self.databases['carda']['path']:
            self.init_db('carda')

        if update_field is not None:
            calibre_db = db(prefs['library_path']).new_api
            if update_field and update_field in calibre_db.fields.keys():
                logging.debug("We can update the 'read' field")
                self.can_set_as_read = True
                self.set_as_read_field = update_field

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

                book = BookeenBook('', book_row['f_internal_uri'][len(self.databases[database]['prefix_fs']):], book_row['f_title'], finished=finished, current_page=book_row['f_current_page'])
                if book_row['f_id_item'] in self.shelves_links.keys():
                    self.collections[self.shelves_links[book_row['f_id_item']][0]].add_book(book)

                self.books[(self.databases[database]['uuid'], book_row['f_id_item'])] = book
                self.databases[database]['books'][book_row['f_id_item']] = book

            logging.debug("Found {} books on {}".format(len(self.books), database))

    def match(self, oncard, calibre_books, threshold=0):
        # ['#pages', '#cleaned', 'rights', 'author_sort', 'author_link_map', 'publisher', 'db_id', 'device_collections', '#onmuse', 'authors', 'languages', '#words', 'uuid', 'rating', 'tags', '#list_remove_orizon', 'cover', 'toc', 'user_metadata', '#author_sort', '#list_orizon', '#read', 'publication_type', 'series_index', 'size', 'series', 'last_modified', '#maj_late', 'identifiers', '#isbn', '#goodreads', '#list_remove_muse', '#onorizon', 'comments', 'title_sort', '#list_muse', 'author_sort_map', 'guide', 'thumbnail', 'formats', 'lpath', 'timestamp', 'pubdate', 'book_producer', 'user_categories', 'spine', 'mime', '#progression', '#chapters', 'cover_data', '#updated', 'title', 'application_id', 'manifest']

        to_close = []
        to_set_as_read = []

        if oncard is None:
            oncard = 'main'
        elif oncard != 'carda':
            logging.debug("No database for '{}'".format(oncard))
            raise BookeenDatabaseException(oncard)

        logging.debug("Matching books for {}...".format(oncard))

        for device_book_id, device_book in self.databases[oncard]['books'].items():
            assert isinstance(device_book, BookeenBook)
            found = False
            for idx, calibre_book in enumerate(calibre_books):
                if device_book.lpath == calibre_book.lpath:
                    # logging.debug("Found : {} -> {}::{} ({} / {})".format(calibre_book.uuid, self.databases[oncard]['uuid'], book_id, calibre_book.title, device_book.title))
                    found = True
                    # calibre_books[idx].bookeen_id = (self.databases[oncard]['uuid'], device_book_id)
                    if device_book.finished:
                        to_set_as_read.append(calibre_book.application_id)

            if not found:
                logging.debug("{} ({}) wasn't found in Calibre".format(device_book.title, device_book.lpath))

            if threshold > 0:
                # logging.debug("Current page is {}, threshold is {} for {}".format(device_book.current_page, threshold, device_book))
                if 0 <= device_book.current_page <= threshold:
                    to_close.append((self.databases[oncard]['uuid'], device_book_id))

        return to_close, to_set_as_read

    def close_book(self, book_id):

        uuid, bookid = book_id

        # logging.debug("closing book {}".format(book_id))

        with closing(sqlite3.connect(self.get_database_path(uuid))) as connection:
            # logging.debug("connect to db")
            # connection.row_factory = dict_factory
            # cursor = connection.cursor()
            # cursor.execute('UPDATE T_ITEM SET f_current_page = -1, f_last_read = NULL WHERE f_id_item = {}'.format(bookid))
            # connection.commit()
            logging.debug("Closed {} ({})".format(book_id, self.books[book_id]))

    def get_database_path(self, uuid):
        for database in self.databases.values():
            if uuid == database['uuid']:
                return database['path']

    def set_as_read(self, book_ids):
        affected_books = []
        if self.can_set_as_read:
            logging.debug("Updating books: {}".format(book_ids))
            calibre_db = db(prefs['library_path']).new_api
            affected_books = calibre_db.set_field(self.set_as_read_field, {book_id: True for book_id in book_ids})
            logging.debug("Affected books: {}".format(affected_books))
        else:
            logging.debug("Can't update books")
        return affected_books


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


class BookeenBook(Book):
    def __init__(self, prefix, lpath, title=None, authors=None, date=None, finished=False, current_page=None, size=None, other=None):

        Book.__init__(self, prefix, lpath, size, other)

        self.current_page = current_page
        self.finished = finished
        self.bookeen_id = None

        self.size = size
        if title is not None and len(title) > 0:
            self.title = title
        else:
            self.title = "(No title)"

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
        return "{}: {} - {}{} - {}".format(self.uuid, self.title, self.current_page if self.current_page > 0 else "Not opened", " - Finished" if self.finished else "", self.lpath)


class BookeenDatabaseException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "{} has no database".format(self.value)
