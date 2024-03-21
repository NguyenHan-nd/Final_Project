import numpy as np
import cv2
import os
def stackImages(scale, imgArray):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range(0, rows):
            for y in range(0, cols):
                if imgArray[x][y].shape[:2] == imgArray[0][0].shape[:2]:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                else:
                    imgArray[x][y] = cv2.resize(imgArray[x][y], (imgArray[0][0].shape[1], imgArray[0][0].shape[0]),
                                                None,
                                                scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y] = cv2.cvtColor(imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank] * rows
        hor_con = [imageBlank] * rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if imgArray[x].shape[:2] == imgArray[0].shape[:2]:
                imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            else:
                imgArray[x] = cv2.resize(imgArray[x], (imgArray[0].shape[1], imgArray[0].shape[0]), None, scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor = np.hstack(imgArray)
        ver = hor
    return ver

def rectangeContour(contour,lower, upper):
    rectCon = []
    for i in contour:
        area = cv2.contourArea(i)
        # print("Area",area)

        if area > lower and area < upper:
            peri = cv2.arcLength(i, True)
            approx = cv2.approxPolyDP(i, 0.02 * peri, True)
            print(area)
            #print("Corner Points",approx)
            if len(approx) == 4:
                # print("Corner Points", approx)
                rectCon.append(i)
    rectCon = sorted(rectCon, key=cv2.contourArea, reverse=True)
    return rectCon


def reorder(myPoints):
    myPoints = myPoints.reshape((4, 2))

    myPointsNew = np.zeros((4, 1, 2), np.int32)
    add = myPoints.sum(1)
    # print(myPoints)
    # print(add)
    myPointsNew[0] = myPoints[np.argmin(add)]  # diem trai tren
    myPointsNew[3] = myPoints[np.argmax(add)]  # diem phai duoi
    diff = np.diff(myPoints, axis=1)

    myPointsNew[1] = myPoints[np.argmin(diff)]  # [w, 0]
    myPointsNew[2] = myPoints[np.argmax(diff)]  # [0, h]
    # print(diff)
    # print(myPointsNew)

    return myPointsNew

def getCornerPoints(cont):
    peri = cv2.arcLength(cont, True)
    approx = cv2.approxPolyDP(cont, 0.02 * peri, True)
    return approx


def Limit_Area_Point(rectCon):
    count = 0
    center_arr = np.zeros((len(rectCon),2))
    flag = np.zeros((6,1))
    mid_point_area = np.zeros((2,2))
    for i in rectCon:
        black_box = getCornerPoints(i)
        black_box = black_box.reshape((4,2))
        center = np.average(black_box,axis=0)
        center_arr[count] = center
        count = count + 1
        # print(center, type(center))

    center_arr = center_arr.astype(int)
    center_arr_tmp = center_arr
    # print(center_arr)
    myPointsAreaLimit = np.zeros((4, 1, 2), np.int32)
    add = center_arr.sum(1)
    myPointsAreaLimit[0] = center_arr[np.argmin(add)]   # trai tren
    myPointsAreaLimit[3] = center_arr[np.argmax(add)]   # phai duoi
    # flag[np.argmin(add)] = 1
    # flag[np.argmax(add)] = 1
    diff = np.diff(center_arr, axis=1)

    myPointsAreaLimit[1] = center_arr[np.argmin(diff)]  # [w, 0] phai tren
    myPointsAreaLimit[2] = center_arr[np.argmax(diff)]  # [0, h] trai duoi
    # flag[np.argmax(diff)] = 1
    # flag[np.argmin(diff)] = 1
    # i = 0
    # c = 0
    # while (i < 6):
    #     if flag[i] == [0]:
    #         mid_point_area[c] = center_arr[i]
    #         c = c + 1
    #     i = i + 1
    #
    # add = mid_point_area.sum(1);
    # myPointsAreaLimit[4] = mid_point_area[np.argmin(add)]   # trai giua
    # myPointsAreaLimit[5] = mid_point_area[np.argmax(add)]   # phai giua

    # print(myPointsAreaLimit)

    return myPointsAreaLimit
def splitBoxes(img, x, y):
    cols = np.hsplit(img, x)
    # if (x > 3):
    #     for i in range(0, 6):
    #         cv2.imwrite(os.path.join('./Image_stages/' + "cols{}.png").format(i), cols[i])
    boxes = []
    i = 0
    for c in cols:
        rows = np.vsplit(c, y)
        for box in rows:
            #crop box
            heightBox, widthBox = box.shape

            if i < 10:
                box = box[10: heightBox - 10, 24: widthBox - 10]
            if i >= (x-1)*10:
                box = box[10: heightBox - 10, 0: widthBox - 15]
            if i % 10 == 0 :
                box = box[10: heightBox,]
            if i % 10 == 9 :
                box = box[0: heightBox - 10, ]
            # print(heightBox, widthBox)
            # if (i < 10 and x == 6) :
            #     cv2.imwrite(os.path.join('./Image_stages/' + "box{}.png").format(i), box)
            boxes.append(box)

            i = i + 1
    return boxes

def splitBoxes_MCQs(img, x, y):
    rows = np.vsplit(img, y)

    boxes = []
    i = 0

    for r in rows:
        c = np.hsplit(r, x)
        c.pop(0)
        for box in c:
            #crop box
            heightBox, widthBox = box.shape
            if i < 4:
                box = box[10: heightBox, 0: widthBox]
            if i >= (y-1)*4:
                box = box[ 0: heightBox - 7, 0: widthBox]
            if i % 4 == 3 :
                box = box[0: heightBox, 0: widthBox - 5]
            # print(heightBox, widthBox)
            boxes.append(box)

            i = i + 1
    return boxes

def showIDorCode(img, myIndex, cols, rows):
    secW = int(img.shape[1] / cols)
    secH = int(img.shape[0] / rows)

    for x in range(0, cols):
        myID = myIndex[x]
        cY = int((myID * secH) + secH / 2)  # find center values in ans box
        cX = int((x * secW) + secW / 2)

        # if grading[x] == 1:
        #     myColor = (0, 255, 0)
        # else:
        #     myColor = (0, 0, 255)
        #     correctAns = ans[x]
        #     cv2.circle(img, ((correctAns * secW) + secW // 2, (x * secH) + secH // 2), 20, (0, 255, 0), cv2.FILLED)

        cv2.circle(img, (cX, cY), 50, (0,0,255), cv2.FILLED)
    return img

def showAnswer(img, myIndex, cols, rows):
    secW = int(img.shape[1] / (cols + 1))
    secH = int(img.shape[0] / rows)

    for x in range(0, rows):
        myID = myIndex[x]
        cY = int((x * secH) + secH / 2)  # find center values in ans box
        cX = int((myID * secW) + secW / 2 + secW)

        # if grading[x] == 1:
        #     myColor = (0, 255, 0)
        # else:
        #     myColor = (0, 0, 255)
        #     correctAns = ans[x]
        #     cv2.circle(img, ((correctAns * secW) + secW // 2, (x * secH) + secH // 2), 20, (0, 255, 0), cv2.FILLED)

        cv2.circle(img, (cX, cY), 20, (0,0,255), cv2.FILLED)
    return img




