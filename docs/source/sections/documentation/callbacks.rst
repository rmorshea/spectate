Callbacks
=========

Callbacks are registered to specific methods in pairs - one will be triggered before, and the other after, a call to that method is made. These two callbacks are referred to as "beforebacks" and "afterbacks" respectively. Defining both a beforeback and an afterback in each pair is not required, but doing so allows a beforeback to pass data to its corresponding afterback.


Beforebacks
-----------

Have a signature of ``(instance, call)``

+ ``instance`` is the owner of the method
+ ``call`` is a ``dict`` with the keys
    + ``'name'`` - the name of the method which was called
    + ``'args'`` - the arguments which that method will call
    + ``'kwargs'`` - the keywords which tCallbacks are registered to specific methods in pairs - one will be triggered before, and the other after, a call to that method is made. These two callbacks are referred to as "beforebacks" and "afterbacks" respectively. Defining both a beforeback and an afterback in each pair is not required, but doing so allows a beforeback to pass data to its corresponding afterback.


    ### Beforebacks

    Have a signature of ``(instance, call)``

    + ``instance`` is the owner of the method
    + ``call`` is a ``dict`` with the keys
        + ``'name'`` - the name of the method which was called
        + ``'args'`` - the arguments which that method will call
        + ``'kwargs'`` - the keywords which that method will call
    + Can ``return`` a value which gets passed on to its respective afterback, or a [Closure](#Closure) that itself gets treated as an afterback.


    ### Afterbacks

    Have a signature of ``(instance, answer)``

    + ``instance`` is the owner of the method
    + ``answer`` is a ``dict`` with the keys
        + ``'name'`` - the name of the method which was called
        + ``'value'`` - the value returned by the method
        + ``'before'`` - the value returned by the respective beforeback


    ### Closures

    Have a signature of ``(value)``

    + ``'value'`` - the value returned by the method
    + All other information is already contained in the closures scope.
    + Should not ``return`` anything.hat method will call
+ Can ``return`` a value which gets passed on to its respective afterback, or a [Closure](#Closure) that itself gets treated as an afterback.


Afterbacks
----------

Have a signature of ``(instance, answer)``

+ ``instance`` is the owner of the method
+ ``answer`` is a ``dict`` with the keys
    + ``'name'`` - the name of the method which was called
    + ``'value'`` - the value returned by the method
    + ``'before'`` - the value returned by the respective beforeback


Closures
--------

Have a signature of ``(value)``

+ ``'value'`` - the value returned by the method
+ All other information is already contained in the closures scope.
+ Should not ``return`` anything.
