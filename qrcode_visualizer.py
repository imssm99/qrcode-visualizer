import cv2 as cv
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import base64
import requests
import colorsys
from scipy.spatial.transform import Rotation
import validators
import webbrowser


options = Options()
options.add_argument("headless")
options.add_argument("window-size=512x512")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)

cache = {}
def get_website_as_img(url):
    if url in cache:
        return cache[url]

    else:
        driver.get(url)
        result = cv.imdecode(np.fromstring(base64.b64decode(driver.get_screenshot_as_base64()), dtype=np.uint8), cv.IMREAD_COLOR)
        cache[url] = result
        driver.close()

        return result

def get_object_as_np(url):
    if url in cache:
        return cache[url]

    else:
        r = requests.get(url)
        obj = np.fromstring(r.text, sep=' ').reshape(-1, 3)

        obj = np.interp(obj, (obj.min(), obj.max()), (-1, +1)) # Size normalize
        obj = obj[obj[:,1].argsort()] # For coloring
        obj_rotation = [90, 0, 90] # Set default rotation
        obj_rvec = Rotation.from_euler('zyx', obj_rotation[::-1], degrees=True).as_matrix()
        obj_tvec = np.array([0.0, 0.0, 0.0]) # Set default position
        obj_result = obj @ obj_rvec + obj_tvec

        cache[url] = obj_result

        return obj_result

def get_text_as_img(text):
    if text in cache:
        return cache[text]

    else:
        img = np.zeros((512, 512, 3), dtype=np.uint8)

        for i, t in enumerate(text.split("\n")):
            cv.putText(img, t, (0, 64 + (i*64)), cv.FONT_HERSHEY_DUPLEX, 1.5, COLOR_WHITE, 3)

        cache[text] = img
        return img

def get_blank_img(text):
    if text in cache:
        return cache[text]

    else:
        img = np.zeros((512, 512, 3), dtype=np.uint8)
        cache[text] = img
        return img

def mouse_event_handler(event, x, y, flags, param):
    if event == cv.EVENT_LBUTTONDOWN:
        param[0] = True
        param[2] = (x, y)
    elif event == cv.EVENT_LBUTTONUP:
        param[0] = False
        param[1] = True
    elif event == cv.EVENT_MOUSEMOVE:
        param[1] = False
        param[2] = (x, y)

if __name__ == "__main__":
    calib_data = np.load("./calibration_result.npz")

    video = cv.VideoCapture(0)

    qr_points = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0],
    ], dtype=np.float32)

    obj_points = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0],
    ], dtype=np.float32)

    render_web_points = np.array([
        [0, 0],
        [1024, 0],
        [1024, 1024],
        [0, 1024],
    ], dtype=np.float32)

    render_points = np.array([
        [0, 0],
        [512, 0],
        [512, 512],
        [0, 512],
    ], dtype=np.float32)

    barcode_cache = []
    mouse_state = [False, False, (-1, -1)]
    mouse_state_popup = [False, False, (-1, -1)]

    cv.namedWindow("QRCode Visualizer")
    cv.setMouseCallback("QRCode Visualizer", mouse_event_handler, mouse_state)

    qrcode_detector = cv.QRCodeDetector()

    while True:
        valid, img = video.read()
        mouse_down, mouse_click, mouse_xy = mouse_state

        img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        img_gray = cv.adaptiveThreshold(img_gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 99, 4)
        barcodes = qrcode_detector.detectAndDecodeMulti(img_gray)

        if barcodes[0]:
            barcode_cache = [[(data, polygon), 5] for data, polygon in zip(barcodes[1], barcodes[2])]
            print(barcodes)

        for idx in range(len(barcode_cache)):
            if barcode_cache[idx][1]:
                barcode_cache[idx][1] -= 1

                barcode = barcode_cache[idx][0]
                img_points = barcode[1]

                ret, rvec, tvec = cv.solvePnP(qr_points, img_points, calib_data["K"], calib_data["dist_coeff"])
                
                data = barcode[0]
                if ret:
                    if validators.url(data):
                        if data.endswith(".xyz"): # XYZ 
                            obj_result = get_object_as_np(data) 
                            point_color = [np.array(colorsys.hsv_to_rgb(i/len(obj_result), 1.0, 1.0)) * 255 for i in range(len(obj_result))]

                            point, _ = cv.projectPoints(obj_result, rvec, tvec, calib_data["K"], calib_data["dist_coeff"])
                            for p, p_c in zip(point, point_color):
                                cv.circle(img, np.int32(p.flatten()), 10, p_c, -1) # Trick to draw surface

                        else: # Normal website
                            point, _ = cv.projectPoints(obj_points, rvec, tvec, calib_data["K"], calib_data["dist_coeff"])
                            
                            render = get_website_as_img(data)

                            matrix = cv.getPerspectiveTransform(render_web_points, point)
                            dst = cv.warpPerspective(render, matrix, (1280, 720))

                            cv.fillConvexPoly(img, point.astype(np.int32), COLOR_BLACK)
                            img += dst

                            if mouse_click and cv.pointPolygonTest(point, mouse_xy, False) == 1.0:
                                webbrowser.open(data)
                                mouse_state[1] = False

                    else: # No url
                        if data.startswith("QRV_PAINT"): # Paint
                            point, _ = cv.projectPoints(obj_points, rvec, tvec, calib_data["K"], calib_data["dist_coeff"]) 
                            render = get_blank_img(data)

                            matrix = cv.getPerspectiveTransform(render_points, point)
                            dst = cv.warpPerspective(render, matrix, (1280, 720))

                            cv.fillConvexPoly(img, point.astype(np.int32), COLOR_BLACK)
                            img += dst 

                            if mouse_down and cv.pointPolygonTest(point, mouse_xy, False) == 1.0:
                                xy = cv.perspectiveTransform(np.array([[mouse_xy]], dtype=np.float32), np.linalg.inv(matrix))
                                cv.circle(render, xy.astype(np.int32).flatten(), 3, COLOR_WHITE, -1)

                        else: # Normal text
                            point, _ = cv.projectPoints(obj_points, rvec, tvec, calib_data["K"], calib_data["dist_coeff"]) 
                            render = get_text_as_img(data)

                            matrix = cv.getPerspectiveTransform(render_points, point)
                            dst = cv.warpPerspective(render, matrix, (1280, 720))

                            cv.fillConvexPoly(img, point.astype(np.int32), COLOR_BLACK)
                            img += dst

                            if mouse_click and cv.pointPolygonTest(point, mouse_xy, False) == 1.0:
                                cv.imshow("Popup", render)
                                cv.setMouseCallback("Popup", mouse_event_handler, mouse_state_popup)
                                mouse_state[1] = False

        mouse_down_popup, mouse_click_popup, mouse_xy_popup = mouse_state_popup
        if mouse_click_popup:
            cv.destroyWindow("Popup")
            mouse_state_popup[1] = False

        cv.imshow("QRCode Visualizer", img)

        key = cv.waitKey(10)

        if key == 27:
            break

    cv.destroyAllWindows()