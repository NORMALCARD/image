import sys
import os
from PIL import Image
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFileDialog, QProgressBar, QGroupBox, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QPixmap, QIcon, QPainter  # 添加了QPainter导入


class ColorSimplifierThread(QThread):
    progress_updated = pyqtSignal(int)
    file_processed = pyqtSignal(str)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, input_path, output_folder, color_hex_list, is_folder):
        super().__init__()
        self.input_path = input_path
        self.output_folder = output_folder
        self.color_hex_list = color_hex_list
        self.is_folder = is_folder
        self.running = True

    def run(self):
        try:
            # 将16进制颜色代码转换为RGB值
            palette = []
            for hex_color in self.color_hex_list:
                hex_color = hex_color.strip().lstrip('#')
                if len(hex_color) == 3:
                    hex_color = ''.join([c * 2 for c in hex_color])
                rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
                palette.append(rgb)

            if not palette:
                self.error_occurred.emit("没有有效的颜色代码！")
                return

            # 处理输入（文件夹或文件）
            if self.is_folder:
                files = [os.path.join(self.input_path, f) for f in os.listdir(self.input_path)
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            else:
                files = [self.input_path]

            total_files = len(files)

            for idx, file_path in enumerate(files):
                if not self.running:
                    break

                try:
                    # 处理单个图像
                    img = Image.open(file_path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    img_array = np.array(img)

                    # 创建一个新数组来存储简化后的图像
                    simplified_array = np.zeros_like(img_array)

                    # 遍历所有像素，找到最接近的颜色
                    height, width, _ = img_array.shape
                    for y in range(height):
                        for x in range(width):
                            pixel = img_array[y, x]
                            min_dist = float('inf')
                            best_color = palette[0]

                            for color in palette:
                                # 计算颜色距离（欧氏距离）
                                dist = np.sqrt(
                                    (pixel[0] - color[0]) ** 2 +
                                    (pixel[1] - color[1]) ** 2 +
                                    (pixel[2] - color[2]) ** 2
                                )
                                if dist < min_dist:
                                    min_dist = dist
                                    best_color = color

                            simplified_array[y, x] = best_color

                    # 保存结果
                    output_path = os.path.join(
                        self.output_folder,
                        f"simplified_{os.path.basename(file_path)}"
                    )
                    simplified_img = Image.fromarray(simplified_array)
                    simplified_img.save(output_path)

                    self.file_processed.emit(os.path.basename(file_path))
                    self.progress_updated.emit(int((idx + 1) / total_files * 100))

                except Exception as e:
                    self.error_occurred.emit(f"处理 {os.path.basename(file_path)} 时出错: {str(e)}")

            self.finished.emit()

        except Exception as e:
            self.error_occurred.emit(f"处理过程中出错: {str(e)}")

    def stop(self):
        self.running = False


class ColorSimplifierApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("颜色简化程序")
        self.setGeometry(100, 100, 800, 600)

        # 设置应用图标
        self.setWindowIcon(QIcon(self.create_color_icon()))

        # 初始化变量
        self.input_path = ""
        self.output_folder = ""
        self.color_hex_list = []
        self.worker_thread = None

        # 创建UI
        self.init_ui()

    def create_color_icon(self):
        """创建程序图标"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)

        # 绘制彩虹色图标
        colors = [
            QColor("#FF0000"),  # 红
            QColor("#FF9900"),  # 橙
            QColor("#FFFF00"),  # 黄
            QColor("#00FF00"),  # 绿
            QColor("#0000FF"),  # 蓝
            QColor("#4B0082"),  # 靛
            QColor("#8F00FF")  # 紫
        ]

        # 创建QPainter对象
        painter = QPainter(pixmap)

        for i, color in enumerate(colors):
            painter.setPen(color)
            painter.setBrush(color)
            painter.drawRect(i * 4, 0, 4, 32)

        # 结束绘制
        painter.end()

        return pixmap

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # 标题
        title_label = QLabel("颜色简化程序")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 输入部分
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout()

        # 输入文件/文件夹选择
        file_layout = QHBoxLayout()
        self.input_label = QLabel("未选择输入")
        self.input_label.setStyleSheet("border: 1px solid #aaa; padding: 5px;")
        file_layout.addWidget(self.input_label)

        file_btn = QPushButton("选择文件")
        file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(file_btn)

        folder_btn = QPushButton("选择文件夹")
        folder_btn.clicked.connect(self.select_folder)
        file_layout.addWidget(folder_btn)

        input_layout.addLayout(file_layout)

        # 输出文件夹选择
        output_layout = QHBoxLayout()
        self.output_label = QLabel("未选择输出文件夹")
        self.output_label.setStyleSheet("border: 1px solid #aaa; padding: 5px;")
        output_layout.addWidget(self.output_label)

        output_btn = QPushButton("选择输出文件夹")
        output_btn.clicked.connect(self.select_output_folder)
        output_layout.addWidget(output_btn)

        input_layout.addLayout(output_layout)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # 颜色设置部分
        color_group = QGroupBox("颜色设置")
        color_layout = QVBoxLayout()

        # 颜色输入
        color_input_layout = QHBoxLayout()
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("输入16进制颜色代码 (例如 #FF0000, #00FF00, #0000FF)，用逗号分隔")
        self.color_input.setStyleSheet("padding: 5px;")
        color_input_layout.addWidget(self.color_input)

        add_color_btn = QPushButton("添加颜色")
        add_color_btn.clicked.connect(self.add_colors)
        color_input_layout.addWidget(add_color_btn)

        color_layout.addLayout(color_input_layout)

        # 颜色列表
        self.color_list = QListWidget()
        self.color_list.setStyleSheet("background-color: #f0f0f0;")
        color_layout.addWidget(self.color_list)

        # 颜色按钮
        color_btn_layout = QHBoxLayout()
        preset_btn = QPushButton("预设颜色")
        preset_btn.clicked.connect(self.add_preset_colors)
        color_btn_layout.addWidget(preset_btn)

        clear_btn = QPushButton("清空颜色")
        clear_btn.clicked.connect(self.clear_colors)
        color_btn_layout.addWidget(clear_btn)

        color_layout.addLayout(color_btn_layout)
        color_group.setLayout(color_layout)
        main_layout.addWidget(color_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #aaa;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # 状态信息
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 处理按钮
        process_layout = QHBoxLayout()
        process_layout.addStretch()

        self.process_btn = QPushButton("开始处理")
        self.process_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.process_btn.clicked.connect(self.start_processing)
        process_layout.addWidget(self.process_btn)

        stop_btn = QPushButton("停止处理")
        stop_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        stop_btn.clicked.connect(self.stop_processing)
        process_layout.addWidget(stop_btn)

        process_layout.addStretch()
        main_layout.addLayout(process_layout)

        # 底部信息
        footer_label = QLabel("© 2023 颜色简化程序 | 基于PyQt5和Pillow开发")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #777; font-size: 10px;")
        main_layout.addWidget(footer_label)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                font-family: Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QListWidget {
                border: 1px solid #aaa;
                border-radius: 4px;
            }
            QLineEdit {
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 5px;
            }
        """)

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file:
            self.input_path = file
            self.input_label.setText(f"已选择文件: {os.path.basename(file)}")
            self.input_label.setToolTip(file)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder:
            self.input_path = folder
            self.input_label.setText(f"已选择文件夹: {os.path.basename(folder)}")
            self.input_label.setToolTip(folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder = folder
            self.output_label.setText(f"输出文件夹: {os.path.basename(folder)}")
            self.output_label.setToolTip(folder)

    def add_colors(self):
        colors = self.color_input.text().split(',')
        valid_colors = []

        for color in colors:
            color = color.strip().lstrip('#')
            if color:
                # 验证是否为有效的16进制颜色代码
                try:
                    if len(color) == 3 or len(color) == 6:
                        int(color, 16)
                        valid_colors.append(f"#{color}")
                    else:
                        QMessageBox.warning(self, "无效颜色", f"'{color}' 不是有效的16进制颜色代码")
                except ValueError:
                    QMessageBox.warning(self, "无效颜色", f"'{color}' 不是有效的16进制颜色代码")

        if valid_colors:
            self.color_hex_list.extend(valid_colors)
            self.update_color_list()
            self.color_input.clear()

    def add_preset_colors(self):
        preset_colors = [
            "#FF0000", "#00FF00", "#0000FF",  # 三原色
            "#FFFF00", "#FF00FF", "#00FFFF",  # 二次色
            "#000000", "#FFFFFF", "#808080",  # 黑白灰
            "#FFA500", "#800080", "#008000"  # 橙紫绿
        ]
        self.color_hex_list.extend(preset_colors)
        self.update_color_list()

    def clear_colors(self):
        self.color_hex_list = []
        self.color_list.clear()

    def update_color_list(self):
        self.color_list.clear()
        for color in self.color_hex_list:
            self.color_list.addItem(color)
            # 设置项的背景颜色
            row = self.color_list.count() - 1
            item = self.color_list.item(row)
            item.setBackground(QColor(color))
            # 根据背景颜色设置文本颜色
            if QColor(color).lightness() < 128:
                item.setForeground(Qt.white)
            else:
                item.setForeground(Qt.black)

    def validate_inputs(self):
        if not self.input_path:
            QMessageBox.warning(self, "输入错误", "请选择输入文件或文件夹")
            return False

        if not self.output_folder:
            QMessageBox.warning(self, "输出错误", "请选择输出文件夹")
            return False

        if not self.color_hex_list:
            QMessageBox.warning(self, "颜色错误", "请添加至少一个颜色代码")
            return False

        return True

    def start_processing(self):
        if not self.validate_inputs():
            return

        # 检查输入路径是否存在
        if not os.path.exists(self.input_path):
            QMessageBox.critical(self, "路径错误", "输入的路径不存在")
            return

        # 检查输出路径是否存在，不存在则创建
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # 确定输入是文件还是文件夹
        is_folder = os.path.isdir(self.input_path)

        # 禁用开始按钮，防止重复启动
        self.process_btn.setEnabled(False)
        self.status_label.setText("处理中...")

        # 创建并启动工作线程
        self.worker_thread = ColorSimplifierThread(
            self.input_path,
            self.output_folder,
            self.color_hex_list,
            is_folder
        )

        # 连接信号
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.file_processed.connect(self.update_status)
        self.worker_thread.finished.connect(self.processing_finished)
        self.worker_thread.error_occurred.connect(self.handle_error)

        self.worker_thread.start()

    def stop_processing(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.status_label.setText("处理已停止")
            self.process_btn.setEnabled(True)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, filename):
        self.status_label.setText(f"处理完成: {filename}")

    def processing_finished(self):
        self.status_label.setText("处理完成！")
        self.process_btn.setEnabled(True)
        QMessageBox.information(self, "完成", "所有图片处理完成！")

    def handle_error(self, error_msg):
        QMessageBox.critical(self, "错误", error_msg)
        self.status_label.setText("处理出错")
        self.process_btn.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorSimplifierApp()
    window.show()
    sys.exit(app.exec_())