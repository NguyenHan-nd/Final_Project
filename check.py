import numpy as np
import utlis
import cv2

def check_image(image,kx,ky):
    try:
        image = cv2.resize(image, (1200, 900), interpolation=cv2.INTER_LINEAR)
        imgGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (kx, ky), 1)
        imgCanny = cv2.Canny(imgBlur, 30, 30)
        imgContours = image.copy()

        Contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectCon = utlis.rectangeContour(Contours, 850, 1400)

        cv2.drawContours(imgContours, rectCon, -1, (0, 255, 0), 3)
        Limit_Points = utlis.Limit_Area_Point(rectCon)
        if (Limit_Points[0][0][0] < 600 and Limit_Points[0][0][1] < 450 and Limit_Points[1][0][0] > 600 and Limit_Points[1][0][1] < 450
            and Limit_Points[2][0][0] < 600 and Limit_Points[2][0][1] > 450 and Limit_Points[3][0][0] > 600 and Limit_Points[3][0][1] > 450):
            return 1
        return 0
    except:
        return 0

