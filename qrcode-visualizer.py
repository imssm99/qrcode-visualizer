import cv2 as cv
from pyzbar import pyzbar

COLOR_RED = (0, 0, 255)

if __name__ == "__main__":
    video = cv.VideoCapture(0)

    while True:
        valid, img = video.read()

        barcodes = pyzbar.decode(img)

        for barcode in barcodes:
            cv.line(img, barcode.polygon[0], barcode.polygon[1], COLOR_RED, 3)
            cv.line(img, barcode.polygon[1], barcode.polygon[2], COLOR_RED, 3)
            cv.line(img, barcode.polygon[0], barcode.polygon[3], COLOR_RED, 3)
            cv.line(img, barcode.polygon[2], barcode.polygon[3], COLOR_RED, 3)

        cv.imshow("QRCode Visualizer", img)

        key = cv.waitKey(10)

        if key == 27:
            break

    cv.destroyAllWindows()