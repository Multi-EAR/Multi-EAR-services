*************************************
Multi-EAR services - CTRL 
*************************************

Local web service to access and monitor both the device and data.

The web service is started automatically via the ``multi-ear-ctrl.service`` in ``/etc/systemd/system`` via a ``uwsgi`` socket handled via ``nginx`` on the default http port 80.

Service
=======

:Service:
    multi-ear-ctrl.service
:ExecStart:
    /home/tud/.py37/bin/uwsgi --ini /home/tud/.py37/multi-ear-services/uwsgi.ini
:Restart:
    always
:SyslogIdentifier:
    multi-ear-ctrl
:Log:
    /var/log/multi-ear/ctrl.log

API
===

DataSelect
----------

.. code-block::

    /api/dataselect/health
    /api/dataselect/query

:starttime:
    Date time string (UTC) or time delta string (defaults to 30min).
:endtime:
    Defaults to now (UTC).
:measurement:
    '*'. Allows multiple items (comma separeted) and regex.
:field:
    '*'. Allows multiple items (comma separeted) and regex.
:bucket:
    telegraf/
:database:
    telegraf
:retention_policy:
    Empty (default database retention policy)
:format:
    json (default), csv or miniseed
:nodata:
    204 (default) or 404


Usage
=====

Command line
------------

You can also manually start the web-service on `http://127.0.0.1:5000`_ for development (bypassing uWSGI and nginx).

First check if the Flask environment variables are set correctly.

.. code-block:: console

    echo $FLASK_APP  # should be multi_ear_services.ctrl
    echo $FLASK_ENV  # should be production (default) or development

If not set in ``.bashrc`` or incorrect

.. code-block:: console

    export FLASK_ENV=development
    export FLASK_APP=multi_ear_services.ctrl

Start the web-service

.. code-block:: console

    flask run

Python
------

.. code-block:: python3

    from multi_ear_services import ctrl
