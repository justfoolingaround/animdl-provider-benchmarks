from PIL import Image, ImageDraw, ImageFont

base_image = Image.new(
    "RGBA", (420, 50)
)

def generate_image(asset_image, color, status, *, font="./assets/font.ttf"):
    
    base_copy = base_image.copy()
    
    drawable_font = ImageFont.truetype(font, size=32)
    content_image = Image.open(asset_image).resize(
        (50, 50)
    )

    base_copy.paste(
        content_image, (15, 0)
    )

    drawable = ImageDraw.Draw(base_copy)

    drawable.text(
        (80, 5), status, color, drawable_font, align="center"
    )

    return base_copy
