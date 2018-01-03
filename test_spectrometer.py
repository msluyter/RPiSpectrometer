import unittest
from PIL import Image
from spectrometer import PicHelper


# x=1048, y=469, b=765
class TestPicHelper(unittest.TestCase):

    def setUp(self):
        filename = 'tests/files/test_capture.jpg'
        img = Image.open(filename)
        pixels = img.load()
        self.pic_helper = PicHelper(pixels)

    def test_pixel_lux(self):
        test_input = [
            {'x': 0, 'y': 0, 'expect': 0},
            {'x': 1048, 'y': 469, 'expect': 765}
        ]
        for i in test_input:
            with self.subTest(i=i):
                actual = self.pic_helper.pixel_lux(test_input[i]['x'], test_input[i]['y'])
                expect = test_input[i]['expect']
                self.assertEqual(expect, actual)

    def tearDown(self):
        self.pic_helper.dispose()


if __name__ == '__main__':
    unittest.main()