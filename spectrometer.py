import logging
import sys
import math
import time
import picamera
from fractions import Fraction
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFile, ImageFont


LOGGER = logging.getLogger(__name__)


class PicHelper:
    # pixels is of type PixelAccess, how do I hint that here?
    def __init__(self, pixels, pic_width: int, pic_height: int, *, brightest_lux=0, aperture_height=0):
        """
        Constructor

        :param pixels: The return value of Image.load()
        :param pic_width: Width of the image in pixels
        :param pic_height: Height of the image in pixels
        """
        self.pixels = pixels
        self.width = pic_width
        self.height = pic_height
        self.midpoint_x = pic_width // 2
        self.midpoint_y = pic_height // 2

    def pixel_lux(self, x: int, y: int) -> int:
        """
        Find the brightness of a pixel

        :param x: The location of the pixel on the X axis
        :param y: The location of the pixel on the Y axis

        :return: The brightness of the pixel
        """
        r, g, b = self.pixels[x, y]
        return r + g + b


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
        a = Aperture(pic_helper)

        # Find brightest pixel in right side of the image along the vertical midpoint of the image
        a.find_brightest_x()

        # Setup ranges to find hotspot bounds
        brightest_lux_x_to_right = range(a.brightest_lux_x, a.pic.width)
        brightest_lux_x_to_center = range(a.brightest_lux_x, a.pic.midpoint_x, -1)
        pic_midpoint_y_to_bottom = range(a.pic.midpoint_y, a.pic.height)
        pic_midpoint_y_to_top = range(a.pic.midpoint_y, 0, -1)

        # finding horizontal bounds
        hotspot_bound_left = a.find_hotspot_horizontal_bound(brightest_lux_x_to_center)
        hotspot_bound_right = a.find_hotspot_horizontal_bound(brightest_lux_x_to_right)

        # finding horizontal midpoint of aperture
        a.aperture_midpoint_x = (hotspot_bound_left + hotspot_bound_right) // 2

        # finding vertical bounds from horizontal hotspot midpoint
        hotspot_bound_top = a.find_hotspot_vertical_bound(pic_midpoint_y_to_top)
        hotspot_bound_bottom = a.find_hotspot_vertical_bound(pic_midpoint_y_to_bottom)

        # finding midpoint between vertical bounds and height of hotspot
        a.aperture_midpoint_y = (hotspot_bound_top + hotspot_bound_bottom) // 2
        a.aperture_height = int((hotspot_bound_top - hotspot_bound_bottom) * a.HEIGHT_REDUCTION_CONSTANT)

        return a


    def find_brightest_x(self):
        """
        Find the brightest pixel on the X axis
        """
        for x in range(self.pic.midpoint_x, self.pic.width, 1):
            lux = self.pic.pixel_lux(x, self.pic.midpoint_y)
            if lux > self.brightest_lux:
                self.brightest_lux = lux
                self.brightest_lux_x = x
        self.hotspot_min_lux = self.brightest_lux * self.DIMMING_CONSTANT

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


def draw_vertical_aperture_midpoint_line(aperture, draw):
    fill_color = "#000"
    aperture_top_y = aperture.midpoint_y + aperture.height // 2
    aperture_bottom_y = aperture.midpoint_y - aperture.height // 2
    draw.line((aperture.midpoint_x, aperture_top_y, aperture.midpoint_x, aperture_bottom_y), fill=fill_color)


# draw scan line
def draw_scan_line(aperture, draw, spectrum_angle):
    fill_color = "#888"
    xd = aperture['x']
    h = aperture['h'] / 2
    y0 = math.tan(spectrum_angle) * xd + aperture['y']
    draw.line((0, y0 - h, aperture['x'], aperture['y'] - h), fill=fill_color)
    draw.line((0, y0 + h, aperture['x'], aperture['y'] + h), fill=fill_color)


