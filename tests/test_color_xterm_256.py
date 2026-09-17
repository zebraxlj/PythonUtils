import pytest

from ColorHelper.color_xterm_256 import BASIC_RGB, CUBE_LEVELS, ColorXTerm256


class TestPalette:
    def test_member_count(self):
        assert len(ColorXTerm256) == 256

    def test_basic_names(self):
        assert ColorXTerm256.BLACK.value == 0
        assert ColorXTerm256.BRIGHT_WHITE.value == 15

    def test_cube_first_and_last(self):
        assert ColorXTerm256.COLOR_16.value == 16
        assert ColorXTerm256.COLOR_231.value == 231

    def test_grayscale_range(self):
        assert ColorXTerm256.GRAY_232.value == 232
        assert ColorXTerm256.GRAY_255.value == 255

    def test_int_construction(self):
        assert ColorXTerm256(42) == ColorXTerm256.COLOR_42
        with pytest.raises(ValueError):
            ColorXTerm256(256)


class TestToRgb:
    def test_basic_colors(self):
        assert ColorXTerm256.BLACK.to_rgb() == (0, 0, 0)
        assert ColorXTerm256.RED.to_rgb() == (128, 0, 0)
        assert ColorXTerm256.BRIGHT_RED.to_rgb() == (255, 0, 0)
        assert ColorXTerm256.BRIGHT_WHITE.to_rgb() == (255, 255, 255)

    def test_basic_rgb_table_consistency(self):
        for index, rgb in BASIC_RGB.items():
            assert ColorXTerm256(index).to_rgb() == rgb

    def test_cube_corners(self):
        # cube index = 16 + r*36 + g*6 + b
        assert ColorXTerm256.COLOR_16.to_rgb() == (0, 0, 0)
        assert ColorXTerm256.COLOR_21.to_rgb() == (0, 0, 255)
        assert ColorXTerm256.COLOR_196.to_rgb() == (255, 0, 0)
        assert ColorXTerm256.COLOR_231.to_rgb() == (255, 255, 255)

    def test_cube_midpoint(self):
        # index 102 = 16 + 2*36 + 2*6 + 2 -> (135, 135, 135)
        assert ColorXTerm256(102).to_rgb() == (135, 135, 135)
        # index 145 = 16 + 3*36 + 3*6 + 3 -> (175, 175, 175)
        assert ColorXTerm256(145).to_rgb() == (175, 175, 175)

    def test_cube_levels_table(self):
        assert CUBE_LEVELS == (0, 95, 135, 175, 215, 255)

    def test_grayscale(self):
        assert ColorXTerm256.GRAY_232.to_rgb() == (8, 8, 8)
        assert ColorXTerm256.GRAY_244.to_rgb() == (128, 128, 128)
        assert ColorXTerm256.GRAY_255.to_rgb() == (238, 238, 238)


class TestFromRgb:
    def test_exact_basic_match(self):
        assert ColorXTerm256.from_rgb(255, 0, 0) == ColorXTerm256.BRIGHT_RED
        assert ColorXTerm256.from_rgb(0, 128, 0) == ColorXTerm256.GREEN

    def test_exact_cube_match(self):
        # pure green is in the cube (index 46) but BRIGHT_GREEN=10 is an exact
        # twin; the tie resolves to the lower index
        assert ColorXTerm256.from_rgb(0, 255, 0) == ColorXTerm256.BRIGHT_GREEN
        assert ColorXTerm256.from_rgb(95, 95, 95) == ColorXTerm256(59)

    def test_roundtrip_palette(self):
        for i in range(256):
            rgb = ColorXTerm256(i).to_rgb()
            # exact palette colors must round-trip to themselves (or a
            # lower-index twin with identical RGB)
            assert ColorXTerm256.from_rgb(*rgb).to_rgb() == rgb

    def test_invalid_channel(self):
        with pytest.raises(ValueError):
            ColorXTerm256.from_rgb(-1, 0, 0)
        with pytest.raises(ValueError):
            ColorXTerm256.from_rgb(0, 256, 0)
        with pytest.raises(ValueError):
            ColorXTerm256.from_rgb(0, 0, 300)


class TestFromHex:
    def test_with_and_without_hash(self):
        assert ColorXTerm256.from_hex('#ff0000') == ColorXTerm256.from_rgb(255, 0, 0)
        assert ColorXTerm256.from_hex('ff0000') == ColorXTerm256.from_hex('#ff0000')

    def test_known_value(self):
        assert ColorXTerm256.from_hex('#0000ff') == ColorXTerm256.BRIGHT_BLUE

    def test_whitespace_tolerance(self):
        assert ColorXTerm256.from_hex('  #00ff00  ') == ColorXTerm256.BRIGHT_GREEN

    def test_invalid(self):
        for bad in ('fff', '#12345', 'gggggg', '', '#12345g'):
            with pytest.raises(ValueError):
                ColorXTerm256.from_hex(bad)