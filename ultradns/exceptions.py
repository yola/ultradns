class DNSError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ZoneAlreadyExistsError(DNSError):
    pass


class ZoneNotFoundError(DNSError):
    pass


class AuthenticationError(DNSError):
    pass


class PermissionDeniedError(DNSError):
    pass


class RecordAlreadyExistsError(DNSError):
    pass


class RecordNotFoundError(DNSError):
    pass


class RecordsNotFoundError(DNSError):
    pass


class HTTPLevelError(DNSError):
    pass


class TransactionError(Exception):
    def __init__(self, errors=[]):
        self.errors = errors

    def __str__(self):
        return ', '.join(self.errors)


class NoActiveTransactionError(TransactionError):
    pass


class TransactionAlreadyInProgressError(TransactionError):
    pass


class EmptyTransactionError(TransactionError):
    pass


class GetInsideTransactionError(TransactionError):
    pass
