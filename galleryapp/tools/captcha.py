import random
import string
from PIL import Image, ImageDraw, ImageFont
import io
import base64


class CaptchaUtil:
    def __init__(self):
        self.width = 120  # 验证码图片宽度
        self.height = 40  # 验证码图片高度
        self.font_size = 30  # 字体大小
        self.code_len = 4  # 验证码长度

    def generate_code(self):
        """生成随机验证码"""
        # 包含数字和大写字母的字符集
        chars = string.ascii_uppercase + string.digits
        code = ''.join(random.choices(chars, k=self.code_len))
        return code

    def generate_captcha(self):
        """生成验证码图片"""
        # 创建画布
        image = Image.new('RGB', (self.width, self.height), 'white')
        draw = ImageDraw.Draw(image)

        # 生成验证码文本
        code = self.generate_code()

        try:
            # 使用系统字体，也可以指定特定字体文件路径
            font = ImageFont.truetype('arial.ttf', self.font_size)
        except:
            # 如果找不到指定字体，使用默认字体
            font = ImageFont.load_default()

        # 绘制文字
        for i in range(self.code_len):
            color = (random.randint(0, 150),
                     random.randint(0, 150),
                     random.randint(0, 150))
            draw.text(
                (5 + i * 30, 5),
                code[i],
                font=font,
                fill=color
            )

        # 添加干扰线
        for _ in range(5):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill='gray')

        # 添加噪点
        for _ in range(30):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point([x, y], fill='black')

        # 将图片转换为base64字符串
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return code, img_str

    @staticmethod
    def verify_code(user_input, stored_code):
        """验证用户输入的验证码"""
        if not user_input or not stored_code:
            return False
        return user_input.upper() == stored_code.upper()
