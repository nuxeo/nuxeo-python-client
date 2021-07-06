# coding: utf-8
import pytest

from nuxeo.models import Batch

# We do not need to set-up a server and log the current test
skip_logging = True


def test_data_leak_with_mutable_properties():
    from nuxeo.models import Batch

    # Testing the Batch.blobs property
    assert isinstance(Batch.__slots__["blobs"], dict)
    # It is empty by default
    assert not Batch.__slots__["blobs"]

    # Mimic on old behavior when the class property could be altered
    Batch.__slots__["blobs"] = {0: "a blob"}

    # Check that the property is not leaked for new instances
    batch = Batch(batchId="1234")
    assert not batch.blobs
    batch = Batch(batchId="1234", blobs={1: "my own blob"})
    assert batch.blobs == {1: "my own blob"}


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, False),
        ({"provider": "s3"}, True),
        ({"provider": "areamaster"}, False),
        ({"provider": "s3", "extraInfo": {}}, True),
        ({"provider": "areamaster", "extraInfo": {"provider_type": "s3"}}, True),
        ({"provider": "areamaster", "extraInfo": {"provider_type": "S3"}}, True),
        ({"provider": "areamaster", "extraInfo": {"provider_type": ""}}, False),
        ({"provider": "areamaster", "extraInfo": {"provider_type": None}}, False),
        ({"provider": "areamaster", "extraInfo": "s3"}, False),
    ],
)
def test_batch_is_s3(kwargs, expected):
    batch = Batch(**kwargs)
    assert batch.is_s3() is expected
