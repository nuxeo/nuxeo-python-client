# coding: utf-8
from __future__ import unicode_literals

# We do not need to set-up a server and log the current test
skip_logging = True


def test_data_leak_with_mutable_properties():
    from nuxeo.models import Batch

    # Testing the Batch.blobs property
    assert isinstance(Batch._valid_properties["blobs"], dict)
    # It is empty by default
    assert not Batch._valid_properties["blobs"]

    # Mimic on old behavior when the class property could be altered
    Batch._valid_properties["blobs"] = {0: "a blob"}

    # Check that the property is not leaked for new instances
    batch = Batch(batchId="1234")
    assert not batch.blobs
    batch = Batch(batchId="1234", blobs={1: "my own blob"})
    assert batch.blobs == {1: "my own blob"}
