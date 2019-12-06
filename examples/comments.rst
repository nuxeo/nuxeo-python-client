Work with comments
------------------

**Fetch a comment**

.. code:: python

    comment = nuxeo.comments.get('<COMMENT_UID>')

**Create a new comment**

.. code:: python

    new_comment = Comment(
        parentId='<DOC_UID>',
        text='This is my comment',
    )
    comment = server.comments.create(new_comment)

**Modify a comment**

.. code:: python

    comment.text = 'Text modified'
    comment.save()

**Delete a comment**

.. code:: python

    nuxeo.comments.delete('<COMMENT_UID>')

**Reply to a given comment**

A repy is just a comment for a given comment.

.. code:: python

    comment.reply('My reply comment')
    comment.reply('Another reply')
    comment.reply('And a 3rd one')

You can reply to replies as well (everything is comment):

.. code:: python

    reply = comment.reply('This is awesome, even unicode: \N{SNOWMAN}')
    reply.reply('Yeah, I know, I know! ᕦ(ò_óˇ)ᕤ')

**Check if the comment has at least 1 reply**

.. code:: python

    comment.has_replies()
