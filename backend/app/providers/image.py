import base64
import hashlib
from abc import ABC, abstractmethod
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageEnhance

from app.core.config import Settings, get_settings


class ImageProvider(ABC):
    name: str
    model_name: str

    @abstractmethod
    def edit(self, source: Path, output: Path, prompt: str, attempt: int) -> None:
        raise NotImplementedError


class MockImageProvider(ImageProvider):
    name = "mock"
    model_name = "mock-qwen-image-edit"

    def edit(self, source: Path, output: Path, prompt: str, attempt: int) -> None:
        if "[mock-fail-once]" in prompt and attempt == 1:
            raise RuntimeError("模拟上游暂时失败，请重试。")
        color_seed = hashlib.sha256(prompt.encode("utf-8")).digest()
        accent = (color_seed[0], color_seed[1], color_seed[2], 72)
        with Image.open(source) as opened:
            image = ImageEnhance.Color(opened.convert("RGBA")).enhance(1.12)
            image = ImageEnhance.Contrast(image).enhance(1.06)
            overlay = Image.new("RGBA", image.size, accent)
            image = Image.blend(image, overlay, 0.12)
            draw = ImageDraw.Draw(image)
            border_width = max(4, min(image.size) // 80)
            draw.rectangle(
                (
                    border_width,
                    border_width,
                    image.width - border_width,
                    image.height - border_width,
                ),
                outline=(255, 255, 255, 210),
                width=border_width,
            )
            badge_width = min(210, max(100, image.width // 3))
            badge_height = max(30, image.height // 16)
            draw.rounded_rectangle(
                (border_width * 2, border_width * 2, badge_width, badge_height),
                radius=8,
                fill=(20, 27, 20, 210),
            )
            draw.text(
                (border_width * 3, border_width * 2.5),
                "MOCK EDIT",
                fill=(255, 255, 255, 255),
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            image.convert("RGB").save(output, format="PNG", optimize=True)


class QwenImageProvider(ImageProvider):
    name = "qwen"

    def __init__(self, settings: Settings):
        if not settings.qwen_image_api_key:
            raise RuntimeError("QWEN_IMAGE_API_KEY is required when Mock mode is disabled")
        self.model_name = settings.qwen_image_model
        self.api_key = settings.qwen_image_api_key
        self.base_url = settings.qwen_image_base_url.rstrip("/")
        self.timeout = settings.provider_timeout_seconds

    def edit(self, source: Path, output: Path, prompt: str, attempt: int) -> None:
        del attempt
        with Image.open(source) as image:
            mime = Image.MIME.get(image.format, "image/png")
        encoded = base64.b64encode(source.read_bytes()).decode("ascii")
        endpoint = f"{self.base_url}/services/aigc/multimodal-generation/generation"
        request_body = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:{mime};base64,{encoded}"},
                            {"text": prompt},
                        ],
                    }
                ]
            },
            "parameters": {
                "n": 1,
                "negative_prompt": " ",
                "prompt_extend": True,
                "watermark": False,
            },
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=request_body,
            )
            response.raise_for_status()
            content = response.json()["output"]["choices"][0]["message"]["content"]
            image_url = next(item["image"] for item in content if "image" in item)
            image_response = client.get(image_url)
            image_response.raise_for_status()
        with Image.open(BytesIO(image_response.content)) as generated:
            generated.verify()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(image_response.content)


def get_image_provider() -> ImageProvider:
    settings = get_settings()
    return MockImageProvider() if settings.mock_mode else QwenImageProvider(settings)
