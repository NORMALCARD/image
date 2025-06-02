import PySimpleGUI as sg
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
import colorsys
from collections import Counter


def extract_all_colors(image_path, max_colors=200):
    """提取图片中的主要颜色（使用K-means聚类）"""
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        return []

    # 转换为RGB格式 - 确保颜色空间正确
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 调整图片大小以加速处理
    h, w, _ = image.shape
    if w > 800 or h > 800:
        scale = 800 / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 重塑图像为像素列表
    pixel_values = image.reshape((-1, 3))
    pixel_values = np.float32(pixel_values)

    # 使用K-means聚类找到主要颜色
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    k = min(max_colors, 10)  # 最多提取max_colors种颜色，但至少10种

    _, labels, centers = cv2.kmeans(
        pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )

    # 转换为整数
    centers = np.uint8(centers)

    # 获取颜色频率
    counts = Counter(labels.flatten())

    # 按频率排序
    sorted_colors = sorted(
        [(centers[i], count) for i, count in counts.items()],
        key=lambda x: x[1],
        reverse=True
    )

    # 返回颜色列表（不带频率）
    return [tuple(color[0]) for color in sorted_colors[:max_colors]]


def rgb_to_hex(rgb):
    """将RGB元组转换为16进制颜色值"""
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def rgb_to_hsv(rgb):
    """将RGB颜色转换为HSV颜色空间"""
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return int(h * 360), int(s * 100), int(v * 100)


def resize_image(image_path, max_size=(400, 400)):
    """调整图像大小以适应预览窗口"""
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)


def create_color_image(color, size=(50, 50), text=None):
    """创建颜色图像块（使用PIL确保颜色准确）"""
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)

    # 添加文本（如果有）
    if text:
        # 根据亮度选择文本颜色
        r, g, b = color
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)

        try:
            # 尝试使用默认字体
            font = ImageFont.load_default()
            text_width, text_height = draw.textsize(text, font=font)
            position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
            draw.text(position, text, fill=text_color, font=font)
        except:
            # 如果加载字体失败，则不添加文本
            pass

    return ImageTk.PhotoImage(img)


def create_color_grid(colors, cols=8, square_size=50):
    """创建颜色网格的布局"""
    grid = []
    row = []

    for i, color in enumerate(colors):
        hex_color = rgb_to_hex(color)

        # 创建颜色图像（确保颜色准确）
        color_img = create_color_image(color, (square_size, square_size), hex_color)

        # 创建图像元素
        image_element = sg.Image(
            data=color_img,
            key=f"-COLOR-{i}-",
            tooltip=hex_color,
            pad=(0, 0),
            size=(square_size, square_size)
        )

        # 创建文本元素
        r, g, b = color
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        text_color = "black" if brightness > 128 else "white"

        text_element = sg.Text(
            hex_color,
            size=(10, 1),
            justification='center',
            text_color=text_color,
            background_color=hex_color,
            pad=(0, 0),
            key=f"-TEXT-{i}-"
        )

        # 组合元素
        color_element = sg.Column([
            [image_element],
            [text_element]
        ], pad=(0, 0), element_justification='center')

        row.append(color_element)

        # 每行达到指定列数后换行
        if (i + 1) % cols == 0 or i == len(colors) - 1:
            grid.append(row)
            row = []

    return grid


# 设置主题
sg.theme('LightBlue3')

