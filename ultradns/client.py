import json

import requests

from exceptions import (ZoneNotFoundError, ZoneAlreadyExistsError,
                        PermissionDeniedError, DNSError, TransactionError,
                        TransactionAlreadyInProgressError,
                        NoActiveTransactionError, EmptyTransactionError,
                        GetInsideTransactionError, RecordsNotFoundError,
                        RecordAlreadyExistsError, AuthenticationError,
                        HTTPLevelError)

ERR_CODE_AUTH_TOKEN_EXPIRED = 60001
ERR_CODE_ZONE_ALREADY_EXISTS = 1802
ERR_CODE_ZONE_NOT_FOUND = 1801
ERR_CODE_PERMISSION_DENIED = 8001
ERR_RECORDS_NOT_FOUND = 70002
ERR_RECORD_ALREADY_EXISTS = 2111
ERR_RECORD_NOT_FOUND = 56001
ERR_HTTP = 111222333

exceptions_map = {ERR_CODE_PERMISSION_DENIED: PermissionDeniedError,
                  ERR_CODE_ZONE_NOT_FOUND: ZoneNotFoundError,
                  ERR_CODE_ZONE_ALREADY_EXISTS: ZoneAlreadyExistsError,
                  ERR_RECORD_ALREADY_EXISTS: RecordAlreadyExistsError,
                  ERR_RECORDS_NOT_FOUND: RecordsNotFoundError,
                  ERR_RECORD_NOT_FOUND: RecordsNotFoundError,
                  ERR_HTTP: HTTPLevelError}


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
        elif isinstance(json_body, dict):
            error_code = json_body['errorCode']
            error_msg = json_body['errorMessage']
        else:
            error_code = ERR_HTTP
            error_msg = """
HTTP-level error. HTTP code: %s; response body: %s""" % (
                response.status_code, response.content)

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

    def is_authenticated(self):
        return self.access_token

    def is_auth_token_expired(self, response):
        """Return True if response says that the authentication token
        is expired.
        """
        if response.status_code == requests.codes.UNAUTHORIZED:
            json_body = response.json()
            return (isinstance(json_body, dict) and
                    json_body.get('errorCode') == ERR_CODE_AUTH_TOKEN_EXPIRED)

        return False

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


