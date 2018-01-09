from collections import namedtuple


Aperture = namedtuple('Aperture', ['brightest_lux', 'brightest_lux_x', 'hotspot_min_lux', 'midpoint_x', 'midpoint_y', 'height'])


# def find_dimensions(pic_helper):

DIMMING_CONSTANT = .9


def find_brightest_x(pic_helper, brightest_lux):
    """
    Find the brightest pixel on the X axis
    """
    brightest_lux_x = 0
    for x in range(pic_helper.midpoint_x, pic_helper.width, 1):
        lux = pic_helper.pixel_lux(x, pic_helper.midpoint_y)
        if lux > brightest_lux:
            brightest_lux = lux
            brightest_lux_x = x

    hotspot_min_lux = int(brightest_lux * DIMMING_CONSTANT)

    return brightest_lux_x, hotspot_min_lux



def find_hotspot_vertical_bound(pic_helper, hotspot_min_lux, aperture_midpoint_x, the_range: range) -> int:
    """
    Find the vertical bounds of the hotspot with a falloff tolerance of max_count

    :param the_range: A range that traverses pixels from the midpoint_y to another location on the Y axis

    :return: Location on Y axis where lux drops below hotspot_min_lux
    """
    gap_pixel_count = 0
    max_gap_height = 64
    vertical_bound = pic_helper.midpoint_y
    for y in the_range:
        lux = pic_helper.pixel_lux(aperture_midpoint_x, y)
        if hotspot_min_lux > lux:
            gap_pixel_count += 1
            if gap_pixel_count > max_gap_height:
                break
        else:
            vertical_bound = y
    return vertical_bound

def foo():
    N = 10
    # O(n^2)
    for i in range(N/2):
        for j in range(N/2):
            print(f"{i} - {j}")



