# Author: Mian Qin
# Date Created: 2025/1/3
import json
import os

import logging
from paddleocr import PaddleOCR
import cv2

from utils.data_structure import OCRResult
#from utils import NestedText
#import utils

OCRer = PaddleOCR(use_gpu=True, lang='ch', show_log=False, use_angle_cls=False)
#OCRer_number = PaddleOCR(use_gpu=True, lang='en', show_log=False, use_angle_cls=False)
#ColoredOCRer = PaddleOCR(use_gpu=True, lang='en', rec_char_dict_path='images/digit_dict.txt', show_log=False, use_angle_cls=False)
logging.getLogger("ppocr").setLevel(logging.ERROR)

def ocr_text(image, save=False) -> list[OCRResult]:
    results = OCRer.ocr(image)[0]
    ocr_results: list[OCRResult] = []
    if results is not None:
        for result in results:
            corners = result[0]
            l = int(corners[0][0])
            r = int(corners[1][0])
            t = int(corners[0][1])
            b = int(corners[2][1])
            text = result[1][0]
            ocr_result = OCRResult((l, t, r, b), text)
            ocr_result.box.expand(5, 5)
            ocr_results.append(ocr_result)
    return ocr_results


def ocr_number(image, save=False) -> list[OCRResult]:
    results = OCRer_number.ocr(image)[0]
    ocr_results: list[OCRResult] = []
    if results is not None:
        for result in results:
            corners = result[0]
            l = int(corners[0][0])
            r = int(corners[1][0])
            t = int(corners[0][1])
            b = int(corners[2][1])
            text = result[1][0]
            ocr_result = OCRResult((l, t, r, b), text)
            ocr_result.box.expand(5, 5)
            ocr_results.append(ocr_result)
    return ocr_results
