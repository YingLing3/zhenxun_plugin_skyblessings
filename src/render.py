"""
图片渲染模块（移植自 skyblessings-python-api，做了相对导入调整）
"""

import random
import io
from pathlib import Path
from typing import Tuple, Optional, Union
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from .draw_data import (
    DRAW_ITEMS,
    DrawItem,
    BACKGROUND_IMAGE_MAP,
    TEXT_IMAGE_MAP,
    extract_color_from_name,
)


@dataclass
class BlessingResult:
    background_image: str = ""
    text_image: str = ""
    text_label: str = ""
    dordas: str = ""
    dordas_color: str = ""
    color_hex: str = ""
    blessing: str = ""
    entry: str = ""


class BlessingRenderer:
    def __init__(self, config: dict):
        self.config = config
        self.width = config['image']['width']
        self.height = config['image']['height']
        self.font_size = config['image']['font_size']
        self.assets_dir = Path(config['image']['assets_dir'])
        self.font_cache: dict[int, Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]] = {}

    def _load_font(self, size: Optional[int] = None) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
        font_size = size if size is not None else self.font_size
        if font_size not in self.font_cache:
            font_path = self.assets_dir / "font" / "LXGWWenKaiMono-Medium.ttf"
            try:
                self.font_cache[font_size] = ImageFont.truetype(str(font_path), font_size)
            except Exception:
                self.font_cache[font_size] = ImageFont.load_default()
        return self.font_cache[font_size]

    def _get_children(self, parent_id: str):
        return [item for item in DRAW_ITEMS if item.parent_id == parent_id]

    def _draw_random_item(self, items: list[DrawItem]) -> DrawItem:
        if not items:
            raise ValueError("没有可选项")
        total_weight = sum(item.weight for item in items)
        rand_num = random.randint(1, total_weight)
        cumulative = 0
        for item in items:
            cumulative += item.weight
            if rand_num <= cumulative:
                return item
        return items[-1]

    def _draw_sub_items(self, parent_id: str, result: BlessingResult):
        children = self._get_children(parent_id)
        if not children:
            return
        selected = self._draw_random_item(children)
        if selected.remark == "dordas":
            result.dordas = selected.name
        elif selected.remark == "dordascolor":
            result.dordas_color = selected.name
            result.color_hex = extract_color_from_name(selected.name)
        elif selected.remark == "blessing":
            result.blessing = selected.name
        elif selected.remark == "entry":
            result.entry = selected.name
        self._draw_sub_items(selected.id, result)

    def perform_draw(self) -> BlessingResult:
        result = BlessingResult()
        bg_items = [item for item in DRAW_ITEMS if item.remark == "backgroundimg"]
        bg_item = self._draw_random_item(bg_items)
        result.background_image = BACKGROUND_IMAGE_MAP.get(bg_item.name, "")
        text_items = self._get_children(bg_item.id)
        text_items = [item for item in text_items if item.remark == "textimg"]
        text_item = self._draw_random_item(text_items)
        result.text_image = TEXT_IMAGE_MAP.get(text_item.name, "")
        result.text_label = text_item.name
        self._draw_sub_items(text_item.id, result)
        return result

    def _hex_to_rgba(self, hex_color: str, alpha: int = 204) -> Tuple[int, int, int, int]:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b, alpha)

    def generate_blessing_image(self, debug: bool = False, add_text_stroke: bool = False) -> bytes:
        result = self.perform_draw()
        canvas = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 0))
        self._draw_colored_background(canvas, result.color_hex)
        if result.background_image:
            self._draw_background_decoration(canvas, result.background_image)
        if result.text_image:
            self._draw_text_image(canvas, result.text_image)
        self._draw_texts(canvas, result, add_text_stroke=add_text_stroke)
        output = io.BytesIO()
        canvas.save(output, format='PNG')
        output.seek(0)
        return output.getvalue()

    def _draw_background_decoration(self, canvas: Image.Image, decoration_filename: str):
        mask_path = self.assets_dir / "image" / decoration_filename
        try:
            base_texture = Image.open(mask_path).convert('RGBA')
            canvas.alpha_composite(base_texture)
        except Exception as e:
            print(f"警告：绘制装饰层失败 {e}")

    def _draw_colored_background(self, canvas: Image.Image, color_hex: str):
        mask_path = self.assets_dir / "image" / "background.png"
        try:
            mask_img = Image.open(mask_path).convert('RGBA')
            alpha_mask = mask_img.split()[-1]
            color_layer = Image.new('RGBA', (self.width, self.height), self._hex_to_rgba(color_hex, alpha=200))
            temp_canvas = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            temp_canvas.paste(color_layer, (0, 0), mask=alpha_mask)
            canvas.alpha_composite(temp_canvas)
        except Exception as e:
            print(f"警告：绘制背景层失败 {e}")

    def _draw_text_image(self, canvas: Image.Image, text_filename: str):
        text_img_path = self.assets_dir / "image" / text_filename
        try:
            text_img = Image.open(text_img_path).convert('RGBA')
            x = int(self.width * 0.204)
            y = int(self.height * 0.49)
            canvas.paste(text_img, (x, y), text_img)
        except Exception as e:
            print(f"警告：加载签文图失败 {e}")

    def _draw_texts(self, canvas: Image.Image, result: BlessingResult, add_text_stroke: bool = False):
        font_normal = self._load_font(size=40)
        font_blod = self._load_font(size=49)
        draw = ImageDraw.Draw(canvas)
        text_color = (255, 255, 255, 255)
        stroke_color = (100, 100, 100, 80)
        texts = [result.dordas, result.dordas_color, result.blessing, result.entry]
        text_width_ratio = 0.35
        margin_right = 40
        text_area_x = int(self.width * (1 - text_width_ratio)) - margin_right - 133
        line_spacings = [20, 60, 85]
        total_height = self.font_size * 3 + 32 + sum(line_spacings)
        start_y = int((self.height - total_height) / 2) + 29
        current_y = start_y
        for i, text in enumerate(texts):
            if text:
                current_font = font_blod if i == 2 else font_normal
                if add_text_stroke:
                    stroke_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for offset_x, offset_y in stroke_offsets:
                        draw.text((text_area_x + offset_x, current_y + offset_y), text, font=current_font, fill=stroke_color)
                draw.text((text_area_x, current_y), text, font=current_font, fill=text_color)
                if i < len(line_spacings):
                    current_y += (32 if i == 2 else self.font_size) + line_spacings[i]
