
Detector
========

Creating a Detector Instance
----------------------------

A detector instance is created by subclassing ``MultiDetectorInterface``, which provides essential features for a multi-dimensional detector.

For real hardware, you should implement device-specific communication methods in your subclass as follows:

.. code-block:: python

    class YourDetector(MultiDetectorInterface):       # Give a name to your subclass, e.g., ``YourDetector``

        def __init__(self, indexShape=(), frameShape=(), exposure=None, **kwargs):
            super().__init__(**kwargs)
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
        def axes(self):
            ... your code to specify the physical axis values for each dimension ...
            return ... a list of arrays or lists, one for each axis, in the order [index axes..., frame axes...]
            # E.g., [listForIndexAxis1, listForIndexAxis2, ..., listForFrameAxis1, listForFrameAxis2, ...]


``frameShape`` specifies the shape of each frame (for example, ``(256, 256)`` for a 256×256 image). 
``indexShape`` specifies the shape of frame indices (for example, ``(10,)`` for 10 frames in a single run with indices 0 to 9).

For example, to acquire 10 images of size 256×256 while sweeping a motor over 10 steps, set ``indexShape=(10,)`` and ``frameShape=(256, 256)``.
If no indexing is needed, simply omit ``indexShape`` or set ``indexShape=()`` (that is, a single frame per run).

See :doc:`Detector GUI </lys_instr_/tutorial_/detectorGUI>` for displaying non-two-dimensional frames.


Checking Operations
-------------------

To verify functionality, use your own detector class (for example, ``YourDetector``).

.. code-block:: python

    detector = YourDetector(... your parameters ...)

For demonstration, we use the dummy detector ``MultiDetectorDummy`` with ``indexShape=()`` and ``frameShape=(256, 256)`` to simulate detector behavior without real hardware.

.. code-block:: python

    from lys_instr import dummy

    detector = dummy.MultiDetectorDummy(frameShape=(256, 256))

You can use the ``startAcq()``, ``stop()``, ``isBusy()``, and ``isAlive()`` methods provided by ``MultiDetectorInterface`` to confirm that the detector is functioning correctly.
For example:

.. code-block:: python

    data = detector.startAcq(wait=True, output=True)   # Start acquisition of 1 frame
    print(data)     # Returns a dictionary, e.g., {(0,): array([[0.1, 0.2, ...], [...], ...])}

