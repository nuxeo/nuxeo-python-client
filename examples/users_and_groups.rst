Manage users and groups
-----------------------

Users
~~~~~

**Fetch a user**

.. code:: python

    nuxeo.users().fetch('Administrator')

**Create a new user**

.. code:: python

    new_user = {
        'username': 'leela',
        'password': 'goodnewseveryone',
        'firstName': 'Leela',
        'lastName': 'Turanga',
        'company': 'Futurama',
        'email': 'leela@futurama.com',
    }
    user = nuxeo.users().create(new_user)

**Modify a user**

.. code:: python

    user = nuxeo.users().fetch('leela')
    user.set({
        'company': 'Planet Express',
        'email': 'leela@planetexpress.com'
    })
    user.save()

**Change a user's password**

You can change the password by using the ``set`` method explained above,
but you can also use this one-liner instead:

.. code:: python

    user = nuxeo.users().fetch('leela')
    user.change_password('multipass')

**Delete a user**

.. code:: python

    nuxeo.users().delete('leela')

Groups
~~~~~~

**Fetch a group**

.. code:: python

    nuxeo.groups().fetch('administrators')

**Create a new group**

.. code:: python

    new_group = {
        'groupname': 'foo',
        'grouplabel': 'Foo',
    }
    group = nuxeo.groups().create(new_group)

**Modify a group**

.. code:: python

    group = nuxeo.groups().fetch('foo')
    group.set({
        'groupname': 'bar',
        'grouplabel': 'Bar',
    })
    group.save()

**Delete a group**

.. code:: python

    nuxeo.groups().delete('foo')
