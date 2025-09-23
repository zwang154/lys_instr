
Detector Options
================

Creating Indexed Detector GUI
-----------------------------

When a detector captures multiple frames per acquisition, the data shape becomes more complex.
For example, with an (8, 8) array of frames, each sized 256×256, the index shape, frame shape, and full data shape are ``(8, 8)``, ``(256, 256)``, and ``(8, 8, 256, 256)``, respectively.

Users can create custom detector GUIs to display multiple views of the data as needed.
The ``MultiDetectorGUI_Opt`` class (:class:`.gui.MultiDetectorOpt.MultiDetectorGUI_Opt`), inherited from ``MultiDetectorGUI``, provides an example that shows frame updates as one image and displays indexed data calculated from each frame, such as the mean, as another.

.. code-block:: python

    import sys
    from lys_instr import gui, dummy

    app = QtWidgets.QApplication(sys.argv)
    detector = dummy.MultiDetectorDummy(indexShape=(8, 8), frameShape=(256, 256), exposure=0.1)
    gui = gui.MultiDetectorGUI_Opt(detector)
    gui.show()
    sys.exit(app.exec_())

Running the above code launches the example GUI:

.. image:: /lys_instr_/tutorial_/detectorOptions_1.png
    :scale: 80%


*lys* Integration
-----------------

The detector GUI can be integrated with *lys* for seamless data acquisition, display, and analysis workflows.

For demonstration, we show the following code with a few lines of *lys* configuration to allow live display of the mean over selected axes of one image in another.

.. code-block:: python

    from lys.widgets import LysSubWindow
    from lys_instr import gui, dummy

    class AppWindow(LysSubWindow):
        def __init__(self):
            super().__init__()
            detector = dummy.MultiDetectorDummy(indexShape=(8, 8), frameShape=(256, 256), exposure=0.1)
            detectorGUI = gui.MultiDetectorGUI(detector)

            mcut = detectorGUI._mcut
            wave1 = mcut.cui._children.addWave([0, 1])
            canvas1 = mcut.display(wave1, type="grid", pos=(0, 0), wid=(4, 2))
            wave2 = mcut.cui._children.addWave([2, 3])
            canvas2 = mcut.display(wave2, type="grid", pos=(0, 2), wid=(4, 2))
            mcut._can.addRect(canvas1)
            rect = canvas1.getRectAnnotations()[0]
            rect.setRegion([[0.4, 0.6], [0.4, 0.6]])
            canvas1.update()

            self.setWidget(detectorGUI)
            self.adjustSize()

Adding the above code to ``proc.py`` in *lys* and calling ``AppWindow()`` from the *lys* command line will display the following GUI:

.. image:: /lys_instr_/tutorial_/detectorOptions_2.png

Alternatively, one can launch the GUI without the ``mcut`` setup lines and manually configure the display in the "MultiCut" tab (see `lys documentation <https://lys-devel.github.io/lys/>`_ for detailed tutorials).

Now, the image on the left displays the "indexed image" (8×8), where each pixel represents the mean value of its corresponding frame (256×256).
The image on the right shows the meaned frame of the region selected by the rectangle annotation in the left image.

The user can refer to the Advanced Examples in :doc:`Advanced Examples </lys_instr_/tutorial_/advancedExamples>` for more integrated and intuitive application scenarios.

