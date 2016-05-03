__author__ = 'loopingz'
from document import Document
from urllib import urlencode


class Repository(object):

    def __init__(self, name, service, schemas=[]):
        self._name = name
        self._service = service
        self._schemas = schemas

    def _get_path(self, path):
        if path.startswith('/'):
            return "repo/" + self._name + "/path/" + path
        else:
            return "repo/" + self._name + "/id/" + path

    def get(self, path):
        return self._service.request(self._get_path(path), extra_headers=self._get_extra_headers())

    def fetch(self, path):
        return Document(self.get(path), self)

    def fetch_blob(self, path, xpath = 'blobholder:0'):
        return self._service.request(self._get_path(path) + "/@blob/" + xpath, extra_headers=self._get_extra_headers())

    def fetch_rendition(self, path, name):
        return self._service.request(self._get_path(path) + "/@rendition/" + name, extra_headers=self._get_extra_headers())

    def fetch_renditions(self, path):
        extra = self._get_extra_headers()
        extra['enrichers-document'] = "renditions"
        renditions = []
        for rendition in self._service.request(self._get_path(path), extra_headers=extra)["contextParameters"]["renditions"]:
            renditions.append(rendition['name'])
        return renditions

    def convert(self, path, options):
        xpath = options['xpath'] if 'xpath' in options else 'blobholder:0'
        path = self._get_path(path) + "/@blob/" + xpath + '/@convert'
        if 'xpath' in options:
            del options['xpath']
        if ("converter" not in options and "type" not in options and "format" not in options):
            raise ValueError("One of converter,type,format is mandatory in options")
        path += "?" + urlencode(options, True)
        return self._service.request(path)

    def update(self, obj, uid=None):
        if isinstance(obj, Document):
            properties = obj.properties
            uid = obj.get_id()
        elif isinstance(obj, dict):
            properties = obj
        else:
            raise Exception("Argument should be either a dict or a Document object")
        body = {
            'entity-type': 'document',
            'uid': uid,
            'properties': properties
        }
        return Document(self._service.request(self._get_path(uid), body=body, method="PUT", extra_headers=self._get_extra_headers()), self)

    def _get_extra_headers(self):
        extras_header = dict()
        if len(self._schemas) > 0:
            extras_header['X-NXDocumentProperties'] = ",".join(self._schemas)
        extras_header['X-NXRepository'] = self._name
        return extras_header

    def create(self, path, obj):
        body = {
            'entity-type': 'document',
            'type': obj['type'],
            'name': obj['name'],
            'properties': obj['properties']
        }

        return Document(self._service.request(self._get_path(path), body=body, method="POST", extra_headers=self._get_extra_headers()), self)

    def delete(self, path):
        self._service.request(self._get_path(path), method="DELETE")

    def query(self, opts = dict()):
        path = 'query/'
        if 'query' in opts:
            path += 'NXQL'
        elif 'pageProvider' in opts:
            path += opts['pageProvider']
        else:
            raise Exception("Need either a pageProvider or a query")
        path += "?" + urlencode(opts, True)
        result = self._service.request(path, extra_headers=self._get_extra_headers())
        # Mapping entries to Document
        docs = []
        for doc in result['entries']:
            docs.append(Document(doc, self))
        result['entries']=docs
        return result