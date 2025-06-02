import PySimpleGUI as sg
import cv2
import numpy as np
from PIL import Image, ImageTk
import io
import os


def extract_main_color(image_path):
    """从图片中提取主要颜色（使用K-means聚类）"""
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 将图像数据重塑为2D数组（像素 x RGB）
    pixel_values = image.reshape((-1, 3))
    pixel_values = np.float32(pixel_values)

    # 使用K-means聚类找到主要颜色
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    k = 1  # 只提取一种主要颜色
    _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # 将颜色值转换为整数
    main_color = centers[0].astype(int)

    # 转换为16进制
    hex_color = "#{:02x}{:02x}{:02x}".format(main_color[0], main_color[1], main_color[2])

    return main_color, hex_color


def rgb_to_hsv(rgb):
    """将RGB颜色转换为HSV颜色空间"""
    r, g, b = [x / 255.0 for x in rgb]
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val

    # 计算色调
    if diff == 0:
        h = 0
    elif max_val == r:
        h = 60 * ((g - b) / diff % 6)
    elif max_val == g:
        h = 60 * ((b - r) / diff + 2)
    else:  # max_val == b
        h = 60 * ((r - g) / diff + 4)

    # 计算饱和度
    s = 0 if max_val == 0 else diff / max_val

    # 计算明度
    v = max_val

    return int(h), int(s * 100), int(v * 100)


def resize_image(image_path, max_size=(400, 400)):
    """调整图像大小以适应预览窗口"""
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


# 设置主题
sg.theme('LightBlue3')

# 布局定义
layout = [
    [sg.Text("图片颜色提取器", font=("Arial", 20), justification='center', expand_x=True)],
    [
        sg.Frame("操作区域", [
            [sg.Text("选择图片:")],
            [sg.InputText(key="-FILE-", size=(40, 1)),
             sg.FileBrowse(file_types=(("图片文件", "*.jpg;*.jpeg;*.png;*.bmp"),))],
            [sg.Button("提取颜色", size=(15, 1)), sg.Button("退出", size=(15, 1))]
        ], size=(350, 120)),
        sg.Frame("颜色信息", [
            [sg.Text("16进制值:", size=(10, 1)), sg.Text("", key="-HEX-", size=(10, 1), font=("Arial", 14))],
            [sg.Text("RGB值:", size=(10, 1)), sg.Text("", key="-RGB-", size=(15, 1), font=("Arial", 14))],
            [sg.Text("HSV值:", size=(10, 1)), sg.Text("", key="-HSV-", size=(20, 1), font=("Arial", 14))],
            [sg.Graph((200, 80), (0, 0), (200, 80), key="-COLORBOX-")]
        ], size=(350, 200))
    ],
    [
        sg.Frame("图片预览", [
            [sg.Image(key="-IMAGE-", size=(300, 300))]
        ], size=(350, 350)),
        sg.Frame("颜色详情", [
            [sg.Text("提取的颜色将显示在这里", key="-COLORTEXT-", font=("Arial", 16), justification='center')],
            [sg.Text("", key="-COLORDESC-", font=("Arial", 12), justification='center', size=(30, 10))]
        ], size=(350, 350))
    ],
    [sg.StatusBar("准备就绪...", key="-STATUS-", size=(50, 1), expand_x=True)]
]

# 创建窗口
window = sg.Window("图片颜色提取器", layout, resizable=True)

# 事件循环
while True:
    event, values = window.read()

    # 退出程序
    if event in (sg.WIN_CLOSED, "退出"):
        break

    # 处理提取颜色事件
    if event == "提取颜色":
        file_path = values["-FILE-"]
        if not file_path:
            sg.popup_error("请先选择一张图片！")
            continue

        if not os.path.exists(file_path):
            sg.popup_error("文件不存在，请重新选择！")
            continue

        window["-STATUS-"].update("正在处理图片...")
        window.refresh()

        try:
            # 显示预览图片
            img_preview = resize_image(file_path)
            window["-IMAGE-"].update(data=img_preview)

            # 提取主要颜色
            main_color, hex_color = extract_main_color(file_path)
            r, g, b = main_color

            # 转换为HSV
            h, s, v = rgb_to_hsv(main_color)

            # 更新UI
            window["-HEX-"].update(hex_color)
            window["-RGB-"].update(f"({r}, {g}, {b})")
            window["-HSV-"].update(f"({h}°, {s}%, {v}%)")

            # 绘制颜色框
            graph = window["-COLORBOX-"]
            graph.erase()
            graph.draw_rectangle((0, 0), (200, 80), fill_color=hex_color, line_color=hex_color)

            # 更新颜色描述
            window["-COLORTEXT-"].update(f"主要颜色: {hex_color}")

            # 根据颜色生成描述性文本
            descriptions = []
            if r > 200 and g > 200 and b > 200:
                descriptions.append("浅色/接近白色")
            elif r < 50 and g < 50 and b < 50:
                descriptions.append("深色/接近黑色")
            else:
                if h < 15 or h > 345:
                    descriptions.append("红色系")
                elif 15 <= h < 45:
                    descriptions.append("橙色系")
                elif 45 <= h < 75:
                    descriptions.append("黄色系")
                elif 75 <= h < 165:
                    descriptions.append("绿色系")
                elif 165 <= h < 195:
                    descriptions.append("青色系")
                elif 195 <= h < 255:
                    descriptions.append("蓝色系")
                elif 255 <= h < 285:
                    descriptions.append("紫色系")
                elif 285 <= h < 345:
                    descriptions.append("粉色系")

                if s < 30:
                    descriptions.append("低饱和度")
                elif s > 70:
                    descriptions.append("高饱和度")

                if v < 30:
                    descriptions.append("暗色")
                elif v > 70:
                    descriptions.append("亮色")

            desc_text = "颜色特征:\n" + "\n".join(descriptions) if descriptions else "中性颜色"
            window["-COLORDESC-"].update(desc_text)

            window["-STATUS-"].update("颜色提取完成！")

        except Exception as e:
            sg.popup_error(f"处理图片时出错:\n{str(e)}")
            window["-STATUS-"].update("错误发生！")

window.close()