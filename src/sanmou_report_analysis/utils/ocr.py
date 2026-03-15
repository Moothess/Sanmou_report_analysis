# Author: Mian Qin
# Date Created: 2025/1/3

import logging

from paddleocr import PaddleOCR

from sanmou_report_analysis.utils.data_structure import OCRResult

# from utils import NestedText
# import utils

OCRer = PaddleOCR(use_gpu=True, lang="ch", show_log=False, use_angle_cls=False)
OCRer_number = PaddleOCR(use_gpu=True, lang="en", show_log=False, use_angle_cls=False)
logging.getLogger("ppocr").setLevel(logging.ERROR)


def ocr_text(image, save=False) -> list[OCRResult]:
    results = OCRer.ocr(image)[0]
    ocr_results: list[OCRResult] = []
    if results is not None:
        for result in results:
            corners = result[0]
            left = int(corners[0][0])
            right = int(corners[1][0])
            top = int(corners[0][1])
            bottom = int(corners[2][1])
            text = result[1][0]
            ocr_result = OCRResult((left, top, right, bottom), text)
            ocr_result.box.expand(5, 5)
            ocr_results.append(ocr_result)
    return ocr_results


def ocr_number(image, save=False) -> list[OCRResult]:
    results = OCRer_number.ocr(image)[0]
    ocr_results: list[OCRResult] = []
    if results is not None:
        for result in results:
            corners = result[0]
            left = int(corners[0][0])
            right = int(corners[1][0])
            top = int(corners[0][1])
            bottom = int(corners[2][1])
            text = result[1][0]
            ocr_result = OCRResult((left, top, right, bottom), text)
            ocr_result.box.expand(5, 5)
            ocr_results.append(ocr_result)
    return ocr_results
