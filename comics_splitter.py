# coding: utf-8
import sys, getopt
import os
import re
from math import ceil
from PIL import Image, ImageDraw
import time

DEBUG = True
STEP = 5

def print_help():
    print('Usage : comics_splitter.py -i <inputDir> -o <outputDir>')
    print("""Options:
    -r, --rotate : enable rotation to always have a portrait page (very usefull on E-reader)
    -d, --diago : enable diagonal split (longer processing)
    -s, --sort : smart sort on files name (Windows sort)
    -h, --help : print help
    --draw : only draw cut area
    """)
    exit(1)

def search_diagonale(start, end, imageGrey, tolerance):
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    stop = 0
    while x1 <= x2  and stop <= tolerance:
        coord = (x1, y1)
        if imageGrey.getpixel(coord) < 250:
            stop += 1

        error -= abs(dy)
        if error < 0:
            y1 += ystep
            error += dx
        x1 += 1

    return x1, stop

def cut_panels(imageColor, polygons, rotate=False):
    sizeX, sizeY = imageColor.size
    part = []
    imagesOut = []

    if len(polygons) == 0:
        if rotate and sizeX > sizeY:
            image = imageColor.rotate(270, expand=True)
            if DEBUG:
                print("Rotation !")
        imagesOut.append(image)
    else:
        for polygon in polygons:
            x0, y0 = polygon[0]
            x1, y1 = polygon[1]
            x2, y2 = polygon[2]
            x3, y3 = polygon[3]

            diago = False
            if y0 == y1:
                yUp = y0
            elif y0 > y1:
                yUp = y1
                diago = True
            else:
                yUp = y0
                diago = True

            if y2 == y3:
                yDown = y2
            elif y2 > y3:
                yDown = y2
                diago = True
            else:
                yDown = y3
                diago = True

            box = (x0, yUp, x1, yDown)

            if diago:
                copy = imageColor.copy()
                imageDraw = ImageDraw.Draw(copy)
                imageDraw.polygon([(0, 0), (sizeX, 0), (sizeX, y1 - 1), (0, y0 - 1)], outline="white", fill="white")
                imageDraw.polygon([(0, y3 + 1), (sizeX, y2 + 1), (sizeX, sizeY), (0, sizeY)], outline="white",
                                  fill="white")
                temp = copy.crop(box)
                del imageDraw
            else:
                temp = imageColor.crop(box)

            if rotate:
                if x1 - x0 > yDown - yUp:
                    temp = temp.rotate(270, expand=True)
                    if DEBUG:
                        print("Rotation !")
            imagesOut.append(temp)

    return imagesOut

def regroup(squareY, miniCaseHeight):
    i = 0
    while i < len(squareY):
        y0, y1 = squareY[i]
        if y1-y0 < miniCaseHeight:
            if i == 0 and i+1 < len(squareY):
                squareY[i][1] = squareY[i+1][1]
                squareY.pop(i+1)
                i = 0
                if DEBUG:
                    print("Regroupage !!")
            elif i > 0 and i+1 == len(squareY):
                squareY[i-1][1] = squareY[i][1]
                squareY.pop(i)
                i=0
                if DEBUG:
                    print("Regroupage !!")
            elif i > 0 and i+1 < len(squareY):
                y00, y01 = squareY[i - 1]
                y10, y11 = squareY[i + 1]
                if (y01 - y00) > (y11 - y10):
                    squareY[i][1] = squareY[i + 1][1]
                    squareY.pop(i + 1)
                else:
                    squareY[i - 1][1] = squareY[i][1]
                    squareY.pop(i)
                i = 0
                if DEBUG:
                    print("Regroupage !!")
            else:
                i += 1
        else:
            i += 1

    return squareY

def search_left_right_borders(imageGrey, tolerance):
    sizeX, sizeY = imageGrey.size
    x_left = 0
    x_right = sizeX
    stop = 0

    while x_left < (sizeX / 3) and stop <= tolerance:
        y = 0
        stop = 0
        while y < sizeY and stop <= tolerance:
            if imageGrey.getpixel((x_left, y)) < 250:
                stop += 1
            y += STEP
        if stop <= tolerance:
            x_left += 1

    stop = 0
    while x_right - 1 >= (sizeX / 3) * 2 and stop <= tolerance:
        y = 0
        stop = 0
        while y < sizeY and stop <= tolerance:
            if imageGrey.getpixel((x_right - 1, y)) < 250:
                stop += 1
            y += STEP
        if stop <= tolerance:
            x_right -= 1

    return x_left, x_right

