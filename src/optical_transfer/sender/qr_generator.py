from __future__ import annotations

from io import BytesIO


def make_qr_png(payload: str) -> bytes:
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
    except ImportError as exc:
        raise RuntimeError("缺少 qrcode/Pillow 依赖") from exc
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=1, border=4)
    qr.add_data(payload, optimize=0)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()

