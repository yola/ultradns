import requests
import json

from exceptions import (ZoneNotFoundError, ZoneAlreadyExistsError,
                        PermissionDeniedError, DNSError, TransactionError,
                        TransactionAlreadyInProgressError,
                        NoActiveTransactionError, EmptyTransactionError,
                        GetInsideTransactionError, RecordsNotFoundError,
                        RecordAlreadyExistsError, AuthenticationError)
from client_base import BaseDNSClient

ERR_CODE_AUTH_TOKEN_EXPIRED = 60001
ERR_CODE_ZONE_ALREADY_EXISTS = 1802
ERR_CODE_ZONE_NOT_FOUND = 1801
ERR_CODE_PERMISSION_DENIED = 8001
ERR_RECORDS_NOT_FOUND = 70002
ERR_RECORD_ALREADY_EXISTS = 2111
ERR_RECORD_NOT_FOUND = 56001

exceptions_map = {ERR_CODE_PERMISSION_DENIED: PermissionDeniedError,
                  ERR_CODE_ZONE_NOT_FOUND: ZoneNotFoundError,
                  ERR_CODE_ZONE_ALREADY_EXISTS: ZoneAlreadyExistsError,
                  ERR_RECORD_ALREADY_EXISTS: RecordAlreadyExistsError,
                  ERR_RECORDS_NOT_FOUND: RecordsNotFoundError,
                  ERR_RECORD_NOT_FOUND: RecordsNotFoundError}


class ErrorHandlingMixin(object):
    """Add errors handling functionality to the Restful API Client class."""
    def _is_error(self, response):
        return response.status_code >= requests.codes.BAD_REQUEST

    def _handle_error(self, response):
        """Handle REST errors and raise exceptions upwards."""
        json_body = response.json()
        error_code = None

        if isinstance(json_body, list):
            error_code = json_body[0]['errorCode']
            error_msg = json_body[0]['errorMessage']
        else:
            error_code = json_body['errorCode']
            error_msg = json_body['errorMessage']

        if error_code in exceptions_map:
            raise exceptions_map[error_code](error_msg)
        else:
            raise DNSError('%s: %s' % (error_code, error_msg))