# return an RGB visual representation of wavelength for chart
# Based on: http://www.efg2.com/Lab/ScienceAndEngineering/Spectra.htm
# The foregoing is based on: http://www.midnightkite.com/color.html
# thresholds = [ 380, 440, 490, 510, 580, 645, 780 ]
#                vio  blu  cyn  gre  yel  org  red
def wavelength_to_color(lambda2):
    factor = 0.0
    color = [0, 0, 0]
    thresholds = [380, 400, 450, 465, 520, 565, 780]
    for i in range(0, len(thresholds) - 1, 1):
        t1 = thresholds[i]
        t2 = thresholds[i + 1]
        if lambda2 < t1 or lambda2 >= t2:
            continue
        if i % 2 != 0:
            tmp = t1
            t1 = t2
            t2 = tmp
        if i < 5:
            color[i % 3] = (lambda2 - t2) / (t1 - t2)
        color[2 - int(i / 2)] = 1.0
        factor = 1.0
        break

    # Let the intensity fall off near the vision limits
    if 380 <= lambda2 < 420:
        factor = 0.2 + 0.8 * (lambda2 - 380) / (420 - 380)
    elif 600 <= lambda2 < 780:
        factor = 0.2 + 0.8 * (780 - lambda2) / (780 - 600)
    return int(255 * color[0] * factor), int(255 * color[1] * factor), int(255 * color[2] * factor)


def take_picture(camera, name, shutter_speed):
    camera.vflip = True
    camera.framerate = Fraction(1, 6)
    camera.shutter_speed = shutter_speed
    camera.iso = 100
    camera.exposure_mode = 'off'
    camera.awb_mode = 'off'
    camera.awb_gains = (1, 1)

    # Why is this sleeping?
    time.sleep(3)

    raw_filename = name + "_raw.jpg"
    camera.capture(raw_filename, resize=(1296, 972))
    return raw_filename


def draw_graph(draw, pic_pixels, aperture, spectrum_angle, wavelength_factor, font_location):
    aperture_height = aperture['h'] / 2
    step = 1
    last_graph_y = 0
    max_result = 0
    results = OrderedDict()
    for x in range(0, int(aperture['x'] * 7 / 8), step):
        wavelength = (aperture['x'] - x) * wavelength_factor
        if 1000 < wavelength or wavelength < 380:
            continue

        # general efficiency curve of 1000/mm grating
        eff = (800 - (wavelength - 250)) / 800
        if eff < 0.3:
            eff = 0.3

        # notch near yellow maybe caused by camera sensitivity
        mid = 575
        width = 10
        if (mid - width) < wavelength < (mid + width):
            d = (width - abs(wavelength - mid)) / width
            eff = eff * (1 - d * 0.1)

        # up notch near 590
        mid = 588
        width = 10
        if (mid - width) < wavelength < (mid + width):
            d = (width - abs(wavelength - mid)) / width
            eff = eff * (1 + d * 0.1)

        y0 = math.tan(spectrum_angle) * (aperture['x'] - x) + aperture['y']
        amplitude = 0
        ac = 0.0
        for y in range(int(y0 - aperture_height), int(y0 + aperture_height), 1):
            r, g, b = pic_pixels[x, y]
            q = r + b + g * 2
            if y < (y0 - aperture_height + 2) or y > (y0 + aperture_height - 3):
                q = q * 0.5
            amplitude = amplitude + q
            ac = ac + 1.0
        amplitude = amplitude / ac / eff
        # amplitude=1/eff
        results[str(wavelength)] = amplitude
        if amplitude > max_result:
            max_result = amplitude
        graph_y = amplitude / 50 * aperture_height
        draw.line((x - step, y0 + aperture_height - last_graph_y, x, y0 + aperture_height - graph_y), fill="#fff")
        last_graph_y = graph_y
    draw_ticks_and_frequencies(draw, aperture, spectrum_angle, wavelength_factor, font_location)
    return results, max_result


def draw_ticks_and_frequencies(draw, aperture, spectrum_angle, wavelength_factor, font_location):
    aperture_height = aperture['h'] / 2
    for wl in range(400, 1001, 50):
        x = aperture['x'] - (wl / wavelength_factor)
        y0 = math.tan(spectrum_angle) * (aperture['x'] - x) + aperture['y']
        draw.line((x, y0 + aperture_height + 5, x, y0 + aperture_height - 5), fill="#fff")
        font = ImageFont.truetype(font_location, 12)
        draw.text((x, y0 + aperture_height + 15), str(wl), font=font, fill="#fff")


def inform_user_of_exposure(max_result):
    exposure = max_result / (255 + 255 + 255)
    print("ideal exposure between 0.15 and 0.30")
    print("exposure=", exposure)
    if exposure < 0.15:
        print("consider increasing shutter time")
    elif exposure > 0.3:
        print("consider reducing shutter time")


