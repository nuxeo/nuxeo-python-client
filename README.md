## Client Library for Nuxeo API

[![Build Status](https://qa.nuxeo.org/jenkins/buildStatus/icon?job=nuxeo-python-client-master&style=flat)](http://qa.nuxeo.org/jenkins/job/nuxeo-python-client-master)

The Nuxeo Python Client is a Python client library for the Nuxeo Automation and REST API.

This is an on-going project, supported by Nuxeo.

## Getting Started


After installing [Python](https://www.python.org/downloads/), use `pip` to install the `nuxeo-client` package:

    $ pip install nuxeo-client

Then, use the following `import` statement to have access to the Nuxeo API:

```python
from nuxeo import Nuxeo
```

## Documentation

Check out the [API documentation](https://nuxeo.github.io/nuxeo-js-client/latest/).

## Requirements

The Nuxeo Python client works only with Nuxeo Platform >= LTS 2015.

## Quick Start

This quick start guide will show how to do basics operations using the client.

### Creating a Client

```python
nuxeo = new Nuxeo(
  auth={
    username: 'Administrator',
    password: 'Administrator'
  })
```

To connect to a different Nuxeo Platform Instance, you can use the following:

```python
nuxeo = new Nuxeo(
  base_url='http://demo.nuxeo.com/nuxeo/',
  auth={
    username: 'Administrator',
    password: 'Administrator'
  })
```

### Operation

`Operation` object allows you to execute an operation
(or operation chain).

See the [Operation](https://nuxeo.github.io/nuxeo-js-client/latest/Operation.html) documentation.

#### Samples

__Call an operation to create a new folder in the Root document__

```python
operation = nuxeo.operation('Document.Create')
operation.params({
    type: 'Folder',
    name: 'My Folder',
    properties: 'dc:title=My Folder \ndc:description=A Simple Folder'
  })
operation.input('/')
doc = operation.execute()
```

### Request

The `Request` object allows you to call the Nuxeo REST API.

See the [Request](https://nuxeo.github.io/nuxeo-js-client/latest/Request.html) documentation.

#### Samples

__Fetch the Administrator user__

```python
user = nuxeo.request('user/Administrator')
```

__Fetch the whole list of Natures__

```python
natures = nuxeo.request('directory/nature')
```

### Repository

The `Repository` object allows you to work with document.

See the [Repository](https://nuxeo.github.io/nuxeo-js-client/latest/Repository.html) documentation.

#### Samples

__Create a `Repository` object__

```python
defaultRepository = nuxeo.repository(); // 'default' repository
...
testRepository = nuxeo.repository('test'); // 'test' repository
...
```

__Fetch the Root document__

```python
nuxeo.repository().fetch('/')
```

__Create a new folder__

```python
newFolder = {
  'entity-type': 'document',
  name: 'a-folder',
  type: 'Folder',
  properties: {
    'dc:title': 'foo',
  }
}
folder = nuxeo.repository().create('/', newFolder)
```

__Delete a document__

```javascript
nuxeo.repository().delete('/a-folder')
```

### Document

`Repository` object returns and works with `Document` objects. `Document` objects exposes a simpler API
to work with a document.

See the [Document](https://nuxeo.github.io/nuxeo-js-client/latest/Document.html) documentation.

#### Samples

__Retrieve a `Document` object__

```python
doc = nuxeo.repository().fetch('/')
```

__Set a document property__

```python
doc.set({ 'dc:title': 'foo' })
```

__Get a document property__

```python
doc.get('dc:title')
```

__Save an updated document__

```python
doc = nuxeo.repository().fetch('/')
doc.set({ 'dc:title': 'foo' })
doc.save()
```

__Fetch the main Blob of a document__

```python
doc.fetch_blob()
```

__Convert a document main Blob to PDF__

```python
doc.convert({ format: 'pdf' })
```

__Fetch the 'thumbnail' rendition__

```python
doc.fetch_rendition('thumbnail')
```

__Fetch the ACLs__

```python
doc.fetch_acls()
```

__Add permission__

```python
doc.add_permission({'username': 'test', 'permission': 'Write'})
```

__Remove permission__

```python
doc.remove_permission({'id': 'members:Write:true:Administrator::'})
```

__Has permission__

```python
doc.has_permission('Write')
```

__Lock document__

```python
doc.lock()
```

__Unlock document__

```python
doc.unlock()
```

__Fetch Lock Status__

```python
doc.fetch_lock_status()
```

### BatchUpload

The `BatchUpload` object allows you to upload blobs to a Nuxeo Platform instance, and use them as operation input or
as document property value.

See the [BatchUpload](https://nuxeo.github.io/nuxeo-js-client/latest/BatchUpload.html) documentation.

#### Samples

__Create a Nuxeo.Blob to be uploaded__

```python
from nuxeo.blob import FileBlob
from nuxeo.blob import BufferBlob
BufferBlob('Content of this text', 'Test.txt', 'text/plain')
...
FileBlob('/path/to/file)
```

__Upload a blob__

```python
nuxeo.batch_upload().upload(blob)
```

__Attach an uploaded blob to a document__

```python
uploaded = nuxeo.batchUpload().upload(blob)
operation = nuxeo.operation('Blob.AttachOnDocument')
operation.params({'document':'/a-file'})
operation.input(uploaded)
operation.execute()
```

### Users

The `Users` object allows you to work with users.

See the [Users](https://nuxeo.github.io/nuxeo-js-client/latest/Users.html) and
[User](https://nuxeo.github.io/nuxeo-js-client/latest/User.html) documentation.

#### Samples

__Fetch an user__

```pyton
nuxeo.users().fetch('Administrator')
```

__Create a new user__

```python
newUser = {
    username: 'leela',
    firstName: 'Leela',
    company: 'Futurama',
    email: 'leela@futurama.com',
  }
user = nuxeo.users().create(newUser)
```

__Delete an user__

```python
nuxeo.users().delete('leela')
```

### Groups

The `Groups` object allows you to work with groups.

See the [Groups](https://nuxeo.github.io/nuxeo-js-client/latest/Groups.html) and
[Group](https://nuxeo.github.io/nuxeo-js-client/latest/Group.html) documentation.

#### Samples

__Fetch a group__

```python
nuxeo.groups().fetch('administrators')
```

__Create a new group__

```python
newGroup = {
  groupname: 'foo',
  grouplabel: 'Foo',
}
group = nuxeo.groups().create(newGroup)
```

__Delete a group__

```python
nuxeo.groups().delete('foo')
```

### Directory

The `Directory` object allows you to work with directories.

See the [Directory](https://nuxeo.github.io/nuxeo-js-client/latest/Directory.html) and
[DirectoryEntry](https://nuxeo.github.io/nuxeo-js-client/latest/DirectoryEntry.html) documentation.

#### Samples

__Fetch all entries of a directory__

```python
entries = nuxeo.directory('nature').fetchAll()
```

__Fetch a given directory entry__

```python
entry = nuxeo.directory('nature').fetch('article')
```

__Create a new directory entry__

```python
newEntry = {
  id: 'foo',
  label: 'Foo',
}
entry = nuxeo.directory('nature').create(newEntry)
```

__Delete a directory entry__

```python
nuxeo.directory('nature').delete('foo')
```

## Contributing

See our [contribution documentation](https://doc.nuxeo.com/x/VIZH).

### Requirements

* [Python >= 2.7](https://www.python.org/downloads/)

### Setup

Install [Python](https://www.python.org/downloads/) and then use `pip` to install all the required
libraries:

    $ git clone https://github.com/nuxeo/nuxeo-python-client
    $ cd nuxeo-python-client
    $ pip install -r requirements.txt

### Test

A Nuxeo Platform instance needs to be running on `http://localhost:8080/nuxeo` for the tests to be run.

Tests can be launched on Node.js with:

    $ nosetests -v


### Reporting Issues

You can follow the developments in the Nuxeo Python Client project of our JIRA bug tracker: [https://jira.nuxeo.com/browse/NXPY](https://jira.nuxeo.com/browse/NXPY).

You can report issues on [answers.nuxeo.com](http://answers.nuxeo.com).

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.txt) Copyright (c) Nuxeo SA


## About Nuxeo

Nuxeo dramatically improves how content-based applications are built, managed and deployed, making customers more agile, innovative and successful. Nuxeo provides a next generation, enterprise ready platform for building traditional and cutting-edge content oriented applications. Combining a powerful application development environment with SaaS-based tools and a modular architecture, the Nuxeo Platform and Products provide clear business value to some of the most recognizable brands including Verizon, Electronic Arts, Netflix, Sharp, FICO, the U.S. Navy, and Boeing. Nuxeo is headquartered in New York and Paris. More information is available at [www.nuxeo.com](http://www.nuxeo.com/).
