import unittest
from PIL import Image

from PicHelper import PicHelper


class TestPicHelper(unittest.TestCase):

    def setUp(self):
        filename = 'tests/files/test_capture.jpg'
        img = Image.open(filename)
        pixels = img.load()
        self.pic_helper = PicHelper(pixels, img.size[0], img.size[1])

    def test_pixel_lux(self):
        test_input_list = [
            {'x': 0, 'y': 0, 'expect': 0},
            {'x': 1048, 'y': 469, 'expect': 765}
        ]
        for test_input in test_input_list:
            with self.subTest(test_input=test_input):
                actual = self.pic_helper.pixel_lux(test_input['x'], test_input['y'])
                expect = test_input['expect']
                self.assertEqual(expect, actual)


if __name__ == '__main__':
    unittest.main()