# 初始布局
layout = [
    [sg.Text("图片颜色提取器", font=("Arial", 20), justification='center', expand_x=True)],
    [
        sg.Frame("操作区域", [
            [sg.Text("选择图片:")],
            [sg.InputText(key="-FILE-", size=(40, 1)),
             sg.FileBrowse(file_types=(("图片文件", "*.jpg;*.jpeg;*.png;*.bmp;*.gif"),))],
            [sg.Button("提取颜色", size=(10, 1)),
             sg.Button("搜索颜色", size=(10, 1)),
             sg.InputText(key="-SEARCH-", size=(15, 1), tooltip="输入16进制颜色值如 #FF0000"),
             sg.Button("重置", size=(10, 1))]
        ], size=(450, 100)),
        sg.Frame("颜色详情", [
            [sg.Text("选择颜色查看详情", key="-COLORTEXT-", font=("Arial", 14), justification='center')],
            [sg.Graph((200, 100), (0, 0), (200, 100), key="-COLORBOX-")],
            [sg.Text("16进制值:", size=(10, 1)), sg.Text("", key="-HEX-", size=(10, 1))],
            [sg.Text("RGB值:", size=(10, 1)), sg.Text("", key="-RGB-", size=(15, 1))],
            [sg.Text("HSV值:", size=(10, 1)), sg.Text("", key="-HSV-", size=(20, 1))],
        ], size=(250, 300))
    ],
    [
        sg.Frame("图片预览", [
            [sg.Image(key="-IMAGE-", size=(300, 300))]
        ], size=(350, 350)),
        sg.Frame("颜色信息", [
            [sg.Text("颜色名称:", size=(10, 1)), sg.Text("", key="-COLORNAME-", size=(20, 1))],
            [sg.Text("颜色描述:", size=(10, 1)), sg.Text("", key="-COLORDESC-", size=(20, 3))]
        ], size=(350, 350))
    ],
    [
        sg.Frame("提取的颜色", [
            [sg.Text("正在等待图片...", key="-COLORGRIDTEXT-", size=(60, 10))],
            [sg.Column([[]], key="-COLORGRIDCONTAINER-", size=(750, 300), scrollable=True, vertical_scroll_only=True)]
        ], size=(800, 300), expand_x=True)
    ],
    [sg.StatusBar("准备就绪...", key="-STATUS-", size=(50, 1), expand_x=True)]
]

# 创建窗口
window = sg.Window("图片颜色提取器", layout, resizable=True, finalize=True)
window.set_min_size((800, 700))

# 颜色名称映射
COLOR_NAMES = {
    "#ff0000": "红色", "#00ff00": "绿色", "#0000ff": "蓝色",
    "#ffff00": "黄色", "#ff00ff": "品红", "#00ffff": "青色",
    "#ffa500": "橙色", "#800080": "紫色", "#008000": "深绿",
    "#000080": "海军蓝", "#800000": "栗色", "#808000": "橄榄色",
    "#008080": "蓝绿色", "#c0c0c0": "银色", "#808080": "灰色",
    "#ffffff": "白色", "#000000": "黑色", "#ffc0cb": "粉色",
    "#a52a2a": "棕色", "#ffd700": "金色", "#e6e6fa": "薰衣草色"
}

