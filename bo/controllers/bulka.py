from bo import *


class ApiCallHandler(handler.ApiCallHandler):
    def CheckIsAdmin(self):
        return False


def main():
    Route([
        ('.*', ApiCallHandler)
    ])


if __name__ == '__main__':
    main()