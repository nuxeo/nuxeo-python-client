Work with comments
------------------

**Fetch a comment**

.. code:: python

    nuxeo.comments.get('<COMMENT_UID>')

**Create a new comment**

.. code:: python

    new_comment = Comment(
        parentId='<DOC_UID>',
        text='This is my comment',
    )
    comment = server.comments.create(new_comment)

    # or from a Document object
    doc.comment('This is my comment')

**Modify a comment**

.. code:: python

    comment.text = 'Text modified'
    comment.save()

**Delete a comment**

.. code:: python

    comment.delete()

    # or
    nuxeo.comments.delete('<COMMENT_UID>')
