import json

from rest_api import UltraDNSRestAPI


class UltraDNSClient(object):
    def __init__(self, username, password, url='https://restapi.ultradns.com'):
        """Initialize a API Client.

        Arguments:
            username -- The username of the user
            password -- The password of the user

        Keyword Arguments:
            url -- Base URL for API.
        """
        self._api = UltraDNSRestAPI(username, password, url=url)

    def create_primary_zone(self, zone_name):
        """Creates a new primary zone.

        Arguments:
            zone_name -- The name of the zone.  It must be unique.

        """
        self._api.create_primary_zone(zone_name)

    def delete_zone(self, zone_name):
        """Deletes the specified zone.

        Arguments:
            zone_name -- The name of the zone being deleted.
        """
        return self._api.delete_zone(zone_name)

    def get_records(self, zone_name, q=None, **kwargs):
        """Returns the list of records in the specified zone.

        Arguments:
            zone_name -- The name of the zone.

        Keyword Arguments:
            q -- The search parameters, in a dict.  Valid keys are:
                 ttl - must match the TTL for the rrset
                 owner - substring match of the owner name
                 value - substring match of the first BIND field value
            sort -- The sort column used to order the list. Valid values for the sort field are:
                    OWNER
                    TTL
                    TYPE
            reverse -- Whether the list is ascending(False) or descending(True)
            offset -- The position in the list for the first returned element(0 based)
            limit -- The maximum number of rows to be returned.
        """
        return self._api.get_records(zone_name, q=q, **kwargs)

    def get_records_by_type(self, zone_name, rtype, q=None, **kwargs):
        """Returns the list of records in the specified zone of the specified type.

        Arguments:
            zone_name -- The name of the zone.
            rtype -- The type of the record.  This can be numeric (1) or
                     if a well-known name is defined for the type (A), you can use it instead.

        Keyword Arguments:
            q -- The search parameters, in a dict.  Valid keys are:
                 ttl - must match the TTL for the rrset
                 owner - substring match of the owner name
                 value - substring match of the first BIND field value
            sort -- The sort column used to order the list. Valid values for the sort field are:
                    OWNER
                    TTL
                    TYPE
            reverse -- Whether the list is ascending(False) or descending(True)
            offset -- The position in the list for the first returned element(0 based)
            limit -- The maximum number of rows to be returned.
        """
        return self._api.get_records_by_type(zone_name, rtype, q=q, **kwargs)

    def create_record(self, zone_name, rtype, owner_name, rdata, ttl=None):
        """Creates a new record in the specified zone.

        Arguments:
            zone_name -- The zone that will contain the new record.  The trailing dot is optional.
            rtype -- The type of the record.  This can be numeric (1) or
                     if a well-known name is defined for the type (A), you can use it instead.
            owner_name -- The owner name for the record.
                          If no trailing dot is supplied, the owner_name is assumed to be relative (foo).
                          If a trailing dot is supplied, the owner name is assumed to be absolute (foo.zonename.com.)
            rdata -- The BIND data for the record as a string.
                     If there is a single resource record in the record, you can pass in the single string.
                     If there are multiple resource records  in this record, pass in a list of strings.

        Keyword Arguments:
            ttl -- The TTL value for the record.
        """
        return self._api.create_record(zone_name, rtype, owner_name, rdata, ttl=ttl)

    def edit_record(self, zone_name, rtype, owner_name, rdata, ttl=None):
        """Updates an existing record in the specified zone.

        Arguments:
            zone_name -- The zone that contains the record.  The trailing dot is optional.
            rtype -- The type of the record.  This can be numeric (1) or
                     if a well-known name is defined for the type (A), you can use it instead.
            owner_name -- The owner name for the record.
                          If no trailing dot is supplied, the owner_name is assumed to be relative (foo).
                          If a trailing dot is supplied, the owner name is assumed to be absolute (foo.zonename.com.)
            rdata -- The updated BIND data for the record as a string.
                     If there is a single resource record in the record, you can pass in the single string.
                     If there are multiple resource records  in this record, pass in a list of strings.

        Keyword Arguments:
            ttl -- The updated TTL value for the record.
        """
        return self._api.edit_record(zone_name, rtype, owner_name, rdata, ttl=ttl)

    def delete_record(self, zone_name, rtype, owner_name):
        """Deletes an record.

        Arguments:
            zone_name -- The zone containing the record to be deleted.  The trailing dot is optional.
            rtype -- The type of the record.  This can be numeric (1) or
                     if a well-known name is defined for the type (A), you can use it instead.
            owner_name -- The owner name for the record.
                          If no trailing dot is supplied, the owner_name is assumed to be relative (foo).
                          If a trailing dot is supplied, the owner name is assumed to be absolute (foo.zonename.com.)
        """
        return self._api.delete_record(zone_name, rtype, owner_name)

    def start_transaction(self):
        self._api.start_transaction()

    def commit_transaction(self):
        return self._api.commit_transaction()

    def rollback_transaction(self):
        return self._api.rollback_transaction()