def draw_search_horizontal(imageGrey, imageColor, name, tolerance=10, ext="png", angle=200):
    sizeX, sizeY = imageGrey.size
    cutY = []
    px = imageColor.load()
    for y in range(sizeY):
        x = 0
        stop = 0
        while x < sizeX and stop <= tolerance:
            pix = imageGrey.getpixel((x, y))
            if pix < 250:
                stop += 1

            px[x, y] = (255-(stop*stop), 0, (stop*stop))

            if stop > tolerance and x > tolerance+1:
                if y >= angle:
                    yUp = y - angle
                else:
                    yUp = y
                if y < sizeY - angle:
                    yDown = y + angle
                else:
                    yDown = y

                for yy in range(yUp, yDown):
                    get_line((0, y), (sizeX - 1, yy), imageGrey, px, tolerance)

                    """i = 0
                    stop2 = 0
                    while i < len(droite) and stop2 <= tolerance:
                        if imageGrey.getpixel(droite[i]) < 250:
                            stop2 += 1
                        px[droite[i][0], droite[i][1]] = (255-(stop2*stop2), 0, (stop2*stop2))
                        i += 1"""

            x += 1

        if stop <= tolerance:
            print("Découpage horizontal à y={}".format(y))
            cutY.append(y)

    imageColor.save("D:\out/debug_{}.{}".format(name, ext))

def search_horizontal(imageGrey, tolerance, y):
    sizeX = imageGrey.size[0]
    x = 0
    stop = 0
    while x < sizeX and stop <= tolerance:
        pix = imageGrey.getpixel((x, y))
        if pix < 250:
            stop += 1
        x += 1
    return (x, stop)

def search_multi_diago(y, yUp, yDown, imageGrey, tolerance):
    sizeX, sizeY = imageGrey.size
    while yUp < yDown:
        x1, y1 = 0, y
        x2, y2 = sizeX - 1, yUp
        dx = x2 - x1
        dy = y2 - y1

        error = int(dx / 2.0)
        ystep = 1 if y1 < y2 else -1

        stop = 0
        while x1 <= x2 and stop <= tolerance:
            coord = (x1, y1)
            if imageGrey.getpixel(coord) < 250:
                stop += 1

            if stop <= tolerance:
                error -= abs(dy)
                if error < 0:
                    y1 += ystep
                    error += dx
                x1 += 1

        if stop > tolerance: #inutile de continuer la diagonale, on calcule la prochaine hauteur max (dy)
            # dy = (y * dx + int(dx/2)) / x
            yy = y1 - y + 1
            ddy = ceil((dx * abs(yy) - int(dx/2)) / x1)
            yyUp = y - ddy if yy < 0 else y + ddy
            yUp = yyUp if yyUp > yUp else yUp + 1
        else:
            return yUp
    return False

def horizontal_cut(imageGrey, tolerance, diago, angle=200):
    sizeX, sizeY = imageGrey.size
    panels = []
    startSquare = False
    inclinaison = 0
    lastY = 0

    for y in range(0, sizeY, STEP):
        if not startSquare: #search for begin of a panel
            if inclinaison:
                if search_diagonale((0, y), (sizeX - 1, min((y + inclinaison), sizeY - 1)), imageGrey, tolerance)[0] < sizeX: #find diagonal panel
                    lastY = y + inclinaison
                    square = [(0, y), (sizeX, lastY)]
                    startSquare = True
                    if DEBUG:
                        print("Découpage diagonal débute à y0={} et y1={}".format(y, lastY))
            else:
                if search_horizontal(imageGrey, tolerance, y)[0] < sizeX: #find horizontal panel
                    lastY = y
                    square = [(0, lastY), (sizeX, lastY)]
                    startSquare = True
                    if DEBUG:
                        print("Découpage horizontal débute à y={}".format(lastY))

        else: #search for end of a panel
            if y > lastY and search_horizontal(imageGrey, tolerance, y)[0] == sizeX: #find blanck line
                square.append((sizeX, y))
                square.append((0, y))
                panels.append(square)
                startSquare = False
                inclinaison = 0
                lastY = y
                if DEBUG:
                    print("Découpage horizontal finit à y={}".format(y))
            elif diago:
                yUp = max(y - angle, lastY)
                yDown = min(y + angle, sizeY - 1)
                yUp = search_multi_diago(y, yUp, yDown, imageGrey, tolerance)
                if yUp:
                    startSquare = False
                    inclinaison = yUp - y
                    square.append((sizeX, yUp))
                    square.append((0, y))
                    panels.append(square)
                    lastY = yUp
                    if DEBUG:
                        print("Découpage diagonal finit à y0={} et y1={}".format(y, yUp))

    if startSquare: #fin de page
        if DEBUG:
            print("Découpage horizontal finit à y={}".format(sizeY))
        square.append((sizeX, sizeY))
        square.append((0, sizeY))
        panels.append(square)

    if DEBUG and len(panels) == 0:
        print("Découpage horizontal impossible")

    return panels

