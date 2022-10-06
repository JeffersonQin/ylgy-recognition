import cv2
import numpy as np

import win32gui
import win32ui
import win32con
import win32api

from mss import mss

bg_color = (36, 50, 255)
resize = (100, 100)
size_thres_ratio = 1440
identical_thres = 12000
dpi_scale = 1.25
file_name = 'monitor-1.png'


def mse(img1, img2):
	r1 = cv2.resize(img1, resize)
	r2 = cv2.resize(img2, resize)
	err = np.sum((r1.astype("float") - r2.astype("float")) ** 2)
	err /= float(resize[0] * resize[1])
	return err


while True:
	hwnd = win32gui.FindWindow(None, u'羊了个羊')
	# get window position
	rect = win32gui.GetWindowRect(hwnd)
	wx = rect[0]
	wy = rect[1]
	ww = int((rect[2] - wx))
	wh = int((rect[3] - wy))

	with mss() as sct:
		sct.shot()

	src = cv2.imread(file_name)[wy:wy + wh, wx:wx + ww]
	src_notate = src.copy()
	size_thres = int(src.shape[0] * src.shape[1] / size_thres_ratio)
	hsv = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
	bg = cv2.inRange(hsv, bg_color, bg_color)

	num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bg, connectivity=4, ltype=cv2.CV_32S)
	bitmap_key_list = []
	true_index_list = []

	for i in range(0, num_labels):
		if stats[i, cv2.CC_STAT_WIDTH] * stats[i, cv2.CC_STAT_HEIGHT] < size_thres:
			continue
		if bg[labels == i][0] != 255:
			continue
		# draw rect
		x, y, w, h = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
		cv2.rectangle(src_notate, (x, y), (x + w, y + h), (0, 0, 255), 2)
		# cv2.putText(src_notate, str(i), (stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
		subgraph = src[y:y + h, x:x + w]
		if len(bitmap_key_list) == 0:
			bitmap_key_list.append(subgraph)
			true_index_list.append([i])
		else:
			for j, bitmap in enumerate(bitmap_key_list):
				if mse(bitmap, subgraph) < identical_thres:
					true_index_list[j].append(i)
					break
			else:
				bitmap_key_list.append(subgraph)
				true_index_list.append([i])

	for i, index_list in enumerate(true_index_list):
		random_color = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
		for j in index_list:
			x, y, w, h = stats[j, cv2.CC_STAT_LEFT], stats[j, cv2.CC_STAT_TOP], stats[j, cv2.CC_STAT_WIDTH], stats[j, cv2.CC_STAT_HEIGHT]
			cv2.putText(src_notate, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, random_color, 2)
			cv2.rectangle(src_notate, (x, y), (x + w, y + h), random_color, 2)
		

	cv2.imshow("notate", src_notate)

	cv2.waitKey(1)
