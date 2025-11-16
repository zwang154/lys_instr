
Detector
========

Creating a Detector Instance
----------------------------

A detector instance is created by subclassing ``MultiDetectorInterface``, which provides essential features for a multi-dimensional detector.

For real hardware, you should implement device-specific communication methods in your subclass as follows:

.. code-block:: python

    from lys_instr import MultiDetectorInterface

    class YourDetector(MultiDetectorInterface):       # Give a name to your subclass, e.g., ``YourDetector``

        def __init__(self, indexShape=(), frameShape=(), exposure=None, **kwargs):
            super().__init__(**kwargs)
            ... your code to establish connection and initialize the instruments ...
            self.exposure = exposure
            self.start()

        def _run(self, iter=1):
            ... your code to tell the instrument to trigger data acquisition ...

        def _get(self):
            ... your code to read the acquired data from the instrument ...
            return ... a dictionary with frame indices as keys and NumPy ndarrays of the acquired data as values ...

        def _stop(self):
            ... your code to tell the instrument to stop ongoing acquisition ...

        def _isAlive(self):
            ... your code to check if the detector is connected and functioning ...
            return ... True if alive, False if not ...

        @property
        def frameShape(self):
            ... your code to specify the shape of each data frame ...
            return ... a tuple of integers specifying the shape of each data frame ...

        @property
        def indexShape(self):
            ... your code to specify the shape of frame indices ...
            return ... a tuple of integers specifying the shape of frame indices ...

        @property
        def axes(self):
            ... your code to specify the physical axis values for each dimension ...
            return ... a list of arrays or lists, one for each axis, in the order [index axes..., frame axes...]
            # E.g., [listForIndexAxis1, listForIndexAxis2, ..., listForFrameAxis1, listForFrameAxis2, ...]


``frameShape`` specifies the shape of each frame (for example, ``(256, 256)`` for a 256×256 image). 
``indexShape`` specifies the shape of frame indices (for example, ``(10,)`` for 10 frames in a single run with indices 0 to 9).

For example, to acquire 10 images of size 256×256 while sweeping a motor over 10 steps, set ``indexShape=(10,)`` and ``frameShape=(256, 256)``.
If no indexing is needed, simply omit ``indexShape`` or set ``indexShape=()`` (that is, a single frame per run).

See :doc:`Detector GUI </lys_instr_/tutorial_/detectorGUI>` for displaying non-two-dimensional frames.


Step-by-Step Demonstration
--------------------------

Here we illustrate step-by-step construction of ``YourDetector`` for a dummy device that provides pre-encoded or synthetic data frames.

Subclass ``MultiDetectorInterface`` to create ``YourDetector``.
The data-supply logic is delegated to the ``setData()``, which keeps an internal buffer ``_data`` of acquired frames for use by other methods.

.. code-block:: python

    from lys_instr import MultiDetectorInterface

    class YourDetector(MultiDetectorInterface):

        def __init__(self, indexShape=(), frameShape=(), exposure=None, **kwargs):
            super().__init__(**kwargs)

            self.setData(indexShape=indexShape, frameShape=frameShape)
            self.error = False

            self.exposure = exposure
            self.start()

        def setData(self, data=None, indexShape=None, frameShape=None):
            if data is None:
                from lys_instr.dummy.MultiDetector import RandomData
                self._obj = RandomData(indexShape, frameShape)
            else:
                self._obj = data
            self._data = {}

By default, ``setData()`` generates random noise with the specified ``indexShape`` and ``frameShape``. 
It can also load pre-encoded frames via the GUI by user selection. 
For real hardware, the details of the dummy data generation logic can be ignored.

Implement ``_run()`` to sequentially fetch or generate frames, populate ``_data`` for respective indices, emit ``updated`` signal after each frame, and check ``_shouldStop`` to allow cancellation.

.. code-block:: python

        def _run(self, iter=1):
            self._shouldStop = False
            
            i = 0
            while i != iter:
                for idx, data in self._obj:
                    if self._shouldStop:
                        return
                    import time
                    time.sleep(self.exposure * self._obj.nframes)
                    self._data[idx] = data
                    self.updated.emit()
                i += 1

Implement ``_stop()`` to request acquisition cancellation by setting a flag checked by ``_run()``.

.. code-block:: python

        def _stop(self):
            self._shouldStop = True

Implement ``_get()`` to return the acquired frames in ``_data`` and clear the buffer afterward.

.. code-block:: python

        def _get(self):
            data = self._data.copy()
            self._data.clear()
            return data

Implement ``_isAlive()`` to report the connection status of the device, here managed by an internal ``error`` flag.

.. code-block:: python

        def _isAlive(self):
            return not self.error

Implement ``frameShape``, ``indexShape``, and ``axes`` properties to return the corresponding attributes set in ``__init__()``.
(In this example, the properties delegate to the dummy-data object ``self._obj`` (a ``RandomData`` instance); you can instead implement them explicitly as needed.)

.. code-block:: python

        @property
        def frameShape(self):
            return self._obj.frameShape

        @property
        def indexShape(self):
            return self._obj.indexShape

        @property
        def axes(self):
            return self._obj.axes

Optionally, implement ``settingsWidget`` to return a *QWidget* for later use by GUI.
The ``_OptionalPanel`` class in the ``lys_instr.dummy.MultiDetector`` module can readily be used.

.. code-block:: python

        def settingsWidget(self):
            from lys_instr.dummy.MultiDetector import _OptionalPanel
            return _OptionalPanel(self)

The class constructed above is actually the ``MultiDetectorDummy`` class provided in the ``lys_instr.dummy`` module.


Checking Operations
-------------------

To verify functionality, instantiate your detector class, for example, ``YourDetector``.
(Import it if defined in a separate module.)

.. code-block:: python

    detector = YourDetector(... your parameters ...)

For demonstration, we use the ``YourDetector`` class defined above with ``indexShape=()``, ``frameShape=(256, 256)``, and 0.1 seconds exposure time:

.. code-block:: python

    detector = YourDetector(frameShape=(256, 256), exposure=0.1)

This is functionally equivalent to instantiating the provided ``MultiDetectorDummy`` class:

.. code-block:: python

    from lys_instr import dummy

    detector = dummy.MultiDetectorDummy(frameShape=(256, 256))

Now, you can use the ``startAcq()``, ``stop()``, ``isBusy()``, and ``isAlive()`` methods provided by ``MultiDetectorInterface`` to confirm that the detector is functioning correctly.
For example:

.. code-block:: python

    import time

    data = detector.startAcq(wait=True, output=True)   # Start acquisition of 1 frame
    print(data)     # Returns a dictionary, e.g., {(): array([[0.1, 0.2, ...], [...], ...])}
