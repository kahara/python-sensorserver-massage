=============================
sensorserver-massage
=============================

Foo!

Docker
------

For more controlled deployments and to get rid of "works on my computer" -syndrome, we always
make sure our software works under docker.

It's also a quick way to get started with a standard development environment.

SSH agent forwarding
^^^^^^^^^^^^^^^^^^^^

We need buildkit_::

    export DOCKER_BUILDKIT=1

.. _buildkit: https://docs.docker.com/develop/develop-images/build_enhancements/

And also the exact way for forwarding agent to running instance is different on OSX::

    export DOCKER_SSHAGENT="-v /run/host-services/ssh-auth.sock:/run/host-services/ssh-auth.sock -e SSH_AUTH_SOCK=/run/host-services/ssh-auth.sock"

and Linux::

    export DOCKER_SSHAGENT="-v $SSH_AUTH_SOCK:$SSH_AUTH_SOCK -e SSH_AUTH_SOCK"

Creating a development container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build image, create container and start it (switch the 1234 port to the port from src/sensorserver_massage/defaultconfig.py)::

    docker build --progress plain --ssh default --target devel_shell -t sensorserver_massage:devel_shell .
    docker create --name sensorserver_massage_devel -p 1234:1234 -v `pwd`":/app" -it -v /tmp:/tmp `echo $DOCKER_SSHAGENT` sensorserver_massage:devel_shell
    docker start -i sensorserver_massage_devel

pre-commit considerations
^^^^^^^^^^^^^^^^^^^^^^^^^

If working in Docker instead of native env you need to run the pre-commit checks in docker too::

    docker exec -i sensorserver_massage_devel /bin/bash -c "pre-commit install"
    docker exec -i sensorserver_massage_devel /bin/bash -c "pre-commit run --all-files"

You need to have the container running, see above. Or alternatively use the docker run syntax but using
the running container is faster::

    docker run -it --rm -v `pwd`":/app" sensorserver_massage:devel_shell -c "pre-commit run --all-files"

Test suite
^^^^^^^^^^

You can use the devel shell to run py.test when doing development, for CI use
the "tox" target in the Dockerfile::

    docker build --progress plain --ssh default --target tox -t sensorserver_massage:tox .
    docker run -it --rm -v `pwd`":/app" `echo $DOCKER_SSHAGENT` sensorserver_massage:tox

Production docker
^^^^^^^^^^^^^^^^^

There's a "production" target as well for running the application (change the "1234" port and "myconfig.toml" for
config file) and remember to change that architecture tag to arm64 if building on ARM::

    docker build --progress plain --ssh default --target production -t sensorserver_massage:latest .
    docker run -it --name sensorserver_massage -v myconfig.toml:/app/config.toml -p 1234:1234 -v /tmp:/tmp `echo $DOCKER_SSHAGENT` sensorserver_massage:amd64-latest


Local Development
-----------------

TODO: Remove the repo init from this document after you have done it.

TLDR:

- Create and activate a Python 3.8 virtualenv (assuming virtualenvwrapper)::

    mkvirtualenv -p `which python3.8` my_virtualenv

- Init your repo (first create it on-line and make note of the remote URI)::

    git init
    git add .
    git commit -m 'Cookiecutter stubs'
    git remote add origin MYREPOURI
    git push origin master

- change to a branch::

    git checkout -b my_branch

- install Poetry: https://python-poetry.org/docs/#installation
- Install project deps and pre-commit hooks::

    poetry install
    pre-commit install
    pre-commit run --all-files

- Ready to go, try the following::

    sensorserver_massage --defaultconfig >config.toml
    sensorserver_massage -vv config.toml

Remember to activate your virtualenv whenever working on the repo, this is needed
because pylint and mypy pre-commit hooks use the "system" python for now (because reasons).

Running "pre-commit run --all-files" and "py.test -v" regularly during development and
especially before committing will save you some headache.
