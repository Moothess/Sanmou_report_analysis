import sys
import cv2
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore


class ColorThresholdApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("颜色阈值演示 (HSV)")
        self.resize(1100, 650)

        # 状态
        self.image_bgr = None
        self.image_rgb = None
        self.image_hsv = None
        self.orig_pixmap = None
        self.result_pixmap = None

        # 顶层容器
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # 工具条区域
        tool_layout = QtWidgets.QHBoxLayout()
        self.btn_open = QtWidgets.QPushButton("打开图片")
        self.btn_reset = QtWidgets.QPushButton("重置")
        self.cb_show_mask = QtWidgets.QCheckBox("显示掩膜(黑白)")
        tool_layout.addWidget(self.btn_open)
        tool_layout.addWidget(self.btn_reset)
        tool_layout.addStretch(1)
        tool_layout.addWidget(self.cb_show_mask)
        main_layout.addLayout(tool_layout)

        # 图片显示区域
        view_layout = QtWidgets.QHBoxLayout()
        self.lbl_orig = QtWidgets.QLabel("原图")
        self.lbl_result = QtWidgets.QLabel("阈值结果")
        for lbl in (self.lbl_orig, self.lbl_result):
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("QLabel { background: #222; color: #ddd; border: 1px solid #444; }")
            lbl.setMinimumSize(320, 240)
        view_layout.addWidget(self.lbl_orig, 1)
        view_layout.addWidget(self.lbl_result, 1)
        main_layout.addLayout(view_layout, 1)

        # 控件：HSV/BGR 上下限
        panel = QtWidgets.QGroupBox("HSV/BGR 颜色阈值")
        panel_layout = QtWidgets.QHBoxLayout(panel)
        self.spins = {}

        # 左：HSV
        panel_hsv = QtWidgets.QGroupBox("HSV")
        grid_hsv = QtWidgets.QGridLayout(panel_hsv)
        hsv_defs = [
            ("H 下限", "h_low", 0, 179, 0),
            ("H 上限", "h_high", 0, 179, 179),
            ("S 下限", "s_low", 0, 255, 0),
            ("S 上限", "s_high", 0, 255, 255),
            ("V 下限", "v_low", 0, 255, 0),
            ("V 上限", "v_high", 0, 255, 255),
        ]
        for row, (text, key, mn, mx, val) in enumerate(hsv_defs):
            lbl = QtWidgets.QLabel(text)
            spin = QtWidgets.QSpinBox()
            spin.setRange(mn, mx)
            spin.setValue(val)
            spin.valueChanged.connect(self.on_threshold_change)
            self.spins[key] = spin
            grid_hsv.addWidget(lbl, row, 0)
            grid_hsv.addWidget(spin, row, 1)

        # 右：BGR
        panel_bgr = QtWidgets.QGroupBox("BGR")
        grid_bgr = QtWidgets.QGridLayout(panel_bgr)
        bgr_defs = [
            ("B 下限", "b_low", 0, 255, 0),
            ("B 上限", "b_high", 0, 255, 255),
            ("G 下限", "g_low", 0, 255, 0),
            ("G 上限", "g_high", 0, 255, 255),
            ("R 下限", "r_low", 0, 255, 0),
            ("R 上限", "r_high", 0, 255, 255),
        ]
        for row, (text, key, mn, mx, val) in enumerate(bgr_defs):
            lbl = QtWidgets.QLabel(text)
            spin = QtWidgets.QSpinBox()
            spin.setRange(mn, mx)
            spin.setValue(val)
            spin.valueChanged.connect(self.on_threshold_change)
            self.spins[key] = spin
            grid_bgr.addWidget(lbl, row, 0)
            grid_bgr.addWidget(spin, row, 1)

        panel_layout.addWidget(panel_hsv, 1)
        panel_layout.addWidget(panel_bgr, 1)
        main_layout.addWidget(panel)

        # 连接信号
        self.btn_open.clicked.connect(self.open_image)
        self.btn_reset.clicked.connect(self.reset_thresholds)
        self.cb_show_mask.toggled.connect(self.update_result)

        # 互斥边界：确保 low <= high
        self.spins["h_low"].valueChanged.connect(lambda v: self.sync_bounds("h_low", "h_high"))
        self.spins["h_high"].valueChanged.connect(lambda v: self.sync_bounds("h_low", "h_high"))
        self.spins["s_low"].valueChanged.connect(lambda v: self.sync_bounds("s_low", "s_high"))
        self.spins["s_high"].valueChanged.connect(lambda v: self.sync_bounds("s_low", "s_high"))
        self.spins["v_low"].valueChanged.connect(lambda v: self.sync_bounds("v_low", "v_high"))
        self.spins["v_high"].valueChanged.connect(lambda v: self.sync_bounds("v_low", "v_high"))
        # BGR 边界互斥
        self.spins["b_low"].valueChanged.connect(lambda v: self.sync_bounds("b_low", "b_high"))
        self.spins["b_high"].valueChanged.connect(lambda v: self.sync_bounds("b_low", "b_high"))
        self.spins["g_low"].valueChanged.connect(lambda v: self.sync_bounds("g_low", "g_high"))
        self.spins["g_high"].valueChanged.connect(lambda v: self.sync_bounds("g_low", "g_high"))
        self.spins["r_low"].valueChanged.connect(lambda v: self.sync_bounds("r_low", "r_high"))
        self.spins["r_high"].valueChanged.connect(lambda v: self.sync_bounds("r_low", "r_high"))

    def sync_bounds(self, low_key, high_key):
        low = self.spins[low_key].value()
        high = self.spins[high_key].value()
        # 限制范围
        if low > high:
            # 简单策略：推高 high
            self.spins[high_key].setValue(low)
        # 动态约束，避免来回越界
        self.spins[high_key].setMinimum(self.spins[low_key].value())
        self.spins[low_key].setMaximum(self.spins[high_key].value())

    def open_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;All Files (*)"
        )
        if not path:
            return
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is not None:
            pass
            #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            #_, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
            #img = img * (binary > 0)[..., None].astype(img.dtype)
        if img is None:
            QtWidgets.QMessageBox.warning(self, "错误", "无法读取图片。")
            return
        self.image_bgr = img
        self.image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.image_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 显示原图
        self.orig_pixmap = self.cv_to_qpixmap(self.image_rgb)
        self.set_scaled_pixmap(self.lbl_orig, self.orig_pixmap)
        # 更新结果
        self.update_result()

    def reset_thresholds(self):
        # 常用默认：全范围
        self.spins["h_low"].setValue(0)
        self.spins["h_high"].setValue(179)
        self.spins["s_low"].setValue(0)
        self.spins["s_high"].setValue(255)
        self.spins["v_low"].setValue(0)
        self.spins["v_high"].setValue(255)
        # BGR 全范围
        self.spins["b_low"].setValue(0)
        self.spins["b_high"].setValue(255)
        self.spins["g_low"].setValue(0)
        self.spins["g_high"].setValue(255)
        self.spins["r_low"].setValue(0)
        self.spins["r_high"].setValue(255)
        self.update_result()

    def on_threshold_change(self, _):
        self.update_result()

    def update_result(self):
        if self.image_hsv is None:
            return
        # HSV mask
        h_low = self.spins["h_low"].value(); h_high = self.spins["h_high"].value()
        s_low = self.spins["s_low"].value(); s_high = self.spins["s_high"].value()
        v_low = self.spins["v_low"].value(); v_high = self.spins["v_high"].value()
        lower_hsv = np.array([h_low, s_low, v_low], dtype=np.uint8)
        upper_hsv = np.array([h_high, s_high, v_high], dtype=np.uint8)
        mask_hsv = cv2.inRange(self.image_hsv, lower_hsv, upper_hsv)

        # BGR mask
        b_low = self.spins["b_low"].value(); b_high = self.spins["b_high"].value()
        g_low = self.spins["g_low"].value(); g_high = self.spins["g_high"].value()
        r_low = self.spins["r_low"].value(); r_high = self.spins["r_high"].value()
        lower_bgr = np.array([b_low, g_low, r_low], dtype=np.uint8)
        upper_bgr = np.array([b_high, g_high, r_high], dtype=np.uint8)
        mask_bgr = cv2.inRange(self.image_bgr, lower_bgr, upper_bgr)

        # 取交集
        mask = cv2.bitwise_and(mask_hsv, mask_bgr)

        if self.cb_show_mask.isChecked():
            # 显示黑白掩膜
            qimg = QtGui.QImage(
                mask.data, mask.shape[1], mask.shape[0], mask.strides[0], QtGui.QImage.Format_Grayscale8
            )
            self.result_pixmap = QtGui.QPixmap.fromImage(qimg)
        else:
            # 显示着色后的结果
            res_bgr = cv2.bitwise_and(self.image_bgr, self.image_bgr, mask=mask)
            res_rgb = cv2.cvtColor(res_bgr, cv2.COLOR_BGR2RGB)
            self.result_pixmap = self.cv_to_qpixmap(res_rgb)

        self.set_scaled_pixmap(self.lbl_result, self.result_pixmap)

    def cv_to_qpixmap(self, rgb_img: np.ndarray) -> QtGui.QPixmap:
        h, w, ch = rgb_img.shape
        bytes_per_line = ch * w
        qimg = QtGui.QImage(rgb_img.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        return QtGui.QPixmap.fromImage(qimg)

    def set_scaled_pixmap(self, label: QtWidgets.QLabel, pix: QtGui.QPixmap):
        if pix is None:
            label.clear()
            return
        scaled = pix.scaled(label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        label.setPixmap(scaled)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        if self.orig_pixmap is not None:
            self.set_scaled_pixmap(self.lbl_orig, self.orig_pixmap)
        if self.result_pixmap is not None:
            self.set_scaled_pixmap(self.lbl_result, self.result_pixmap)


def main():
    # 启用高分屏缩放
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)

    app = QtWidgets.QApplication(sys.argv)
    # 全局字体大小（可调成 16/18）
    app.setFont(QtGui.QFont("", 14))

    w = ColorThresholdApp()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