def search_split(imageGrey, diago=False, verticalSplit=False, tolerance=10):
    case2split = []
    sizeX, sizeY = imageGrey.size

    #tmps1 = time.clock()
    x_left, x_right = search_left_right_borders(imageGrey, tolerance)
    #tmps2 = time.clock()
    #print("after search_left_border %f" % (tmps2 - tmps1))

    #x_right = search_right_border(imageGrey, tolerance)
    #tmps3 = time.clock()
    #print("after search_right_border %f" % (tmps3 - tmps2))

    if DEBUG:
        print("x_left = {}, x_right = {}".format(x_left, x_right))

    box = (x_left, 0, x_right, sizeY)
    imageGrey = imageGrey.crop(box)

    horiSplit = horizontal_cut(imageGrey, tolerance, diago)

    #tmps4 = time.clock()
    #print("after search_horizontal %f" % (tmps4 - tmps3))

    if DEBUG:
        print(horiSplit)

    if len(horiSplit) == 0:
        case2split.append([(x_left, 0), (x_right, 0), (x_right, sizeY), (x_left, sizeY)])
    else:
        for square in horiSplit:
            x0, y0 = square[0]
            x1, y1 = square[1]
            x2, y2 = square[2]
            x3, y3 = square[3]

            if verticalSplit:
                print("#TODO")

            case2split.append([(x_left, y0), (x_right, y1), (x_right, y2), (x_left, y3)])

        #tmps444 = time.clock()
        #print("after tot %f" % (tmps444 - tmps1))
    return case2split

def draw_case(boxList, imageColor, borderWidth=3):
    imageDraw = ImageDraw.Draw(imageColor)
    for square in boxList:
        x0, y0 = square[0]
        x1, y1 = square[1]
        x2, y2 = square[2]
        x3, y3 = square[3]
        for i in range(borderWidth):
            imageDraw.polygon([(x0 - i, y0 - i), (x1 + i, y1 - i), (x2 + i, y2 + i), (x3 - i, y3 + i)], outline="red")
            #imageDraw.rectangle([(x0 - i, y0 - i), (x1 + i, y1 + i)], outline="red")
    del imageDraw
    return imageColor

def main(argv):
    inputDir = ''
    outputDir = ''
    sort = False
    diago = False
    rotate = False
    draw = False
    try:
        opts, args = getopt.getopt(argv,"hi:o:sdrw",["help", "idir=", "odir=", "sort", "diago", "rotate", "draw"])
        print(opts)
    except getopt.GetoptError:
        print_help()

    for opt, arg in opts:
        if opt in ("-i", "--idir"):
            inputDir = arg
        elif opt in ("-o", "--odir"):
            outputDir = arg
        elif opt in ("-s", "--sort"):
            sort = True
        elif opt in ("-d", "--diago"):
            diago = True
        elif opt in ("-r", "--rotate"):
            rotate = True
        elif opt == "--draw":
            draw = True
        else:
            print_help()

    if len(inputDir) == 0 or len(outputDir) == 0:
        print_help()
        exit()

    if not os.path.isdir(inputDir):
        print("{} n'est pas un dossier".format(inputDir))
        exit()
    if not os.path.isdir(outputDir):
        print("{} n'est pas un dossier".format(outputDir))
        exit()

    page = 0

    files = os.listdir(inputDir)
    if sort:
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        files = sorted(files, key=lambda x: alphanum_key(x))

    for file in files:
        print(os.path.splitext(file))
        ext = os.path.splitext(file)[1].lower()
        if ext in [".jpg", ".png", ".jpeg"]:
            page += 1
            tmps1 = time.clock()
            im = Image.open("{}/{}".format(inputDir, file))
            #tmps2 = time.clock()
            #print("after open %f"  % (tmps2 - tmps1))
            imGrey = im.convert("L")
            #tmps3 = time.clock()
            #print("after convert %f" % (tmps3 - tmps2))

            case2split = search_split(imGrey, diago=diago)
            #tmps4 = time.clock()
            #print("after split %f" % (tmps4 - tmps3))
            #imDraw = draw_case(case2split, im)
            if draw:
                im2sav = [draw_case(case2split, im)]
            else:
                im2sav = cut_panels(im, case2split, rotate)
            #tmps5 = time.clock()
            #print("after cut %f" % (tmps5 - tmps4))

            num = 0
            for i2s in im2sav:
                i2s.save("{}/{}_{:02}{}".format(outputDir, page, num, ext))
                num += 1
            #tmps6 = time.clock()
            #print("after save %f" % (tmps6 - tmps5))
            print("totale = %f" % (time.clock() - tmps1))

if __name__ == "__main__":
   main(sys.argv[1:])


