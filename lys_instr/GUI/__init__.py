from .DataStorage import DataStorageGUI
from .MultiMotor import MultiMotorGUI
from .MultiDetector import MultiDetectorGUI
from .Scan import ScanWidget



def test():
    from .test_GUI import test_window
    return test_window()
