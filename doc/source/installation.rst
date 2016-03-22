
Installation
=============

There are several ways to install HyperSpyUI. The application itself is rather
simple to install, but its dependencies can be a bit more tricky.

Bundle Installer
-----------------

If you're on Windows, the quickest way to get set up is to download and install
the HyperSpyUI bundle installer. The bundled WinPython_ distribution includes
all the dependencies of the program, and the installer also helps create
program shortucts and register common microscopy file formats with the
application.

The bundle installer can also be used if you already have installed a WinPython
distribution (e.g. via the `HyperSpy bundle`_), and just want to add HyperSpyUI
and its dependencies, although it might not support older versions.

.. _WinPython: http://winpython.github.io/
.. _HyperSpy bundle: http://hyperspy.org/download.html


Install via `pip`
-----------------

HyperSpyUI is on PyPI_, so simply running the command ``pip install hyperspyui``
should download and install HyperSpyUI and its dependencies. The package defines
a GUI script ``hyperspyui``, which can be called to start the application, or
alternatively it can be started by running ``python -m hyperspyui.launch``.

To get HyperSpyUI to integrate with your operating system after installation,
you can run the script ``hyperspyui_install.py``. Currently, this only
integrates with Windows, but this is intended to be extend to Linux systems
in the future (please consider contributing).

.. _PyPI: https://pypi.python.org/pypi/hyperspyui/


HyperSpy version dependency
"""""""""""""""""""""""""""
HyperSpyUI currently depends on the development version of HyperSpy for much of
its functionallity. To install the development version, run the following
command::

    pip install https://github.com/hyperspy/hyperspy/archive/master.zip


Getting Qt
""""""""""
Getting and installing Qt_ might or might not be easy, depending on which
operating system you are on. For this reason, it is recommended to run
HyperSpyUI on a distribution which offers ready-made Qt packages. Examples
include WinPython_, Conda_ and Canopy_.

.. _Conda: https://github.com/conda/conda
.. _Canopy:

.. _Qt: http://www.qt.io/
