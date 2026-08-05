"""
仕様
・Scanner.startでスキャンが開始されること
・スキャン中はisBusyがTrue、終了後はFalseになること
・Scanner.stopでスキャンが停止されること
・プロセスで指定した位置に正しく移動すること
・複数階層のスキャンが正しく実行可能であること
・ファイル名が正しく反映されていること（delayスイッチのような特殊なケースでも正しくindexが反映されていること）
・完了したら必要なデータが正しく保存されていること（exposureや移動速度が極端に速い場合でも）
・スキャンが完了した場合はfinishedシグナル、stopした場合はstoppedシグナルが発行されること
・スキャンはstartしたスレッドとは別のスレッドで動くこと

・ScanRowのテスト
　・scanName, scanObj, scanRange, scanIndexが正しく取得できること
　・setCounterでcounterが正しく設定できること
"""

import unittest
import time
import os
import tempfile
import numpy as np

from PyQt5 import QtTest

class TestMultiScan(unittest.TestCase):
    def test_init(self):
        """
        Test that the MultiScan object is initialized correctly.
        """
        pass