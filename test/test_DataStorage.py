import unittest
import time
import os
import tempfile
import numpy as np

from PyQt5 import QtTest
from lys_instr.DataStorage import DataStorage


class TestDataStorage(unittest.TestCase):

    def test_init(self):
        storage = DataStorage()
        self.assertEqual(storage.base, ".", "Default base directory should be '.'.")
        self.assertEqual(storage.folder, "folder", "Default folder should be 'folder'.")
        self.assertEqual(storage.name, "data", "Default name should be 'data'.")
        self.assertTrue(storage.enabled, "Storage should be enabled by default.")
        self.assertTrue(storage.numbered, "Storage should use numbering by default.")

    def test_getNumber(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = DataStorage()
            storage.base = tmpdir
            storage.folder = "newFolder"
            storage.name = "newName"
            n1 = storage.getNumber()
            storage.reserve(shape=(2, 2, 2, 2))
            n2 = storage.getNumber()
            self.assertEqual(n2, n1 + 1, "getNumber should increment after reserving a file.")

    def test_enabled_false(self):
        storage = DataStorage()
        storage.enabled = False
        storage.reserve(shape=(2, 2, 2, 2))
        self.assertIsNone(storage._arr, "No array should be reserved when storage is disabled.")

    def test_numbered_false(self):
        storage = DataStorage()
        storage.numbered = False
        n = storage.getNumber()
        self.assertIsNone(n, "getNumber should return None when numbering is disabled.")

    def test_reserve_update_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = DataStorage()
            storage.base = tmpdir
            storage.folder = "newFolder"
            storage.name = "newName"

            n = storage.getNumber()
            storage.reserve(shape=(2, 2, 2, 2), fillValue=5)
            data = {(0, 0): np.ones((2, 2))}
            storage.update(data)
            axes = [np.arange(2), np.arange(2), np.arange(2), np.arange(2)]
            arrSaving = storage._arr
            storage.save(axes)
            self.assertTrue(storage.saving, "Storage should be saving after save() is called.")

            timeout = 5  # seconds
            start = time.time()
            while storage.saving and (time.time() - start < timeout):
                QtTest.QTest.qWait(10)
            self.assertFalse(storage.saving, "Save thread did not finish in time.")

            folder = os.path.join(storage.base, storage.folder)
            expectedFile = os.path.join(folder, f"{storage.name}_{n}.npz")
            self.assertTrue(os.path.exists(expectedFile), f"Expected file {expectedFile} does not exist.")

            with np.load(expectedFile) as npz:
                arr_keys = npz.files
                self.assertTrue(len(arr_keys) > 0, "No arrays found in saved file.")
                arrFromFile = npz[arr_keys[0]]
                self.assertTrue(np.array_equal(arrFromFile, arrSaving), "Saved array does not match the storage buffer.")
