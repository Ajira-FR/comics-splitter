# coding: utf-8
import sys, getopt
import os
import re

from PIL import Image, ImageDraw

def print_help():
    print('Usage : comics_splitter.py -i <inputDir> -o <outputDir>')
    print("""Options:
    -r, --rotate : enable rotation to always have a portrait page (very usefull on E-reader)
    -d, --diago : (beta feature!!) enable diagonal split but overlong processing
    -s, --sort : smart sort on files name (Windows sort)
    -h, --help : print help
    """)
    exit(1)


def get_line(start, end, imageGrey, px, tolerance):
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end

    points1 = get_line((0, 0), (3, 4))
    points2 = get_line((3, 4), (0, 0))
    assert(set(points1) == set(points2))
    print points1
    [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
    print points2
    [(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []

    stop = 0

    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        if imageGrey.getpixel(coord) < 250:
            stop += 1
        px[coord[0], coord[1]] = (255 - (stop * stop), 0, (stop * stop))

        if stop > tolerance:
            return

        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    return points

def search_diagonale(start, end, imageGrey, tolerance):
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    stop = 0

    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        if imageGrey.getpixel(coord) < 250:
            stop += 1

        if stop > tolerance:
            return False

        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    return True


def cut_panels(imageColor, polygons, rotate=False):
    sizeX, sizeY = imageColor.size
    part = []
    imagesOut = []

    if len(polygons) == 0:
        if rotate and sizeX > sizeY:
            image = imageColor.rotate(270, expand=True)
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
                print("Regroupage !!")
            elif i > 0 and i+1 == len(squareY):
                squareY[i-1][1] = squareY[i][1]
                squareY.pop(i)
                i=0
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
                print("Regroupage !!")
            else:
                i += 1
        else:
            i += 1

    return squareY

def search_left_border(imageGrey, tolerance):
    sizeX, sizeY = imageGrey.size
    x = 0
    stop = 0
    while x < sizeX and stop <= tolerance:
        y = 0
        stop = 0
        while y < sizeY and stop <= tolerance:
            if imageGrey.getpixel((x, y)) < 250:
                stop += 1
            y += 1
        if stop <= tolerance:
            x += 1
    return x

def search_right_border(imageGrey, tolerance):
    sizeX, sizeY = imageGrey.size
    x = sizeX
    stop = 0
    while x - 1 >= 0 and stop <= tolerance:
        y = 0
        stop = 0
        while y < sizeY and stop <= tolerance:
            if imageGrey.getpixel((x - 1, y)) < 250:
                stop += 1
            y += 1
        if stop <= tolerance:
            x -= 1
    return x

def remove_borders(imageGrey):
    sizeY = imageGrey.size[1]
    x_left = search_left_border(imageGrey)
    x_right = search_right_border(imageGrey)

    print("x_left = {}, x_right = {}".format((x_left, x_right)))

    box = (x_left, 0, x_right, sizeY)
    return imageGrey.crop(box)

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

def search_horizontal(imageGrey, tolerance, miniWhiteBorder, diago, angle=200):
    sizeX, sizeY = imageGrey.size
    cutY = []
    startSquare = False
    yDiago = -1
    for y in range(sizeY):
        x = 0
        stop = 0
        while x < sizeX and stop <= tolerance:
            pix = imageGrey.getpixel((x, y))

            if pix < 250:
                stop += 1
            x += 1

        if startSquare:
            if stop <= tolerance:
                print("Découpage horizontal finit à y={}".format(y))
                square.append((sizeX, y))
                square.append((0, y))
                cutY.append(square)
                startSquare = False
            elif diago and x > tolerance + 5:
                if y >= angle:
                    yUp = y - angle
                else:
                    yUp = 0
                if y < sizeY - angle:
                    yDown = y + angle
                else:
                    yDown = sizeY
                while yUp < yDown:
                    if search_diagonale((0, y), (sizeX - 1, yUp), imageGrey, tolerance):
                        print("Découpage diagonal finit à y0={} et y1={}".format(y, yUp))
                        square.append((sizeX, yUp))
                        square.append((0, y))
                        cutY.append(square)
                        startSquare = False
                        break
                    yUp += 1
        else:
            if stop > tolerance: #no horizontal white line
                noWhite = False
                if diago and x > tolerance + 5:
                    if y >= angle:
                        yUp = y - angle
                    else:
                        yUp = 0
                    if y < sizeY - angle:
                        yDown = y + angle
                    else:
                        yDown = sizeY - 1
                    while yDown >= yUp:
                        if search_diagonale((0, y), (sizeX - 1, yDown), imageGrey, tolerance):
                            yDiago = yDown
                            break
                        yDown -= 1
                    if yDown < yUp:
                        noWhite = True
                elif diago:
                    noWhite = True

                if noWhite and yDiago >= 0: # no more diago white
                    print("Découpage diagonal débute à y0={} et y1={}".format(y - 1, yDiago))
                    square = [(0, y - 1), (sizeX, yDiago)]
                    startSquare = True
                    yDiago = -1
                elif yDiago < 0:
                    print("Découpage horizontal débute à y={}".format(y))
                    square = [(0, y), (sizeX, y)]
                    startSquare = True

    if startSquare: #fin de page
        print("Découpage horizontal finit à y={}".format(sizeY))
        square.append((sizeX, sizeY))
        square.append((0, sizeY))
        cutY.append(square)

    if len(cutY) == 0:
        print("Découpage horizontal impossible")

    return cutY

def search_split(imageGrey, diago=False, verticalSplit=False, tolerance=10, miniWhiteBorder=3, miniCaseHeight=100):
    case2split = []
    horiSplit = search_horizontal(imageGrey, tolerance, miniWhiteBorder, diago)
    print(horiSplit)
    #horiSplit = regroup(horiSplit, miniCaseHeight)
    #print(horiSplit)

    sizeX, sizeY = imageGrey.size

    if len(horiSplit) == 0:
        x_left = search_left_border(imageGrey, tolerance)
        x_right = search_right_border(imageGrey, tolerance)
        print("x_left = {}, x_right = {}".format(x_left, x_right))
        case2split.append([(x_left, 0), (x_right, 0), (x_right, sizeY), (x_left, sizeY)])
        return  case2split

    for square in horiSplit:
        x0, y0 = square[0]
        x1, y1 = square[1]
        x2, y2 = square[2]
        x3, y3 = square[3]

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

        box = (0, yUp, sizeX, yDown)

        if diago:
            copy = imageGrey.copy()
            imageDraw = ImageDraw.Draw(copy)
            imageDraw.polygon([(0, 0), (sizeX, 0), (sizeX, y1 - 1), (0, y0 - 1)], outline="white", fill="white")
            imageDraw.polygon([(0, y3 + 1), (sizeX, y2 + 1), (sizeX, sizeY), (0, sizeY)], outline="white", fill="white")
            temp = copy.crop(box)
            del imageDraw
        else:
            temp = imageGrey.crop(box)

        if verticalSplit:
            print("#TODO")

        x_left = search_left_border(temp, tolerance)
        x_right = search_right_border(temp, tolerance)
        print("x_left = {}, x_right = {}".format(x_left, x_right))
        case2split.append([(x_left, y0), (x_right, y1), (x_right, y2), (x_left, y3)])
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
    try:
        opts, args = getopt.getopt(argv,"hi:o:sdr",["help", "idir=", "odir=", "sort", "diago", "rotate"])
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
        if os.path.splitext(file)[1] in [".jpg", ".png", ".jpeg"]:
            page += 1
            im = Image.open("{}/{}".format(inputDir, file))
            imGrey = im.convert("L")

            case2split = search_split(imGrey, diago=diago)
            #imDraw = draw_case(case2split, im)

            im2sav = cut_panels(im, case2split, rotate)
            num = 0
            for i2s in im2sav:
                i2s.save("{}/{}_{:02}.{}".format(outputDir, page, num, "png"))
                num += 1


if __name__ == "__main__":
   main(sys.argv[1:])


