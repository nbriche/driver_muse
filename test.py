# -*- coding: utf-8 -*-

__author__ = 'Aleyx'

# from books import BookeenDatabase


class Test(object):
    def meth(self):
        def int_func(self):
            return "test_int"
        return 'Test_meth', int_func(self)


class Test2(Test):
    def meth(self):
        Test.meth(self)
        return 'Test2_meth'


test = Test2()
print test.meth()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Manage Muse.')
    parser.add_argument("--main", default='library.main.sqlite')
    parser.add_argument("--card")
    parser.add_argument("--to_close", type=int)
    args = parser.parse_args()
    # print args.main, args.card

    # db = BookeenDatabase(args.main, args.card)
    # for c in db.collections.values():
    #     logging.debug(c)
    #     pass
    #
    # for b in db.books.values():
    #     logging.debug(b)
    #     pass
    #
    # if args.to_close:
    #     print "Books to close (limit set to {}):".format(args.to_close)
    #     for i, b in db.books.items():
    #         if not b.finished and 0 <= b.current_page <= args.to_close:
    #             db.close_book(i)
    #         # print "closing {}".format(i)
