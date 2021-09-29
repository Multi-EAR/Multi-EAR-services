*************************************
Multi-EAR-CTRL
*************************************
...


Manual setup
============


nginx
-----

Install nginx

.. code-block:: console

    sudo apt install -y nginx


Remove default nginx site at port 80.

.. code-block:: console

    sudo rm -f /etc/nginx/sites-enabled/default
    sudo rm -f /etc/nginx/sites-available/default


Copy multi-ear-ctrl proxy configuration for port 80 to available sites and enable.

.. code-block:: console

    sudo cp nginx.proxy /etc/nginx/sites-available/multi-ear-ctrl.proxy
    sudo ln -s -f /etc/nginx/sites-available/multi-ear-ctrl.proxy /etc/nginx/sites-enabled


Check nginx configuration.

.. code-block:: console

    sudo service nginx configtest


Restart service on success.

.. code-block:: console

    sudo service nginx restart


Nginx is ready.


systemd
-------

.. code-block:: console

    sudo cp ctrl.service /etc/systemd/system/multi-ear-ctrl.service
    sudo systemctl daemon-reload
    sudo systemctl enable multi-ear-ctrl
    sudo systemctl start multi-ear-ctrl