class UltraDNSAuthentication(ErrorHandlingMixin):
    def __init__(self, url, user, password):
        self._url = url
        self._user = user
        self._password = password
        self.access_token = ''
        self._refresh_token = ''

    def authenticate(self):
        data = {'grant_type': 'password', 'username': self._user,
                'password': self._password}
        response = requests.post(self._url + '/v1/authorization/token',
                                 data=data)
        json_body = response.json()
        if response.ok:
            self.access_token = json_body[u'accessToken']
            self._refresh_token = json_body[u'refreshToken']
        else:
            self._handle_error(response)

    def is_auth_token_expired(self, response):
        """Return True if response says that the authentication token
        is expired.
        """
        json_body = response.json()
        return (response.status_code == requests.codes.UNAUTHORIZED and
                isinstance(json_body, dict) and
                json_body.get('errorCode') == ERR_CODE_AUTH_TOKEN_EXPIRED)

    def refresh_auth_token(self):
        data = {'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token}
        response = requests.post(self._url + '/v1/authorization/token',
                                 data=data)
        json_body = response.json()
        if response.ok:
            self.access_token = json_body[u'accessToken']
            self._refresh_token = json_body[u'refreshToken']
        else:
            raise AuthenticationError(json_body)


class UltraDNSClient(BaseDNSClient, ErrorHandlingMixin):
    _auth_class = UltraDNSAuthentication

    def __init__(self, username, password, url='https://restapi.ultradns.com'):
        self._username = username
        self._password = password
        self._base_url = url
        self._auth = self._auth_class(self._base_url, self._username,
                                      self._password)

        self._transaction = False
        self._transaction_queries = []
        self._connect()
        self._account_name = \
            self.get_account_details()[u'accounts'][0][u'accountName']

    def create_primary_zone(self, zone_name):
        zone_properties = {'name': zone_name, 'accountName': self._account_name,
                           'type': 'PRIMARY'}
        primary_zone_info = {'forceImport': True, 'createType': 'NEW'}
        zone_data = {'properties': zone_properties,
                     'primaryCreateInfo': primary_zone_info}
        self._post('/v1/zones', zone_data)

    def get_zones_of_account(self, account_name, q=None, **kwargs):
        uri = '/v1/accounts/' + account_name + '/zones'
        params = self._build_params(q, kwargs)
        return self._get(uri, params)

    def get_zone_metadata(self, zone_name):
        return self._get('/v1/zones/' + zone_name)

    def delete_zone(self, zone_name):
        self._delete('/v1/zones/' + zone_name)

    def get_records(self, zone_name, rtype=None, q=None, **kwargs):
        uri = '/v1/zones/' + zone_name + '/rrsets'
        if rtype:
            uri += '/' + rtype
        params = self._build_params(q, kwargs)

        try:
            return self._get(uri, params)['rrSets']
        except RecordsNotFoundError:
            return []

    def create_record(self, zone_name, rtype, owner_name, rdata, ttl=None):
        if not isinstance(rdata, list):
            rdata = [rdata]

        record = {'rdata': rdata}
        if ttl:
            record.update({'ttl': ttl})

        self._post('/v1/zones/' + zone_name + '/rrsets/' + rtype + '/' +
                   owner_name, record)

    def edit_record(self, zone_name, rtype, owner_name, rdata, ttl=None):
        if type(rdata) is not list:
            rdata = [rdata]

        record = {'rdata': rdata}
        if ttl is not None:
            record.update({'ttl': ttl})

        uri = '/v1/zones/' + zone_name + '/rrsets/' + rtype + '/' + owner_name
        return self._put(uri, record)

    def delete_record(self, zone_name, rtype, owner_name):
        return self._delete('/v1/zones/' + zone_name + '/rrsets/' + rtype +
                            '/' + owner_name)

    def get_account_details(self):
        """Returns a list of all accounts of which the current user is a
        member."""
        return self._get('/v1/accounts')

    def version(self):
        """Returns the version of the REST API server."""
        return self._get('/v1/version')

    def status(self):
        """Returns the status of the REST API server."""
        return self._get('/v1/status')

    def start_transaction(self):
        if self._transaction:
            raise TransactionAlreadyInProgressError()
        self._transaction_queries = []
        self._transaction = True

    def commit_transaction(self):
        if not self._transaction:
            raise NoActiveTransactionError()
        elif not self._transaction_queries:
            raise EmptyTransactionError()

        result = self._run_transaction_queries()
        return result

    def _end_transaction(self):
        if not self._transaction:
            raise NoActiveTransactionError()

        self._transaction_queries = []
        self._transaction = False

    def rollback_transaction(self):
        if not self._transaction:
            raise NoActiveTransactionError()
        self._end_transaction()

    def _connect(self):
        self._auth.authenticate()

    def _build_headers(self):
        return {'Content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self._auth.access_token}

    def _build_params(self, q, args):
        params = {}
        params.update(args)
        if q is not None:
            params.update(q)
        return params

    def _get(self, url, params={}):
        if self._transaction:
            raise GetInsideTransactionError
        return self._do_call('GET', url, params=params)

    def _post(self, url, data):
        return self._request('POST', url, data)

    def _put(self, url, data):
        return self._request('PUT', url, data)

    def _delete(self, url):
        return self._request('DELETE', url)

    def _request(self, method, url, data=None):
        if self._transaction:
            self._transaction_queries.append(
                self._get_transaction_query_body(method, url, data))
        else:
            return self._do_call(method, url, data=json.dumps(data))

    def _get_transaction_query_body(self, method, url, data={}):
        return {'method': method.upper(), 'uri': url, 'body': data}

    def _do_call(self, method, url, params=None, data={}):
        def _http_request(method, url, params, data):
            return requests.request(method, self._base_url + url,
                                    params=params, data=data,
                                    headers=self._build_headers())

        response = _http_request(method, url, params, data)
        if response.status_code == requests.codes.NO_CONTENT:
            return None
        elif self._is_error(response):
            if self._auth.is_auth_token_expired(response):
                self._auth.refresh_auth_token()
                return self._do_call(method, url, params, data)
            elif self._transaction:
                self._handle_transaction_error(response)
            else:
                self._handle_error(response)

        try:
            return response.json()
        except ValueError:
            return True

    def _run_transaction_queries(self):
        try:
            result = self._do_call('post', '/v1/batch',
                                   data=json.dumps(self._transaction_queries))
        finally:
            self._end_transaction()

        return result

    def _handle_transaction_error(self, response):
        errors = response.json()['errors']
        raise TransactionError([e['errorMessage'] for e in errors])