# 事件循环
all_colors = []
current_colors = []
color_grid_container = window["-COLORGRIDCONTAINER-"]
color_images = {}  # 存储颜色图像引用

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

            # 提取所有颜色
            all_colors = extract_all_colors(file_path)
            current_colors = all_colors.copy()

            if not all_colors:
                sg.popup_error("无法从图片中提取颜色！")
                window["-STATUS-"].update("提取失败")
                continue

            # 创建颜色网格
            color_grid_layout = create_color_grid(all_colors, cols=10)

            # 更新颜色网格区域
            # 清除容器中的旧内容
            color_grid_container.update(visible=False)
            for child in color_grid_container.Widget.winfo_children():
                child.destroy()

            # 添加新的颜色网格
            new_color_grid = sg.Column(
                color_grid_layout,
                key="-COLORGRID-",
                size=(750, 300),
                scrollable=True,
                vertical_scroll_only=True
            )

            color_grid_container.add_row(new_color_grid)
            color_grid_container.update(visible=True)
            window["-COLORGRIDTEXT-"].update(visible=False)

            # 更新状态
            window["-STATUS-"].update(f"提取完成！共找到 {len(all_colors)} 种主要颜色")

            # 重置详情区域
            window["-COLORTEXT-"].update("点击颜色查看详情")
            window["-COLORBOX-"].erase()
            window["-HEX-"].update("")
            window["-RGB-"].update("")
            window["-HSV-"].update("")
            window["-COLORNAME-"].update("")
            window["-COLORDESC-"].update("")

        except Exception as e:
            sg.popup_error(f"处理图片时出错:\n{str(e)}")
            import traceback

            traceback.print_exc()
            window["-STATUS-"].update("错误发生！")

    # 处理颜色搜索事件
    if event == "搜索颜色":
        search_value = values["-SEARCH-"].strip().lower()
        if not search_value:
            sg.popup_error("请输入要搜索的颜色值（如 #FF0000）")
            continue

        # 确保搜索值以#开头
        if not search_value.startswith("#"):
            search_value = "#" + search_value

        # 搜索匹配的颜色
        matched_colors = []
        for color in all_colors:
            hex_color = rgb_to_hex(color)
            if search_value in hex_color:
                matched_colors.append(color)

        if not matched_colors:
            sg.popup(f"未找到匹配的颜色: {search_value}")
            continue

        # 更新颜色网格
        current_colors = matched_colors
        color_grid_layout = create_color_grid(matched_colors, cols=10)

        # 更新颜色网格区域
        color_grid_container.update(visible=False)
        for child in color_grid_container.Widget.winfo_children():
            child.destroy()

        new_color_grid = sg.Column(
            color_grid_layout,
            key="-COLORGRID-",
            size=(750, 300),
            scrollable=True,
            vertical_scroll_only=True
        )

        color_grid_container.add_row(new_color_grid)
        color_grid_container.update(visible=True)

        window["-STATUS-"].update(f"找到 {len(matched_colors)} 个匹配的颜色")

    # 处理重置事件
    if event == "重置":
        if all_colors:
            current_colors = all_colors.copy()
            color_grid_layout = create_color_grid(all_colors, cols=10)

            # 更新颜色网格区域
            color_grid_container.update(visible=False)
            for child in color_grid_container.Widget.winfo_children():
                child.destroy()

            new_color_grid = sg.Column(
                color_grid_layout,
                key="-COLORGRID-",
                size=(750, 300),
                scrollable=True,
                vertical_scroll_only=True
            )

            color_grid_container.add_row(new_color_grid)
            color_grid_container.update(visible=True)

            window["-SEARCH-"].update("")
            window["-STATUS-"].update(f"显示所有 {len(all_colors)} 种颜色")

    # 处理颜色点击事件
    if event and event.startswith("-COLOR-"):
        # 提取颜色索引
        try:
            idx = int(event.split("-")[2])
        except:
            continue

        if idx < len(current_colors):
            color = current_colors[idx]
            r, g, b = color
            hex_color = rgb_to_hex(color)
            h, s, v = rgb_to_hsv(color)

            # 更新详情区域
            window["-COLORTEXT-"].update(f"所选颜色: {hex_color}")
            window["-HEX-"].update(hex_color)
            window["-RGB-"].update(f"RGB({r}, {g}, {b})")
            window["-HSV-"].update(f"HSV({h}°, {s}%, {v}%)")

            # 绘制颜色框
            graph = window["-COLORBOX-"]
            graph.erase()
            graph.draw_rectangle((0, 0), (200, 100), fill_color=hex_color, line_color=hex_color)

            # 获取颜色名称
            color_name = COLOR_NAMES.get(hex_color, "未知颜色")
            window["-COLORNAME-"].update(color_name)

            # 生成颜色描述
            descriptions = []
            if r > 220 and g > 220 and b > 220:
                descriptions.append("非常明亮的颜色")
            elif r < 30 and g < 30 and b < 30:
                descriptions.append("非常暗的颜色")

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
                descriptions.append("深色调")
            elif v > 70:
                descriptions.append("浅色调")

            desc_text = "\n".join(descriptions) if descriptions else "中性颜色"
            window["-COLORDESC-"].update(desc_text)

window.close()