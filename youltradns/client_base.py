import abc


class BaseDNSClient(object):
    @abc.abstractmethod
    def get_zones_of_account(self, account_name, q=None, **kwargs):
        """Returns a list of zones for the specified account.

        Arguments:
            account_name -- The name of the account.

        Keyword Arguments:
            q -- The search parameters, in a dict.  Valid keys are:
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

    @abc.abstractmethod
    def get_zone_metadata(self, zone_name):
        """Get metadata for zone.

        Arguments:
            zone_name -- The name of the zone.  It must be unique.
        """

    @abc.abstractmethod
    def create_primary_zone(self, zone_name):
        """Creates a new primary zone.

        Arguments:
            zone_name -- The name of the zone.  It must be unique.
        """

    @abc.abstractmethod
    def delete_zone(self, zone_name):
        """Deletes the specified zone.

        Arguments:
            zone_name -- The name of the zone being deleted.
        """

    @abc.abstractmethod
    def get_records(self, zone_name, rtype=None, q=None, **kwargs):
        """Returns the list of records in the specified zone.

        Arguments:
            zone_name -- The name of the zone.

        Keyword Arguments:
            q -- The search parameters, in a dict.  Valid keys are:
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
    def start_transaction(self):
        """ Start transaction. """

    @abc.abstractmethod
    def commit_transaction(self):
        """ Commit transaction. """

    @abc.abstractmethod
    def rollback_transaction(self):
        """ Rollback transaction. """
