class PGSheetsException(Exception):
    pass


class PGSheetsHTTPException(PGSheetsException):
    pass


class PGSheetsValueError(PGSheetsException):
    pass


def _check_status(r):
    if r.status_code // 100 != 2:
        raise PGSheetsHTTPException(
            "Bad HTTP response {}:\n{}"
            .format(r.status_code, r.content.decode())
            )
