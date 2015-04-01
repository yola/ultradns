from mock import Mock, patch
from unittest2 import TestCase

import ultradns
from ultradns.client import UltraDNSClient
from ultradns.exceptions import HTTPError


class ClientTestCase(TestCase):
    def _mock_response(self, requests_mock, json_result, status_code=200,
                       content=None):
        response_mock = Mock()
        response_mock.status_code = status_code
        response_mock.json = Mock(return_value=json_result)
        response_mock.content = content
        requests_mock.return_value = response_mock


class TestCreatePrimaryZone(ClientTestCase):

    @patch.object(ultradns.client.UltraDNSAuthentication, 'is_authenticated')
    @patch.object(ultradns.client.requests, 'request')
    def test_http_error_is_raised(self, post_mock, auth_mock):
        self._mock_response(post_mock, '', 504, content='')
        auth_mock.return_value=True
        client = UltraDNSClient('user', 'password')

        with self.assertRaises(HTTPError) as exc:
            client.create_primary_zone('aaa.bbb.ccc')

        expected_message = 'HTTP-level error. HTTP code: 504; response body: '
        self.assertEqual(exc.exception.message, expected_message)
