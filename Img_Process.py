import numpy as np
import cv2
import utlis
import os
import random
def Process(image, kx, ky, flag):
    try:
        image = cv2.resize(image, (1200, 900), interpolation=cv2.INTER_LINEAR)
        # cv2.imshow("test", image)
        h, w = image.shape[:2]
        widthImg = 900
        heightImg = 1200
        StudentID = []
        CodeExam = []
        Student_Ans = []
        Example_Contours_Corners = np.array([[[65, 22]], [[64, 1110]], [[745, 1105]], [[743, 21]]])
        imgGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (kx, ky), 1)
        imgCanny = cv2.Canny(imgBlur, 40, 40)
        imgContours = image.copy()

        ##### Find Limited Point ######

        Contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectCon = utlis.rectangeContour(Contours, 850, 1400)

        cv2.drawContours(imgContours, rectCon, -1, (0, 255, 0), 3)
        imgRes = utlis.stackImages(0.5, [[imgCanny, imgContours]])
        # cv2.imshow("result", imgRes)

        Limit_Points = utlis.Limit_Area_Point(rectCon)
        # print(Limit_Points)
        # ------------- Crop image ---------------------------#
        point1 = np.float32([Limit_Points[0], Limit_Points[1], Limit_Points[2], Limit_Points[3]])
        point2 = np.float32([[0, 0], [heightImg, 0], [0, widthImg], [heightImg, widthImg]])
        matrix = cv2.getPerspectiveTransform(point1, point2)

        imgCropProcess = cv2.warpPerspective(image, matrix, (heightImg, widthImg))
        imgCropProcess_Canny = cv2.warpPerspective(imgCanny, matrix, (heightImg, widthImg))
        # cv2.imshow("imgCrop", imgCropProcess)
        imgFinal = imgCropProcess.copy()
        # ------------- Area 1 has ID and Code------------------------#

        # -------- Divide 3 to detect ID_Code_Area-----------#
        point1_Area1 = np.float32([[heightImg * 2 / 3, 0], [heightImg, 0], [heightImg * 2 / 3, widthImg / 2 + 40],
                                   [heightImg, widthImg / 2 + 40]])  # print (Limit_Points[0][0])
        point2_Area1 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix_Area1 = cv2.getPerspectiveTransform(point1_Area1, point2_Area1)
        imgWarpArea1 = cv2.warpPerspective(imgCropProcess, matrix_Area1, (widthImg, heightImg))
        imgWarpArea1_Canny = cv2.warpPerspective(imgCropProcess_Canny, matrix_Area1, (widthImg, heightImg))
        # cv2.imshow("canny",imgWarpArea1_Canny)
        # --------- Find Contours to detect ID and Code Area---------------------#

        Contours_Area1, hierarchy_Area1 = cv2.findContours(imgWarpArea1_Canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # cv2.imshow("CCCC", imgWarpArea1_Canny)
        rectCon_Area1 = utlis.rectangeContour(Contours_Area1, 50000, 500000)

        imgContours_Area1 = imgWarpArea1.copy()
        cv2.drawContours(imgContours_Area1, rectCon_Area1, -1, (255, 0, 0), 3)

        # cv2.imshow("CC", imgContours_Area1)
        ID_Contours = utlis.getCornerPoints(rectCon_Area1[0])
        Code_Contours = utlis.getCornerPoints(rectCon_Area1[1])
        ID_Contours = utlis.reorder(ID_Contours)
        Code_Contours = utlis.reorder(Code_Contours)
        imgWarpColorID = imgWarpArea1.copy()
        if (ID_Contours.size != 0) and (Code_Contours.size != 0):
            cv2.drawContours(imgContours_Area1, ID_Contours, -1, (255, 0, 0), 10)
            cv2.drawContours(imgContours_Area1, Code_Contours, -1, (0, 255, 0), 10)
            # cv2.imshow("C", imgContours_Area1)
            # ------------------Make img for ID_Area----------------#
            point1_ID_Area = np.float32(ID_Contours)
            # print(point1_ID_Area)
            point2_ID_Area = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
            matrix_ID_Area = cv2.getPerspectiveTransform(point1_ID_Area, point2_ID_Area)
            imgWarpColorID = cv2.warpPerspective(imgWarpArea1, matrix_ID_Area, (widthImg, heightImg))

            imgWarpGrayID = cv2.cvtColor(imgWarpColorID, cv2.COLOR_BGR2GRAY)
            ret_ID, imgThresh_ID = cv2.threshold(imgWarpGrayID, 125, 255, cv2.THRESH_BINARY_INV)
            # cv2.imshow("ID", imgWarpColorID)

            boxes_ID = utlis.splitBoxes(imgThresh_ID, 6, 10)
            # cv2.imshow("CC", boxes_ID[30])
            PixelBox_ID = np.zeros((6, 10))
            cntRows = cntCols = 0
            for box in boxes_ID:
                totalPixel = cv2.countNonZero(box)
                PixelBox_ID[cntCols][cntRows] = totalPixel
                cntRows += 1
                if (cntRows == 10):
                    cntCols += 1
                    cntRows = 0
            Index_ID = []
            for x in range(0, 6):
                arr = PixelBox_ID[x]
                IndexVal = np.where(arr == np.amax(arr))
                Index_ID.append(IndexVal[0][0])
            # print(Index_ID)
            StudentID = Index_ID

            # imgIDRes = imgWarpColorID.copy()
            # imgIDRes = utlis.showIDorCode(imgIDRes, Index_ID, 6, 10)

            imgRawID = np.zeros_like(imgWarpColorID)
            imgRawID = utlis.showIDorCode(imgRawID, Index_ID, 6, 10)

            invMatrix_ID = cv2.getPerspectiveTransform(point2_ID_Area, point1_ID_Area)
            imgInvWarpID = cv2.warpPerspective(imgRawID, invMatrix_ID, (widthImg, heightImg))

            invMatrix_Area1 = cv2.getPerspectiveTransform(point2_Area1, point1_Area1)
            imgInvWarp_Area1_ID = cv2.warpPerspective(imgInvWarpID, invMatrix_Area1, (heightImg, widthImg))

            # ------------------- Exam Code Processing------------------#
            point1_Code_Area = np.float32(Code_Contours)
            point2_Code_Area = np.float32([[0, 0], [widthImg / 2, 0], [0, heightImg], [widthImg / 2, heightImg]])

            matrix_Code_Area = cv2.getPerspectiveTransform(point1_Code_Area, point2_Code_Area)
            imgWarpColorCode = cv2.warpPerspective(imgWarpArea1, matrix_Code_Area, (round(widthImg / 2), heightImg))
            # cv2.imshow("imgWarpColorCode", imgWarpColorCode)
            imgWarpGrayCode = cv2.cvtColor(imgWarpColorCode, cv2.COLOR_BGR2GRAY)
            ret_Code, imgThresh_Code = cv2.threshold(imgWarpGrayCode, 125, 255, cv2.THRESH_BINARY_INV)
            # cv2.imshow("Thresh code", imgThresh_Code)

            boxes_Code = utlis.splitBoxes(imgThresh_Code, 3, 10)
            # cv2.imshow("box10", boxes_Code[10])
            PixelBox_Code = np.zeros((3, 10))
            cntRows = cntCols = 0
            for box in boxes_Code:
                totalPixel = cv2.countNonZero(box)
                PixelBox_Code[cntCols][cntRows] = totalPixel
                cntRows += 1
                if (cntRows == 10):
                    cntCols += 1
                    cntRows = 0
            Index_Code = []
            for x in range(0, 3):
                arr = PixelBox_Code[x]
                IndexVal = np.where(arr == np.amax(arr))
                Index_Code.append(IndexVal[0][0])
            # print(Index_Code)
            CodeExam = Index_Code
            # print(PixelBox_Code)

            # --------------------Show results------------------#
            imgRawCode = np.zeros_like(imgWarpColorCode)
            imgRawCode = utlis.showIDorCode(imgRawCode, Index_Code, 3, 10)

            invMatrix_Code = cv2.getPerspectiveTransform(point2_Code_Area, point1_Code_Area)
            imgInvWarpCode = cv2.warpPerspective(imgRawCode, invMatrix_Code, (widthImg, heightImg))

            invMatrix_Area1 = cv2.getPerspectiveTransform(point2_Area1, point1_Area1)
            imgInvWarp_Area1_Code = cv2.warpPerspective(imgInvWarpCode, invMatrix_Area1, (heightImg, widthImg))

            # --------------Result ID and Code----------------#

            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarp_Area1_Code, 1, 0)
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarp_Area1_ID, 1, 0)
            # cv2.imshow("Final", imgFinal)

        # ---------------Area 2 has MCQs------------------#

        point1_Area2 = np.float32(
            [[0, widthImg / 2 + 40], [heightImg, widthImg / 2 + 40], [0, widthImg], [heightImg, widthImg]])
        point2_Area2 = np.float32([[0, 0], [heightImg, 0], [0, widthImg], [heightImg, widthImg]])
        matrix_Area2 = cv2.getPerspectiveTransform(point1_Area2, point2_Area2)
        imgWarpArea2 = cv2.warpPerspective(imgCropProcess, matrix_Area2, (heightImg, widthImg))
        imgWarpArea2_Canny = cv2.warpPerspective(imgCropProcess_Canny, matrix_Area2, (heightImg, widthImg))

        # cv2.imshow("imgWarpArea2", imgWarpArea2)

        # divide 4 for each 10 answers
        # 1 - 10
        p1_1 = np.float32([[0, 0], [heightImg / 4, 0], [0, widthImg - 30], [heightImg / 4, widthImg - 30]])
        p2_1 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix2_1 = cv2.getPerspectiveTransform(p1_1, p2_1)
        imgWarp2_1 = cv2.warpPerspective(imgWarpArea2, matrix2_1, (widthImg, heightImg))
        imgWarp2_1_Canny = cv2.warpPerspective(imgWarpArea2_Canny, matrix2_1, (widthImg, heightImg))

        Contours_21, hierarchy_2_1 = cv2.findContours(imgWarp2_1_Canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectCon_2_1 = utlis.rectangeContour(Contours_21, 50000, 1000000)
        if (len(rectCon_2_1) != 0):
            Contours_2_1 = utlis.getCornerPoints(rectCon_2_1[0])
            # cv2.drawContours(imgWarp2_1, rectCon_2_1, -1, (255, 0, 0), 3)
        else:
            Contours_2_1 = Example_Contours_Corners

        # cv2.imshow("CCcc", imgWarp2_1_Canny)
        Contours_2_1 = utlis.reorder(Contours_2_1)

        imgContours_2_1 = imgWarp2_1.copy()

        cv2.drawContours(imgContours_2_1, rectCon_2_1, -1, (0, 255, 0), 3)
        # cv2.imshow("Contours_2_1", imgContours_2_1)
        if Contours_2_1.size != 0:
            p1_1_c = np.float32(Contours_2_1)
            p2_1_c = np.float32([[0, 0], [heightImg / 4, 0], [0, widthImg], [heightImg / 4, widthImg]])
            matrix2_1_c = cv2.getPerspectiveTransform(p1_1_c, p2_1_c)
            imgWarpColor2_1 = cv2.warpPerspective(imgWarp2_1, matrix2_1_c, (round(heightImg / 4), widthImg))
            imgWarpGray2_1 = cv2.cvtColor(imgWarpColor2_1, cv2.COLOR_BGR2GRAY)
            ret_Code, imgThresh2_1 = cv2.threshold(imgWarpGray2_1, 120, 255, cv2.THRESH_BINARY_INV)

            boxes2_1 = utlis.splitBoxes_MCQs(imgThresh2_1, 5, 10)
            # cv2.imshow("boxes",boxes2_1[36])
            PixelBox2_1 = np.zeros((10, 4))
            cntRows = cntCols = 0
            for box in boxes2_1:
                totalPixel = cv2.countNonZero(box)
                PixelBox2_1[cntRows][cntCols] = totalPixel
                cntCols += 1
                if (cntCols == 4):
                    cntCols = 0
                    cntRows += 1
            Ans2_1 = []
            for x in range(0, 10):
                arr = PixelBox2_1[x]
                IndexVal = np.where(arr == np.amax(arr))
                Ans2_1.append(IndexVal[0][0])
            # print(Ans2_1)
            Student_Ans.extend(Ans2_1)

            # ---------- Show results-------------#
            imgRaw2_1 = np.zeros_like(imgWarpColor2_1)
            imgRaw2_1 = utlis.showAnswer(imgRaw2_1, Ans2_1, 4, 10)

            invMatrix2_1_c = cv2.getPerspectiveTransform(p2_1_c, p1_1_c)
            imgInvWarp2_1_c = cv2.warpPerspective(imgRaw2_1, invMatrix2_1_c, (widthImg, heightImg))
            # cv2.imshow("imgInvWarp2_1", imgInvWarp2_1)
            # imginv2_1= utlis.stackImages(0.5, [[imgInvWarp2_1]])
            # cv2.imshow("imginvwarp21", imginv2_1)
            invMatrixWarp2_1 = cv2.getPerspectiveTransform(p2_1, p1_1)
            imgInvWarp2_1 = cv2.warpPerspective(imgInvWarp2_1_c, invMatrixWarp2_1, (heightImg, widthImg))

            invMatrixWarpArea2 = cv2.getPerspectiveTransform(point2_Area2, point1_Area2)
            imgInvWarpArea2 = cv2.warpPerspective(imgInvWarp2_1, invMatrixWarpArea2, (heightImg, widthImg))
            # res= utlis.stackImages(0.5, [[imgInvWarpArea2]])
            #
            # cv2.imshow("res", res)
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarpArea2, 1, 0)
            Example_Contours_Corners = Contours_2_1

            # 11 - 20
        p1_2 = np.float32(
            [[heightImg / 4, 0], [heightImg / 2, 0], [heightImg / 4, widthImg - 30], [heightImg / 2, widthImg - 30]])
        p2_2 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix2_2 = cv2.getPerspectiveTransform(p1_2, p2_2)
        imgWarp2_2 = cv2.warpPerspective(imgWarpArea2, matrix2_2, (widthImg, heightImg))
        imgWarp2_2_Canny = cv2.warpPerspective(imgWarpArea2_Canny, matrix2_2, (widthImg, heightImg))
        # cv2.imshow("imgWarp2_2", imgWarp2_2)
        Contours_22, hierarchy_2_2 = cv2.findContours(imgWarp2_2_Canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectCon_2_2 = utlis.rectangeContour(Contours_22, 50000, 1000000)
        if (len(rectCon_2_2) != 0):
            Contours_2_2 = utlis.getCornerPoints(rectCon_2_1[0])
        else:
            Contours_2_2 = Example_Contours_Corners
        Contours_2_2 = utlis.reorder(Contours_2_2)
        imgContours_2_2 = imgWarp2_2.copy()

        cv2.drawContours(imgContours_2_2, rectCon_2_2, -1, (0, 255, 0), 3)
        # cv2.imshow("Contours_2_2", imgContours_2_2)
        if Contours_2_2.size != 0:
            p1_2_c = np.float32(Contours_2_2)
            p2_2_c = np.float32([[0, 0], [heightImg / 4, 0], [0, widthImg], [heightImg / 4, widthImg]])
            matrix2_2_c = cv2.getPerspectiveTransform(p1_2_c, p2_2_c)
            imgWarpColor2_2 = cv2.warpPerspective(imgWarp2_2, matrix2_2_c, (round(heightImg / 4), widthImg))
            imgWarpGray2_2 = cv2.cvtColor(imgWarpColor2_2, cv2.COLOR_BGR2GRAY)
            ret_Code, imgThresh2_2 = cv2.threshold(imgWarpGray2_2, 120, 255, cv2.THRESH_BINARY_INV)

            boxes2_2 = utlis.splitBoxes_MCQs(imgThresh2_2, 5, 10)
            # cv2.imshow("boxes",boxes2_1[36])
            PixelBox2_2 = np.zeros((10, 4))
            cntRows = cntCols = 0
            for box in boxes2_2:
                totalPixel = cv2.countNonZero(box)
                PixelBox2_2[cntRows][cntCols] = totalPixel
                cntCols += 1
                if (cntCols == 4):
                    cntCols = 0
                    cntRows += 1
            Ans2_2 = []
            for x in range(0, 10):
                arr = PixelBox2_2[x]
                IndexVal = np.where(arr == np.amax(arr))
                Ans2_2.append(IndexVal[0][0])
            # print(Ans2_2)
            Student_Ans.extend(Ans2_2)

            # ---------- Show results-------------#
            imgRaw2_2 = np.zeros_like(imgWarpColor2_2)
            imgRaw2_2 = utlis.showAnswer(imgRaw2_2, Ans2_2, 4, 10)

            invMatrix2_2_c = cv2.getPerspectiveTransform(p2_2_c, p1_2_c)
            imgInvWarp2_2_c = cv2.warpPerspective(imgRaw2_2, invMatrix2_2_c, (widthImg, heightImg))
            # cv2.imshow("imgInvWarp2_2", imgInvWarp2_2)
            # imginv2_2= utlis.stackImages(0.5, [[imgInvWarp2_2]])
            # cv2.imshow("imginvwarp22", imginv2_2)
            invMatrixWarp2_2 = cv2.getPerspectiveTransform(p2_2, p1_2)
            imgInvWarp2_2 = cv2.warpPerspective(imgInvWarp2_2_c, invMatrixWarp2_2, (heightImg, widthImg))

            invMatrixWarpArea2 = cv2.getPerspectiveTransform(point2_Area2, point1_Area2)
            imgInvWarpArea2 = cv2.warpPerspective(imgInvWarp2_2, invMatrixWarpArea2, (heightImg, widthImg))
            res = utlis.stackImages(0.5, [[imgInvWarpArea2]])

            # cv2.imshow("res2", res)
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarpArea2, 1, 0)

            # 21 - 30
        p1_3 = np.float32([[heightImg / 2, 0], [heightImg / 4 * 3, 0], [heightImg / 2, widthImg - 30],
                           [heightImg / 4 * 3, widthImg - 30]])
        p2_3 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix2_3 = cv2.getPerspectiveTransform(p1_3, p2_3)
        imgWarp2_3 = cv2.warpPerspective(imgWarpArea2, matrix2_3, (widthImg, heightImg))
        imgWarp2_3_Canny = cv2.warpPerspective(imgWarpArea2_Canny, matrix2_3, (widthImg, heightImg))
        # cv2.imshow("imgWarp2_3", imgWarp2_3)
        Contours_23, hierarchy_2_3 = cv2.findContours(imgWarp2_3_Canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectCon_2_3 = utlis.rectangeContour(Contours_23, 50000, 1000000)
        if (len(rectCon_2_3) != 0):
            Contours_2_3 = utlis.getCornerPoints(rectCon_2_3[0])
        else:
            Contours_2_3 = Example_Contours_Corners
        Contours_2_3 = utlis.reorder(Contours_2_3)
        imgContours_2_3 = imgWarp2_3.copy()

        cv2.drawContours(imgContours_2_3, rectCon_2_3, -1, (0, 255, 0), 3)
        # cv2.imshow("Contours_2_3", imgContours_2_3)
        if Contours_2_3.size != 0:
            p1_3_c = np.float32(Contours_2_3)
            p2_3_c = np.float32([[0, 0], [heightImg / 4, 0], [0, widthImg], [heightImg / 4, widthImg]])
            matrix2_3_c = cv2.getPerspectiveTransform(p1_3_c, p2_3_c)
            imgWarpColor2_3 = cv2.warpPerspective(imgWarp2_3, matrix2_3_c, (round(heightImg / 4), widthImg))
            imgWarpGray2_3 = cv2.cvtColor(imgWarpColor2_3, cv2.COLOR_BGR2GRAY)
            ret_Code, imgThresh2_3 = cv2.threshold(imgWarpGray2_3, 120, 255, cv2.THRESH_BINARY_INV)

            boxes2_3 = utlis.splitBoxes_MCQs(imgThresh2_3, 5, 10)
            # cv2.imshow("boxes",boxes2_1[36])
            PixelBox2_3 = np.zeros((10, 4))
            cntRows = cntCols = 0
            for box in boxes2_3:
                totalPixel = cv2.countNonZero(box)
                PixelBox2_3[cntRows][cntCols] = totalPixel
                cntCols += 1
                if (cntCols == 4):
                    cntCols = 0
                    cntRows += 1
            Ans2_3 = []
            for x in range(0, 10):
                arr = PixelBox2_3[x]
                IndexVal = np.where(arr == np.amax(arr))
                Ans2_3.append(IndexVal[0][0])
            # print(Ans2_3)
            Student_Ans.extend(Ans2_3)

            # ---------- Show results-------------#
            imgRaw2_3 = np.zeros_like(imgWarpColor2_3)
            imgRaw2_3 = utlis.showAnswer(imgRaw2_3, Ans2_3, 4, 10)

            invMatrix2_3_c = cv2.getPerspectiveTransform(p2_3_c, p1_3_c)
            imgInvWarp2_3_c = cv2.warpPerspective(imgRaw2_3, invMatrix2_3_c, (widthImg, heightImg))
            # cv2.imshow("imgInvWarp2_3", imgInvWarp2_3)
            # imginv2_3= utlis.stackImages(0.5, [[imgInvWarp2_3]])
            # cv2.imshow("imginvwarp23", imginv2_3)
            invMatrixWarp2_3 = cv2.getPerspectiveTransform(p2_3, p1_3)
            imgInvWarp2_3 = cv2.warpPerspective(imgInvWarp2_3_c, invMatrixWarp2_3, (heightImg, widthImg))

            invMatrixWarpArea2 = cv2.getPerspectiveTransform(point2_Area2, point1_Area2)
            imgInvWarpArea2 = cv2.warpPerspective(imgInvWarp2_3, invMatrixWarpArea2, (heightImg, widthImg))
            res = utlis.stackImages(0.5, [[imgInvWarpArea2]])

            # cv2.imshow("res3", res)
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarpArea2, 1, 0)

            # 31 - 40
        p1_4 = np.float32(
            [[heightImg / 4 * 3, 0], [heightImg, 0], [heightImg / 4 * 3, widthImg - 30], [heightImg, widthImg - 30]])
        p2_4 = np.float32([[0, 0], [widthImg, 0], [0, heightImg], [widthImg, heightImg]])
        matrix2_4 = cv2.getPerspectiveTransform(p1_4, p2_4)
        imgWarp2_4 = cv2.warpPerspective(imgWarpArea2, matrix2_4, (widthImg, heightImg))
        imgWarp2_4_Canny = cv2.warpPerspective(imgWarpArea2_Canny, matrix2_4, (widthImg, heightImg))
        # cv2.imshow("imgWarp2_4", imgWarp2_4)
        Contours_24, hierarchy_2_4 = cv2.findContours(imgWarp2_4_Canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        rectCon_2_4 = utlis.rectangeContour(Contours_24, 50000, 1000000)
        if (len(rectCon_2_4) != 0):
            Contours_2_4 = utlis.getCornerPoints(rectCon_2_4[0])
        else:
            Contours_2_4 = Example_Contours_Corners
        Contours_2_4 = utlis.reorder(Contours_2_4)
        imgContours_2_4 = imgWarp2_4.copy()

        cv2.drawContours(imgContours_2_4, rectCon_2_4, -1, (0, 255, 0), 3)
        # cv2.imshow("Contours_2_4", imgContours_2_4)
        if Contours_2_4.size != 0:
            p1_4_c = np.float32(Contours_2_4)
            p2_4_c = np.float32([[0, 0], [heightImg / 4, 0], [0, widthImg], [heightImg / 4, widthImg]])
            matrix2_4_c = cv2.getPerspectiveTransform(p1_4_c, p2_4_c)
            imgWarpColor2_4 = cv2.warpPerspective(imgWarp2_4, matrix2_4_c, (round(heightImg / 4), widthImg))
            imgWarpGray2_4 = cv2.cvtColor(imgWarpColor2_4, cv2.COLOR_BGR2GRAY)
            ret_Code, imgThresh2_4 = cv2.threshold(imgWarpGray2_4, 120, 255, cv2.THRESH_BINARY_INV)

            boxes2_4 = utlis.splitBoxes_MCQs(imgThresh2_4, 5, 10)
            # cv2.imshow("boxes",boxes2_1[36])
            PixelBox2_4 = np.zeros((10, 4))
            cntRows = cntCols = 0
            for box in boxes2_4:
                totalPixel = cv2.countNonZero(box)
                PixelBox2_4[cntRows][cntCols] = totalPixel
                cntCols += 1
                if (cntCols == 4):
                    cntCols = 0
                    cntRows += 1
            Ans2_4 = []
            for x in range(0, 10):
                arr = PixelBox2_4[x]
                IndexVal = np.where(arr == np.amax(arr))
                Ans2_4.append(IndexVal[0][0])
            # print(Ans2_4)
            Student_Ans.extend(Ans2_4)

            # ---------- Show results-------------#
            imgRaw2_4 = np.zeros_like(imgWarpColor2_4)
            imgRaw2_4 = utlis.showAnswer(imgRaw2_4, Ans2_4, 4, 10)

            invMatrix2_4_c = cv2.getPerspectiveTransform(p2_4_c, p1_4_c)
            imgInvWarp2_4_c = cv2.warpPerspective(imgRaw2_4, invMatrix2_4_c, (widthImg, heightImg))
            # cv2.imshow("imgInvWarp2_4", imgInvWarp2_4)
            # imginv2_4= utlis.stackImages(0.5, [[imgInvWarp2_4]])
            # cv2.imshow("imginvwarp24", imginv2_4)
            invMatrixWarp2_4 = cv2.getPerspectiveTransform(p2_4, p1_4)
            imgInvWarp2_4 = cv2.warpPerspective(imgInvWarp2_4_c, invMatrixWarp2_4, (heightImg, widthImg))

            invMatrixWarpArea2 = cv2.getPerspectiveTransform(point2_Area2, point1_Area2)
            imgInvWarpArea2 = cv2.warpPerspective(imgInvWarp2_4, invMatrixWarpArea2, (heightImg, widthImg))
            res = utlis.stackImages(0.5, [[imgInvWarpArea2]])

            # cv2.imshow("res4", res)
            imgFinal = cv2.addWeighted(imgFinal, 1, imgInvWarpArea2, 1, 0)

        imgRes = utlis.stackImages(0.7, [[imgFinal]])
        name = ''
        for k in StudentID:
            name = name + str(k)
        # cv2.imshow("result", imgRes)

        cv2.imwrite(os.path.join('./Image_Result', name + ".png"), imgFinal)

        # print("Student Ans = ", Student_Ans)
        # print("Student ID = ", StudentID)
        # print("Code Exam = ", CodeExam)
        cv2.destroyAllWindows()


        return StudentID, Student_Ans, CodeExam

    except Exception as e:
        print(e)
        # if (flag == 0):
        #     cv2.imwrite(os.path.join('./tmp', str(random.randint(0, 999)) + ".png"), image)
        # else:
        #     cv2.imwrite(os.path.join('./Fault', str(random.randint(0, 999)) + ".png"), image)
        if (flag):
            cv2.imwrite(os.path.join('./Fault', str(random.randint(0, 999)) + ".png"), image)
        return 0, 0, 0


