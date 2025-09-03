import numpy as np
import os

def sampleRamanData():
    # shape (11, 21, 36, 1000)
    path = os.path.join(os.path.dirname(__file__), "sampleRamanData.npy")
    data = np.load(path)
    return data