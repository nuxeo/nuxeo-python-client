Manage users and groups
-----------------------

Users
~~~~~

**Fetch a user**

.. code:: python

    nuxeo.users.get('Administrator')

**Create a new user**

.. code:: python

    new_user = User(
        properties = {
            'username': 'leela',
            'password': 'goodnewseveryone',
            'firstName': 'Leela',
            'lastName': 'Turanga',
            'company': 'Futurama',
            'email': 'leela@futurama.com',
        })
    user = nuxeo.users.create(new_user)

**Modify a user**

.. code:: python

    user = nuxeo.users.get('leela')
    user.set({
        'company': 'Planet Express',
        'email': 'leela@planetexpress.com'
    })
    user.save()

**Change a user's password**

You can change the password by using the ``set`` method explained above,
but you can also use this one-liner instead:

.. code:: python

    user = nuxeo.users.get('leela')
    user.change_password('multipass')

**Delete a user**

.. code:: python

    nuxeo.users.delete('leela')

Groups
~~~~~~

**Fetch a group**

.. code:: python

    nuxeo.groups.get('administrators')

**Create a new group**

.. code:: python

    new_group = Group(groupname='foo', grouplabel='Foo')
    group = nuxeo.groups.create(new_group)

**Modify a group**

.. code:: python

    group = nuxeo.groups.get('foo')
    group.groupname = 'bar'
    group.grouplabel = 'Bar'
    group.save()

**Delete a group**

.. code:: python

    nuxeo.groups.delete('foo')

**Subgroup**

.. code:: python

    # Create 2 groups
    new_group1 = Group(groupname='ParentGroup', grouplabel='ParentGroup')
    group1 = server.groups.create(new_group1)

    new_group2 = Group(groupname='SubGroup', grouplabel='SubGroup')
    group2 = server.groups.create(new_group2)

    # Add group2 to subgroups of group1
    group1.memberGroups = [group2.groupname]
    group1.save()

Alternatively, if the subgroup already exists, it is smaller to write:

.. code:: python

    new_group = Group(
        groupname='ParentGroup',
        grouplabel='ParentGroup',
        memberGroups=['SubGroup'],
    )
    group = server.groups.create(new_group)
