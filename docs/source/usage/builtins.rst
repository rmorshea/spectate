Builtin Model Types
===================

Spectate provides a number of builtin model types that you can use out of the box.
For most users these built-in types should be enough, however if you're adventurous,
then you can :ref:`define your own models <Creating Models>`.


Dictionary
''''''''''

The :class:`~spectate.mvc.models.Dict` model is a subclass of Python's standard
:class:`dict`. This will produce events when the value of a key in the dictionary
changes or is deleted. This will result when calling methods like :meth:`dict.update`
and :meth:`dict.pop`, but also when using the normal syntax to set or delete an item.
Events produced by :class:`~spectate.mvc.models.Dict` have the following fields:

.. list-table::
  :widths: 1 10
  :header-rows: 1

  * - Field
    - Description

  * - ``key``
    - The key in the dict model that changed.

  * - ``old``
    - * The value that was present in the key before the change
      * Is :attr:`~spectate.mvc.models.Undefined` if the index was not present.

  * - ``new``
    - * The value that this is now present after the change
      * Is :attr:`~spectate.mvc.models.Undefined` if the index was deleted.


List
''''

The :class:`~spectate.mvc.models.List` model is a subclass of Python's standard
:class:`list`. This model will produce events when an element of the list changes
or an element changes from one position to another. This may happen when calling
methods like :meth:`list.append` or :meth:`list.remove`, but also when using the
normal syntax to set or delete an item. Events produced by
:class:`~spectate.mvc.models.List` have the following keys:

.. list-table::
  :widths: 1 10
  :header-rows: 1

  * - Field
    - Description

  * - ``index``
    - The index in the dict model that changed.

  * - ``old``
    - * The value that was present before the change
      * Is :attr:`~spectate.mvc.models.Undefined` if the key was not present.

  * - ``new``
    - * The value that this is now present after the change
      * Is :attr:`~spectate.mvc.models.Undefined` if the key was deleted.


Set
'''

The :class:`~spectate.mvc.models.Set` model is a subclass of Python's standard
:class:`set`. This model will produce events when an element of the set changes.
This may happen when calling methods like :meth:`set.add` or :meth:`set.discard`.
Events produced by :class:`~spectate.mvc.models.Set` have the following keys:

.. list-table::
  :widths: 1 10
  :header-rows: 1

  * - Field
    - Description

  * - ``old``
    - A set of values that were removed due to the change.

  * - ``new``
    - A set of the values that were added due to the change.


Object
''''''

The :class:`~spectate.mvc.models.Object` model is a subclass of Python's standard
:class:`object`. This model will produce events when an attribute of the object changes
or is deleted. This may happen when using :func:`setattr` or :func:`delattr`, but also
when using the normal syntax to set or delete attributes. Events produced by
:class:`~spectate.mvc.models.Object` have the following keys:

.. list-table::
  :widths: 1 10
  :header-rows: 1

  * - Field
    - Description

  * - ``attr``
    - The attribute in the model that changed.

  * - ``old``
    - * The value that was present before the change
      * Is :attr:`~spectate.mvc.models.Undefined` if the attribute was not present.

  * - ``new``
    - * The value that this is now present after the change
      * Is :attr:`~spectate.mvc.models.Undefined` if the key was deleted.
