import generator
import optparse
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import cm, mm, inch, pica
# import Image
import reportlab
from reportlab.pdfbase import pdfmetrics
# reportlab.lib.utils.Image = Image
try:
    from PIL import Image
except ImportError:
    import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont

USAGE = """usage: %(prog)s [options]

This script generates pdf from list of provided barcodes
"""

PARSER = optparse.OptionParser()
PARSER.add_option('-1', dest='one_barcode', type=str, default="",
                  help="print single barcode")
PARSER.add_option('-m', dest='barcodes', type=str, default="",
                  help="list of barcodes with ; as delimeter")
PARSER.add_option('-f', dest='format', type=str, default="",
                  help="format print output of barcode, for ex. 2x3, 5x10 etc.")

## Fonts setup
path = os.path.realpath(__file__)
path = path[:path.rindex('/')]
pdfmetrics.registerFont(TTFont('normal', path + '/Exo-Regular.ttf'))
pdfmetrics.registerFont(TTFont('bold', path + '/DoppioOne-Regular.ttf'))


def pdf_images(img_generator, output, code_size=(3.8, 2.12), page_margin=(1.3, 1, 0.7, 1), \
    code_margin=(0, 0), code_padding=(0.2, 0.2), extra_pictogram=None, start_position=0, page_size=(21, 29.7)):
    """
    Pdf creation function. Takes all the parameters and draws on a PDF canvas.
    """
    page_size = (page_size[0] * cm, page_size[1] * cm)
    width, height = page_size  # Default is A4
    c = canvas.Canvas(output, pagesize=page_size)
    fontSize = 7
    c.setFont('normal', fontSize)

    extra_pictogram = Image.open(extra_pictogram)
    w, h = code_size[0] * cm, code_size[1] * cm

    def calculate_postion(row, column):
        x_pos = (w + code_margin[0] * cm) * column + page_margin[3] * cm
        y_pos = height - (h + code_margin[1] * cm) * row - page_margin[0] * cm
        return x_pos, y_pos

    # Set start column and row
    elems_per_row = int((width - 2 * page_margin[3] * cm) / (calculate_postion(0, 1)[0] - calculate_postion(0, 0)[0]))
    row = int(1 + start_position / elems_per_row)
    column = int(start_position - (row - 1) * elems_per_row)

    for i, data in enumerate(img_generator):
        img, code, price, label = data

        x_pos, y_pos = calculate_postion(row, column)
        if x_pos + (code_size[0] + page_margin[1] + code_margin[0]) * cm > width:
            column = 0
            row += 1
            x_pos, y_pos = calculate_postion(row, column)

        if (y_pos - page_margin[2] * cm - code_margin[1] * cm) < 0:
            c.showPage()
            row = 1
            column = 0
            x_pos, y_pos = calculate_postion(row, column)

        # c.rect(x_pos, y_pos, code_size[0] * cm, code_size[1] * cm, stroke=1, fill=0)
        size_x = (code_size[0] - 2 * code_padding[0]) * cm
        size_y = (code_size[1] - 2 * code_padding[1]) * cm
        x_pos = x_pos + code_padding[0] * cm
        y_pos = y_pos + code_padding[1] * cm

        c.saveState()
        c.translate(x_pos, y_pos)
        # c.rect(0, 0, size_x, size_y, stroke=1, fill=0)

        c.setFont('normal', fontSize)

        # Draw label
        label_w = c.stringWidth(label, 'normal', fontSize)
        label_h = fontSize
        c.drawString(size_x / 2 - label_w / 2, size_y - label_h, label)

        # Draw extra pictorgram
        c.drawImage(ImageReader(extra_pictogram), size_x - 0.7 * cm, 0, 0.7 * cm, size_y / 2, preserveAspectRatio=True)

        # Draw price
        c.rotate(-90)
        c.setFont('bold', fontSize)
        label_w = c.stringWidth(price, 'bold', fontSize)
        # label_pos = get_absolute_pos(size_x - label_w, size_y / 2 - label_w / 2)
        c.drawString(-1 * size_y + 0.2 * cm, size_x - fontSize - 0.15 * cm, price)
        c.setFont('normal', fontSize - 3)
        c.drawString(-1 * size_y + 0.2 * cm + label_w, size_x - fontSize - 0.15 * cm, "PLN")
        c.setFont('normal', fontSize)
        c.rotate(90)

        # Draw code as string
        label_w = c.stringWidth(code, 'normal', fontSize)
        c.drawString(size_x / 2 - label_w / 2, 3, code)

        # Finally, draw the barcode !
        c.drawImage(ImageReader(img), 0, label_h * 1.2, size_x - 0.7 * cm, size_y - 2 * label_h * 1.2, preserveAspectRatio=True)
        c.restoreState()

        column += 1

    c.showPage()
    c.save()


def main():
    """
    Command line barcode printer.
    """
    options, args = PARSER.parse_args()

    if options.one_barcode:
        image = generator.code128_image(options.one_barcode, height=100, thickness=3, quiet_zone=True, label=True)
        image.save(options.one_barcode + ".gif", format="GIF")

    elif options.barcodes:
        # Multiple barcodes, generate PDF with them
        options.barcodes = ""
        sample_codes = "123124123345|23|pointy grishko;12312412334545|32|blayer M;123124123345kk|423|florette;1234321,623,kaktasowo;ghash|1|ajfusowo;xcvabcdefgkihj|423|calkiem dlugi napisek;"
        for i in range(0, 13):
            options.barcodes += sample_codes
        options.barcodes = options.barcodes[:-1]

        def barcode_generator():
            for code_data in options.barcodes.split(";"):
                code = code_data.split(",")
                # Generate barcode data in img, price, label format
                yield (generator.code128_image(code[0], height=700, thickness=13, quiet_zone=False), code[0], code[1], code[2])

        pdf_images(barcode_generator(), "out.pdf")


if __name__ == "__main__":
    main()
