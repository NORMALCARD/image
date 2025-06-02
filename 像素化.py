import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class PixelArtConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("图像像素画转换器")
        self.root.geometry("800x600")

        # 初始化变量
        self.original_image = None
        self.processed_image = None
        self.pixel_size = 16
        self.preview_width = 300  # 初始预览宽度
        self.preview_height = 300  # 初始预览高度

        # 创建UI组件
        self.create_widgets()
        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self.on_window_resize)

    def create_widgets(self):
        # 文件选择按钮
        self.btn_select = tk.Button(self.root, text="选择图片", command=self.select_image)
        self.btn_select.pack(pady=10, fill=tk.X, padx=20)

        # 像素调节区域
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=5, fill=tk.X, padx=20)

        tk.Label(self.control_frame, text="像素大小:").pack(side=tk.LEFT, padx=5)
        self.var_pixel = tk.StringVar(value="16")
        self.entry_pixel = tk.Entry(self.control_frame, textvariable=self.var_pixel, width=5)
        self.entry_pixel.pack(side=tk.LEFT, padx=5)
        self.entry_pixel.bind("<Return>", self.validate_input)

        self.slider_pixel = tk.Scale(self.control_frame, from_=1, to=1024, orient=tk.HORIZONTAL,
                                     command=self.slider_update, showvalue=0)
        self.slider_pixel.set(16)
        self.slider_pixel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 自适应预览区域（左右分栏）
        self.preview_container = tk.Frame(self.root)
        self.preview_container.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

        # 原图预览面板（左）
        self.original_panel = tk.Frame(self.preview_container, relief=tk.SUNKEN, borderwidth=1)
        self.original_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_original = tk.Label(self.original_panel)
        self.lbl_original.pack(fill=tk.BOTH, expand=True)

        # 像素画预览面板（右）
        self.processed_panel = tk.Frame(self.preview_container, relief=tk.SUNKEN, borderwidth=1)
        self.processed_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_processed = tk.Label(self.processed_panel)
        self.lbl_processed.pack(fill=tk.BOTH, expand=True)

        # 保存按钮
        self.btn_save = tk.Button(self.root, text="保存像素画", command=self.save_image)
        self.btn_save.pack(pady=10, fill=tk.X, padx=20)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("图像文件", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if not file_path:
            return

        try:
            self.original_image = Image.open(file_path)
            self.update_preview()  # 首次加载时更新预览
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片文件: {str(e)}")

    def on_window_resize(self, event):
        """窗口大小变化时更新预览尺寸"""
        if event.widget == self.root and self.original_image:
            # 获取预览面板的当前尺寸（减去边框和padding）
            panel_width = self.original_panel.winfo_width() - 10
            panel_height = self.original_panel.winfo_height() - 10
            if panel_width > 0 and panel_height > 0:
                self.preview_width = panel_width
                self.preview_height = panel_height
                self.update_preview()  # 触发预览更新

    def update_preview(self):
        """更新原图和像素画的预览显示"""
        if not self.original_image:
            return

        # 处理原图预览（保持宽高比自适应）
        original_resized = self.resize_image(self.original_image,
                                             self.preview_width,
                                             self.preview_height)
        self.original_tk = ImageTk.PhotoImage(original_resized)
        self.lbl_original.config(image=self.original_tk)

        # 处理像素画预览
        self.processed_image = self.generate_pixel_art()
        if self.processed_image:
            processed_resized = self.resize_image(self.processed_image,
                                                  self.preview_width,
                                                  self.preview_height)
            self.processed_tk = ImageTk.PhotoImage(processed_resized)
            self.lbl_processed.config(image=self.processed_tk)

    def resize_image(self, image, max_width, max_height):
        """调整图片尺寸以适应预览区域（保持宽高比）"""
        width, height = image.size
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def generate_pixel_art(self):
        """生成像素画核心算法"""
        if not self.original_image:
            return None

        original_width, original_height = self.original_image.size
        target_width = max(1, original_width // self.pixel_size)
        target_height = max(1, original_height // self.pixel_size)

        small_image = self.original_image.resize(
            (target_width, target_height),
            Image.Resampling.NEAREST
        )
        return small_image.resize(
            (original_width, original_height),
            Image.Resampling.NEAREST
        )

    def slider_update(self, value):
        """滑块更新时同步数值"""
        self.pixel_size = int(float(value))
        self.var_pixel.set(str(self.pixel_size))
        if self.original_image:
            self.update_preview()

    def validate_input(self, event):
        """输入框数值验证"""
        try:
            input_value = int(self.var_pixel.get())
            if 1 <= input_value <= 1024:
                self.pixel_size = input_value
                self.slider_pixel.set(input_value)
                self.update_preview()
            else:
                raise ValueError
        except:
            self.var_pixel.set(str(self.pixel_size))
            messagebox.showwarning("提示", "请输入1-1024之间的整数")

    def save_image(self):
        """保存最终像素画"""
        if not self.processed_image:
            messagebox.showwarning("提示", "请先选择图片并生成像素画")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("JPG文件", "*.jpg")]
        )
        if file_path:
            try:
                self.processed_image.save(file_path)
                messagebox.showinfo("成功", "像素画已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelArtConverter(root)
    root.mainloop()
