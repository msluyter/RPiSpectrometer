import unittest
from PIL import Image

from PicHelper import PicHelper
from Aperture import Aperture
from msluyter_refactor import find_hotspot_vertical_bound
from unittest.mock import MagicMock

class TestMsluyterRefactor(unittest.TestCase):
    def setUp(self):
        filename = 'tests/files/test_capture.jpg'
        img = Image.open(filename)
        pixels = img.load()
        self.pic_helper = PicHelper(pixels, img.size[0], img.size[1])

    def test_find_hotspot_vertical_bound(self):
        # m.return_value = (255, 255, 255)

        bound = find_hotspot_vertical_bound(self.pic_helper, 1, 5, range(5,9))
        print(bound)
