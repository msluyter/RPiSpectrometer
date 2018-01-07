class Aperture:

    DIMMING_CONSTANT = 0.9
    HEIGHT_REDUCTION_CONSTANT = 0.9

    def __init__(self, pic_helper, brightest_lux=0, brightest_lux_x=0, min_lux=0, midpoint_x=0, midpoint_y=0,
                 height=0):
        """
        Constructor

        :param pic_helper: The PicHelper class
        """

        self.pic = pic_helper

        # Set with find_brightest_x()
        self.brightest_lux = brightest_lux
        self.brightest_lux_x = brightest_lux_x
        self.hotspot_min_lux = min_lux

        # Set with find_aperture_dimensions()
        self.midpoint_x = midpoint_x
        self.midpoint_y = midpoint_y
        self.height = height

    # factory
    @classmethod
    def find_dimensions(cls, pic_helper):
        aperture = cls(pic_helper)

        # Find brightest pixel in right side of the image along the vertical midpoint of the image
        aperture.find_brightest_x()

        # find horizontal bounds
        brightest_lux_x_to_right = range(aperture.brightest_lux_x, aperture.pic.width)
        brightest_lux_x_to_center = range(aperture.brightest_lux_x, aperture.pic.midpoint_x, -1)
        hotspot_bound_left = aperture.find_hotspot_horizontal_bound(brightest_lux_x_to_center)
        hotspot_bound_right = aperture.find_hotspot_horizontal_bound(brightest_lux_x_to_right)

        # find horizontal midpoint of aperture
        aperture.midpoint_x = (hotspot_bound_left + hotspot_bound_right) // 2

        # find vertical bounds from horizontal hotspot midpoint
        pic_midpoint_y_to_bottom = range(aperture.pic.midpoint_y, aperture.pic.height)
        pic_midpoint_y_to_top = range(aperture.pic.midpoint_y, 0, -1)
        hotspot_bound_top = aperture.find_hotspot_vertical_bound(pic_midpoint_y_to_top)
        hotspot_bound_bottom = aperture.find_hotspot_vertical_bound(pic_midpoint_y_to_bottom)

        # find midpoint between vertical bounds and height of hotspot
        aperture.midpoint_y = (hotspot_bound_top + hotspot_bound_bottom) // 2
        aperture.height = abs(int((hotspot_bound_top - hotspot_bound_bottom) * aperture.HEIGHT_REDUCTION_CONSTANT))

        return aperture

    def find_brightest_x(self):
        """
        Find the brightest pixel on the X axis
        """
        for x in range(self.pic.midpoint_x, self.pic.width, 1):
            lux = self.pic.pixel_lux(x, self.pic.midpoint_y)
            if lux > self.brightest_lux:
                self.brightest_lux = lux
                self.brightest_lux_x = x
        self.hotspot_min_lux = int(self.brightest_lux * self.DIMMING_CONSTANT)

    def find_hotspot_horizontal_bound(self, the_range: range) -> int:
        """
        Find the horizontal bounds of a hotspot

        :param the_range: A range that traverses pixels from the brightest_lux to another location on the X axis

        :return: Location where lux drops below hotspot_min_lux
        """
        for x in the_range:
            lux = self.pic.pixel_lux(x, self.pic.midpoint_y)
            if self.hotspot_min_lux > lux:
                return x
        return self.brightest_lux_x

    def find_hotspot_vertical_bound(self, the_range: range) -> int:
        """
        Find the vertical bounds of the hotspot with a falloff tolerance of max_count

        :param the_range: A range that traverses pixels from the midpoint_y to another location on the Y axis

        :return: Location on Y axis where lux drops below hotspot_min_lux
        """
        gap_pixel_count = 0
        max_gap_height = 64
        vertical_bound = self.pic.midpoint_y
        for y in the_range:
            lux = self.pic.pixel_lux(self.midpoint_x, y)
            if self.hotspot_min_lux > lux:
                gap_pixel_count += 1
                if gap_pixel_count > max_gap_height:
                    break
            else:
                vertical_bound = y
        return vertical_bound
