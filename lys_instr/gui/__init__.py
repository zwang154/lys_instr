from .DataStorage import DataStorageGUI
from .MultiMotor import MultiMotorGUI
from .Memory import ControllerMemory
from .MultiDetector import MultiDetectorGUI
from .PreCorrection import PreCorrectorGUI
#from .Scan import ScanWidget


def test():
    from .test_GUI import test_window
    return test_window()
