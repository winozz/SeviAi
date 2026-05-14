import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image
from pathlib import Path

URL = "https://downloaded-wrestling-genuine-wood.trycloudflare.com"
HERE = Path(__file__).parent
LOGO = HERE / "diwa.jpg"
OUT = HERE / "diwa_qr.png"

qr = qrcode.QRCode(
    version=None,
    error_correction=ERROR_CORRECT_H,
    box_size=20,
    border=2,
)
qr.add_data(URL)
qr.make(fit=True)

img = qr.make_image(fill_color="#0c3a14", back_color="#f5f1e6").convert("RGBA")

logo = Image.open(LOGO).convert("RGBA")
logo_w = img.size[0] // 4
ratio = logo_w / logo.size[0]
logo = logo.resize((logo_w, int(logo.size[1] * ratio)), Image.LANCZOS)

pad = 18
bg = Image.new(
    "RGBA",
    (logo.size[0] + pad * 2, logo.size[1] + pad * 2),
    (245, 241, 230, 255),
)
bg.paste(logo, (pad, pad), logo)

pos = ((img.size[0] - bg.size[0]) // 2, (img.size[1] - bg.size[1]) // 2)
img.paste(bg, pos, bg)
img.save(OUT)
print(f"saved {OUT}  size={img.size}")
