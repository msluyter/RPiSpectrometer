import unittest
from PIL import Image

from PicHelper import PicHelper
from Aperture import Aperture


class TestAperture(unittest.TestCase):

    def setUp(self):
        filename = 'tests/files/test_capture.jpg'
        img = Image.open(filename)
        pixels = img.load()
        self.pic_helper = PicHelper(pixels, img.size[0], img.size[1])
        self.aperture = Aperture(self.pic_helper)

    def test_find_brightest_x(self):
        expect_brightest_lux = 765
        expect_brightest_lux_x = 1044
        expect_hotspot_min_lux = 688

        self.aperture.find_brightest_x()
        with self.subTest():
            self.assertEqual(expect_brightest_lux, self.aperture.brightest_lux)

        with self.subTest():
            self.assertEqual(expect_brightest_lux_x, self.aperture.brightest_lux_x)

        with self.subTest():
            self.assertEqual(expect_hotspot_min_lux, self.aperture.hotspot_min_lux)

    def test_find_hotspot_horizontal_bound(self):
        self.aperture.find_brightest_x()

        brightest_lux_x_to_right = range(self.aperture.brightest_lux_x, self.aperture.pic.width)
        brightest_lux_x_to_center = range(self.aperture.brightest_lux_x, self.aperture.pic.midpoint_x, -1)

        hotspot_bound_left = self.aperture.find_hotspot_horizontal_bound(brightest_lux_x_to_center)
        hotspot_bound_right = self.aperture.find_hotspot_horizontal_bound(brightest_lux_x_to_right)

        expect_hotspot_bound_left = 1039
        expect_hotspot_bound_right = 1058

        with self.subTest():
            self.assertEqual(expect_hotspot_bound_left, hotspot_bound_left)

        with self.subTest():
            self.assertEqual(expect_hotspot_bound_right, hotspot_bound_right)

    @unittest.skip("Gives incorrect bound data. Need to fix.")
    def test_find_hotspot_vertical_bound(self):
        self.aperture.find_brightest_x()

        self.aperture.midpoint_x = 1048
        pic_midpoint_y_to_bottom = range(self.aperture.pic.midpoint_y, self.aperture.pic.height)
        pic_midpoint_y_to_top = range(self.aperture.pic.midpoint_y, 0, -1)

        # finding vertical bounds from horizontal hotspot midpoint
        hotspot_bound_top = self.aperture.find_hotspot_vertical_bound(pic_midpoint_y_to_top)
        hotspot_bound_bottom = self.aperture.find_hotspot_vertical_bound(pic_midpoint_y_to_bottom)

        expect_hotspot_bound_top = 551
        expect_hotspot_bound_bottom = 387

        with self.subTest():
            self.assertEqual(expect_hotspot_bound_top, hotspot_bound_top)

        with self.subTest():
            self.assertEqual(expect_hotspot_bound_bottom, hotspot_bound_bottom)

    def test_find_dimensions(self):
        aperture = Aperture.find_dimensions(self.pic_helper)

        with self.subTest():
            self.assertEqual(aperture.brightest_lux, 765)

        with self.subTest():
            self.assertEqual(aperture.brightest_lux_x, 1044)

        with self.subTest():
            self.assertEqual(aperture.hotspot_min_lux, 688)

        with self.subTest():
            self.assertEqual(aperture.midpoint_x, 1048)

        with self.subTest():
            self.assertEqual(aperture.midpoint_y, 469)

        with self.subTest():
            self.assertEqual(aperture.height, 164)


if __name__ == '__main__':
    unittest.main()