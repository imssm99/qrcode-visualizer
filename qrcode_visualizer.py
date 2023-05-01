import cv2 as cv
from pyzbar import pyzbar
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import base64

options = Options()
options.add_argument("headless")
options.add_argument("window-size=512x512")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)
COLOR_BLACK = (0, 0, 0)

def barcode_to_points(barcode):
    data = {
        "UP": [0, 1, 2, 3],
        "LEFT": [0, 1, 2, 3],
        "RIGHT": [0, 1, 2, 3]
    }

    return np.array([[barcode.polygon[i].x, barcode.polygon[i].y] for i in data[barcode.orientation]], dtype=np.float32)

img_db = {}
def get_website_as_img(url):
    if url in img_db:
        return img_db[url]

    else:
        driver.get(url)
        result = cv.imdecode(np.fromstring(base64.b64decode(driver.get_screenshot_as_base64()), dtype=np.uint8), cv.IMREAD_COLOR)[::-1]
        img_db[url] = result
        driver.close()

        return result

if __name__ == "__main__":
    calib_data = np.load("./calibration_result.npz")

    video = cv.VideoCapture(0)

    obj_points = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0],
    ], dtype=np.float32)

    obj_points2 = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0],
    ], dtype=np.float32)

    render_points = np.array([
        [0, 0],
        [1024, 0],
        [1024, 1024],
        [0, 1024]
    ], dtype=np.float32)

    while True:
        valid, img = video.read()

        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        img_gray = cv.adaptiveThreshold(img_gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 99, 4)
        barcodes = pyzbar.decode(img_gray)

        for barcode in barcodes:
            img_points = barcode_to_points(barcode)

            for p1, p2 in zip(img_points[:-1], img_points[1:]):
                cv.line(img, p1.astype(np.int32), p2.astype(np.int32), COLOR_RED, 3)

            ret, rvec, tvec = cv.solvePnP(obj_points, img_points, calib_data["K"], calib_data["dist_coeff"])
            
            if ret:
                point, _ = cv.projectPoints(obj_points2, rvec, tvec, calib_data["K"], calib_data["dist_coeff"])
                
                render = get_website_as_img(barcode.data.decode())

                matrix = cv.getPerspectiveTransform(render_points, point)
                dst = cv.warpPerspective(render, matrix, (1280, 720))

                cv.fillConvexPoly(img, point.astype(np.int32), COLOR_BLACK)
                img += dst

        cv.imshow("QRCode Visualizer", img)

        key = cv.waitKey(10)

        if key == 27:
            break

    cv.destroyAllWindows()