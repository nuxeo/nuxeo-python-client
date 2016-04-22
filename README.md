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
