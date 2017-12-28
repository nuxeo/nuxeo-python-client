# coding: utf-8
from __future__ import unicode_literals

from requests import Response

from .exceptions import HTTPError


class APIEndpoint(object):
    """
    Represents an API endpoint for Nuxeo, containing common patterns
    for CRUD operations.
    """

    def __init__(self, client, endpoint=None, headers=None, cls=None):
        # type: (NuxeoClient, Optional[Text], Optional[Dict[Text, Text]], Optional[Type]) -> None
        """
        Creates an instance of the APIEndpoint class.

        :param client: the authenticated REST client
        :param endpoint: the URL path to the resource endpoint
        :param headers: the extra HTTP headers
        :param cls: the Class to use when parsing results
        """
        self.client = client
        if endpoint:
            self.endpoint = '{}/{}'.format(client.api_path, endpoint)
        else:
            self.endpoint = client.api_path
        self.headers = headers or {}
        self._cls = cls

    def get(self,
            request_path=None,      # type: Optional[Text]
            resource_cls=None,      # type: Optional[Type]
            raw=False,              # type: bool
            single_resource=False,  # type: bool
            **kwargs                # type: **Any
            ):
        # type: (...) -> Any
        """
        Gets the details for one or more resources

         :param request_path: the endpoint (URL path) for the request
         :param resource_cls: a class to use for parsing, if different than the base resource
         :param raw: if True, directly return the content of the response
         :param single_resource: if True, do not parse as list
         :return one or more instances of cls parsed from the returned JSON
        """

        endpoint = self.endpoint

        if not resource_cls:
            resource_cls = self._cls

        if request_path:
            endpoint = '{}/{}'.format(endpoint, request_path)

        response = self.client.request('GET', endpoint, **kwargs)

        if isinstance(response, Response):
            if raw:
                return response.content
            json = response.json()
        else:
            json = response

        if resource_cls == dict:
            return json

        if not single_resource and isinstance(json, dict) and 'entries' in json:
            json = json['entries']

        if isinstance(json, list):
            return [resource_cls.parse(resource, service=self) for resource in json]

        return resource_cls.parse(response.json(), service=self)

    def post(self, resource=None, request_path=None, raw=False, **kwargs):
        # type: (Optional[Any], Optional[Text], Optional[Text], **Any) -> Any
        """
        Creates a new instance of the resource.

        :param resource: the data to post
        :param request_path: the endpoint (URL path) for the request
        :param raw: if False, parse the outgoing data to JSON
        :return the created resource
        """
        if resource and not raw and not isinstance(resource, dict):
            if isinstance(resource, self._cls):
                resource = resource.as_dict()
            else:
                raise ValueError('Data must be a Model object or a dictionary.')

        endpoint = self.endpoint

        if request_path:
            endpoint = '{}/{}'.format(endpoint, request_path)

        response = self.client.request(
            'POST', endpoint, data=resource, raw=raw, **kwargs)

        return self._cls.parse(response.json(), service=self)

    def put(self, resource=None, request_path=None, **kwargs):
        # type: (Optional[Model], Optional[Text], **Any) -> Any
        """
        Edits an existing resource.

        :param resource: the resource instance
        :param request_path: the endpoint (URL path) for the request
        :return the modified resource
        """

        endpoint = self.endpoint

        if request_path:
            endpoint = '{}/{}'.format(endpoint, request_path)
        else:
            endpoint = '{}/{}'.format(endpoint, resource.id)

        if resource:
            resource = resource.as_dict()

        response = self.client.request('PUT', endpoint, data=resource, **kwargs)

        if resource:
            return self._cls.parse(response.json(), service=self)

    def delete(self, resource_id):
        # type: (Text) -> Any
        """
        Deletes an existing resource.

        :param resource_id: the resource ID to be deleted
        :
        """

        endpoint = '{}/{}'.format(self.endpoint, resource_id)

        response = self.client.request('DELETE', endpoint)

        if response.content:
            return self._cls.parse(response.json(), service=self)

    def exists(self, request_path):
        # type: (Text) -> bool
        """
        Checks if a resource exists.

        :param request_path: the endpoint (URL path) for the request
        :return: True if it exists, else False
        """
        endpoint = '{}/{}'.format(self.endpoint, request_path)

        try:
            self.client.request('GET', endpoint)
            return True
        except HTTPError as e:
            if e.status != 404:
                raise e
        return False
