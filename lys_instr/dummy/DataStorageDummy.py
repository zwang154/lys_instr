import h5py
import zarr
import logging
from lys_instr.DataStorage import DataStorageInterface

# logging.basicConfig(level=logging.INFO)


class DataStorageDummy(DataStorageInterface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _write(self, data, path=None, type=None):
        if not path or not type:
            logging.error("Path or type not set for writing.")
            return

        if type == 'hdf5':
            with h5py.File(path, 'a') as f:
                for idx, frame in data.items():
                    key = str(idx)
                    if key in f:
                        del f[key]
                    f.create_dataset(key, data=frame)
            logging.info(f"Data saved in {path}")
        elif type == 'zarr':
            root = zarr.open(path, mode='a')
            for idx, frame in data.items():
                key = str(idx)
                root[key] = frame
            logging.info(f"Data saved in {path}")
        else:
            logging.error(f"Unsupported save type: {type}")
            return

    def _read(self, path=None, type=None, keys=None):
        data = {}
        if type == "hdf5":
            with h5py.File(path, 'r') as f:
                allKeys = list(f.keys())
                selectedKeys = [str(k) for k in keys] if keys is not None else allKeys
                for key in selectedKeys:
                    if key in f:
                        data[key] = f[key][()]
        elif type == "zarr":
            root = zarr.open(path, mode='r')
            allKeys = list(root.keys())
            selectedKeys = [str(k) for k in keys] if keys is not None else allKeys
            for key in selectedKeys:
                if key in root:
                    data[key] = root[key][()]
        else:
            logging.error(f"Unsupported file type: {type}")
            return {}
        return data
