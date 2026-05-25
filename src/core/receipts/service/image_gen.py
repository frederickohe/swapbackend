import base64
import io
from datetime import datetime
from typing import Any, Dict, Optional

from PIL import Image, ImageDraw, ImageFont


class ReceiptGenerator:
    def generate_receipt_image(self, data: Dict[str, Any]) -> str:
        width, height = 400, 720
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        try:
            title_font = ImageFont.truetype("arial.ttf", 22)
            body_font = ImageFont.truetype("arial.ttf", 14)
        except OSError:
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        y = 24
        draw.text((width // 2, y), "Transaction Receipt", fill="black", font=title_font, anchor="mt")
        y += 40

        lines = self._build_lines(data)
        for line in lines:
            draw.text((24, y), line, fill="black", font=body_font)
            y += 22

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    def _build_lines(self, data: Dict[str, Any]) -> list[str]:
        timestamp = data.get("timestamp")
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = str(timestamp) if timestamp else "N/A"

        lines = [
            f"Amount: GHS {data.get('amount', '0.00')}",
            f"Transaction ID: {data.get('transaction_id', 'N/A')}",
            f"Status: {data.get('status', 'N/A')}",
            f"Date: {timestamp_str}",
            "",
            f"Sender: {data.get('sender_name', 'N/A')}",
            f"Sender Account: {data.get('sender_account', 'N/A')}",
            f"Sender Provider: {data.get('sender_provider', 'N/A')}",
            "",
            f"Receiver: {data.get('receiver_name', 'N/A')}",
            f"Receiver Account: {data.get('receiver_account', 'N/A')}",
            f"Receiver Provider: {data.get('receiver_provider', 'N/A')}",
        ]

        optional_fields = [
            ("interest_rate", "Interest Rate"),
            ("loan_period", "Loan Period"),
            ("expected_pay_date", "Expected Pay Date"),
            ("penalty_rate", "Penalty Rate"),
        ]
        for key, label in optional_fields:
            value = data.get(key)
            if value is not None:
                lines.extend(["", f"{label}: {value}"])

        return lines