class UltraDNSClient(ErrorHandlingMixin):
    _auth_class = UltraDNSAuthentication

    def __init__(self, username, password, url='https://restapi.ultradns.com'):
        self._username = username
        self._password = password
        self._base_url = url
        self._auth = self._auth_class(self._base_url, self._username,
                                      self._password)

        self._transaction = False
        self._transaction_queries = []

    def create_primary_zone(self, zone_name):
        """Creates a new primary zone.

        Arguments:
            zone_name -- The name of the zone.  It must be unique.
        """
        zone_properties = {'name': zone_name,
                           'accountName': self._account_name,
                           'type': 'PRIMARY'}
        primary_zone_info = {'forceImport': True, 'createType': 'NEW'}
        zone_data = {'properties': zone_properties,
                     'primaryCreateInfo': primary_zone_info}
        self._post('/v1/zones', zone_data)

    def get_zones_of_account(self, account_name, query=None, **kwargs):
        """Returns a list of zones for the specified account.

        Arguments:
            account_name -- The name of the account.

        Keyword Arguments:
            query -- The search query, string:
                     "<key1>:<value1>,<key2>:<value2>,". Valid keys are:
                         name - substring match of the zone name
                         zone_type - one of:
                            PRIMARY
                            SECONDARY
                            ALIAS
            sort -- The sort column used to order the list. Valid values for
                    the sort field are:
                    NAME
                    ACCOUNT_NAME
                    RECORD_COUNT
                    ZONE_TYPE
            reverse -- Whether the list is ascending(False) or descending(True)
            offset -- The position in the list for the first returned
                      element(0 based)
            limit -- The maximum number of rows to be returned.
        """
        uri = '/v1/accounts/' + account_name + '/zones'
        params = self._build_params(query, kwargs)
        return self._get(uri, params)

    def get_zone_metadata(self, zone_name):
        return self._get('/v1/zones/' + zone_name)

    def delete_zone(self, zone_name):
        """Deletes the specified zone.

        Arguments:
            zone_name -- The name of the zone being deleted.
        """
        self._delete('/v1/zones/' + zone_name)

    def get_records(self, zone_name, rtype=None, query=None, **kwargs):
        """Returns the list of records in the specified zone.

        Arguments:
            zone_name -- The name of the zone.

        Keyword Arguments:
            query -- The search query, string:
                     "<key1>:<value1>,<key2>:<value2>,". Valid keys are:
                         ttl - must match the TTL for the rrset
                         owner - substring match of the owner name
                         value - substring match of the first BIND field value
            sort -- The sort column used to order the list. Valid values for
                    the sort field are:
                    OWNER
                    TTL
                    TYPE
            reverse -- Whether the list is ascending(False) or descending(True)
            offset -- The position in the list for the first returned
                      element(0 based)
            limit -- The maximum number of rows to be returned.
        """
        uri = '/v1/zones/' + zone_name + '/rrsets'
        if rtype:
            uri += '/' + rtype
        params = self._build_params(query, kwargs)

        try:
            return self._get(uri, params)['rrSets']
        except RecordsNotFoundError:
            return []

    def create_record(self, zone_name, rtype, owner_name, rdata, ttl=None):
        """Creates a new record in the specified zone.

        Arguments:
            zone_name -- The zone that will contain the new record.
                         The trailing dot is optional.
            rtype -- The type of the record.  This can be numeric (1) or
                     if a well-known name is defined for the type (A), you can
                     use it instead.
            owner_name -- The owner name for the record.
                          If no trailing dot is supplied, the owner_name is
                          assumed to be relative (foo).
                          If a trailing dot is supplied, the owner name is
                          assumed to be absolute (foo.zonename.com.)
            rdata -- The BIND data for the record as a string.
                     If there is a single resource record in the record, you
                     can pass in the single string.
                     If there are multiple resource records  in this record,
                     pass in a list of strings.

        Keyword Arguments:
            ttl -- The TTL value for the record.
        """
        if not isinstance(rdata, list):
            rdata = [rdata]

        record = {'rdata': rdata}
        if ttl:
            record['ttl'] = ttl

        self._post('/v1/zones/' + zone_name + '/rrsets/' + rtype + '/' +
                   owner_name, record)

    def edit_record(self, zone_name, rtype, owner_name, rdata, ttl=None):
        """Updates an existing record in the specified zone.

        Arguments:
            zone_name -- The zone that contains the record.  The trailing dot
                         is optional.
            rtype -- The type of the record.  This can be numeric (1) or
                     if a well-known name is defined for the type (A), you can
                     use it instead.
            owner_name -- The owner name for the record.
                          If no trailing dot is supplied, the owner_name is
                          assumed to be relative (foo).
                          If a trailing dot is supplied, the owner name is
                          assumed to be absolute (foo.zonename.com.)
            rdata -- The updated BIND data for the record as a string.
                     If there is a single resource record in the record, you
                     can pass in the single string.
                     If there are multiple resource records  in this record,
                     pass in a list of strings.

        Keyword Arguments:
            ttl -- The updated TTL value for the record.
        """
        if type(rdata) is not list:
            rdata = [rdata]

        record = {'rdata': rdata}
        if ttl is not None:
            record['ttl'] = ttl

        uri = '/v1/zones/' + zone_name + '/rrsets/' + rtype + '/' + owner_name
        return self._put(uri, record)

    def delete_record(self, zone_name, rtype, owner_name):
        """Deletes an record.

        Arguments:
            zone_name -- The zone containing the record to be deleted.
                         The trailing dot is optional.
            rtype -- The type of the record.  This can be numeric (1) or
                     if a well-known name is defined for the type (A), you can
                     use it instead.
            owner_name -- The owner name for the record.
                          If no trailing dot is supplied, the owner_name is
                          assumed to be relative (foo).
                          If a trailing dot is supplied, the owner name is
                          assumed to be absolute (foo.zonename.com.)
        """
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
        """ Start transaction. """
        if self._transaction:
            raise TransactionAlreadyInProgressError()
        self._transaction_queries = []
        self._transaction = True

    def commit_transaction(self):
        """ Commit transaction. """
        if not self._transaction:
            raise NoActiveTransactionError()
        elif not self._transaction_queries:
            raise EmptyTransactionError()

        result = self._run_transaction_queries()
        return result

    def rollback_transaction(self):
        """ Rollback transaction. """
        if not self._transaction:
            raise NoActiveTransactionError()
        self._end_transaction()

    def _end_transaction(self):
        if not self._transaction:
            raise NoActiveTransactionError()

        self._transaction_queries = []
        self._transaction = False

    def _authenticate(self):
        self._auth.authenticate()

    @property
    def _account_name(self):
        return self.get_account_details()[u'accounts'][0][u'accountName']

    def _is_authenticated(self):
        return self._auth.is_authenticated()

    def _build_headers(self):
        return {'Content-type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self._auth.access_token}

    def _build_params(self, query, args):
        params = {}
        params.update(args)
        if query is not None:
            params['q'] = query
        return params

    def _get(self, url, params=None):
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

    def _get_transaction_query_body(self, method, url, data=None):
        return {'method': method.upper(), 'uri': url, 'body': data or {}}

    def _do_call(self, method, url, params=None, data=None):
        if not self._is_authenticated():
            self._authenticate()

        response = requests.request(method, self._base_url + url,
                                    params=params, data=data,
                                    headers=self._build_headers())

        if response.status_code == requests.codes.NO_CONTENT:
            return None

        if self._is_error(response):
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
