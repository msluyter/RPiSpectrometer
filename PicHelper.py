class PicHelper:
    # pixels is of type PixelAccess, how do I hint that here?
    def __init__(self, pixels, pic_width: int, pic_height: int):
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