def save_image_with_overlay(im, name):
    output_filename = name + "_out.jpg"
    ImageFile.MAXBLOCK = 2 ** 20
    im.save(output_filename, "JPEG", quality=80, optimize=True, progressive=True)


def normalize_results(results, max_result):
    for wavelength in results:
        results[wavelength] = results[wavelength] / max_result
    return results


def export_csv(name, normalized_results):
    csv_filename = name + ".csv"
    csv = open(csv_filename, 'w')
    csv.write("wavelength,amplitude\n")
    for wavelength in normalized_results:
        csv.write(wavelength)
        csv.write(",")
        csv.write("{:0.3f}".format(normalized_results[wavelength]))
        csv.write("\n")
    csv.close()


def export_diagram(name, normalized_results, font_location):
    antialias = 4
    w = 600 * antialias
    h2 = 300 * antialias

    h = h2 - 20 * antialias
    sd = Image.new('RGB', (w, h2), (255, 255, 255))
    draw = ImageDraw.Draw(sd)

    w1 = 380.0
    w2 = 780.0
    f1 = 1.0 / w1
    f2 = 1.0 / w2
    for x in range(0, w, 1):
        # Iterate across frequencies, not wavelengths
        lambda2 = 1.0 / (f1 - (float(x) / float(w) * (f1 - f2)))
        c = wavelength_to_color(lambda2)
        draw.line((x, 0, x, h), fill=c)

    pl = [(w, 0), (w, h)]
    for wavelength in normalized_results:
        wl = float(wavelength)
        x = int((wl - w1) / (w2 - w1) * w)
        # print wavelength,x
        pl.append((int(x), int((1 - normalized_results[wavelength]) * h)))
    pl.append((0, h))
    pl.append((0, 0))
    draw.polygon(pl, fill="#FFF")
    draw.polygon(pl)

    font = ImageFont.truetype(font_location, 12 * antialias)
    draw.line((0, h, w, h), fill="#000", width=antialias)

    for wl in range(400, 1001, 10):
        x = int((float(wl) - w1) / (w2 - w1) * w)
        draw.line((x, h, x, h + 3 * antialias), fill="#000", width=antialias)

    for wl in range(400, 1001, 50):
        x = int((float(wl) - w1) / (w2 - w1) * w)
        draw.line((x, h, x, h + 5 * antialias), fill="#000", width=antialias)
        wls = str(wl)
        tx = draw.textsize(wls, font=font)
        draw.text((x - tx[0] / 2, h + 5 * antialias), wls, font=font, fill="#000")

    # save chart
    sd = sd.resize((int(w / antialias), int(h / antialias)), Image.ANTIALIAS)
    output_filename = name + "_chart.png"
    sd.save(output_filename, "PNG", quality=95, optimize=True, progressive=True)


def main():
    # 1. Take picture
    camera = picamera.PiCamera()
    name = str(sys.argv[1])
    shutter_speed = int(sys.argv[2])
    raw_filename = take_picture(camera, name, shutter_speed)
    im = Image.open(raw_filename)

    # 2. Get picture's aperture
    pic_pixels = im.load()
    pic_helper = PicHelper(pic_pixels, im.size[0], im.size[1])
    aperture = Aperture.find_dimensions(pic_helper)
    aperture_dict = {'x': aperture.midpoint_x, 'y': aperture.midpoint_y, 'h': aperture.height,
                     'b': aperture.brightest_lux}  # get rid of this dict asap

    # 3. Draw aperture and scan line
    font_location = '/usr/share/fonts/truetype/lato/Lato-Regular.ttf'
    spectrum_angle = 0.03
    draw = ImageDraw.Draw(im)
    draw_vertical_aperture_midpoint_line(aperture, draw)
    draw_scan_line(aperture_dict, draw, spectrum_angle)

    # 4. Draw graph on picture
    wavelength_factor = 0.892  # 1000/mm
    # wavelength_factor=0.892*2.0*600/650 # 500/mm
    results, max_result = draw_graph(draw, pic_pixels, aperture_dict, spectrum_angle, wavelength_factor,
                                     font_location)

    # 5. Inform user of issues with exposure
    inform_user_of_exposure(max_result)

    # 6. Save picture with overlay
    save_image_with_overlay(im, name)

    # 7. Normalize results for export
    normalized_results = normalize_results(results, max_result)

    # 8. Save csv of results
    export_csv(name, normalized_results)

    # 9. Generate spectrum diagram
    export_diagram(name, normalized_results, font_location)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )
    main()
