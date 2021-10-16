import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageSequence

from django.conf import settings

def generate_match_nft(
        user1_name: str,
        user2_name: str
):

    img = Image.open(os.path.join(settings.BASE_DIR, "matching/giphy.gif"))
    logo = Image.open(os.path.join(settings.BASE_DIR, "matching/imgs/transparent_fixed_small_v2.png"))
    # Transparency
    new_logo = []
    for item in logo.getdata():
        if item[:3] == (255, 255, 255):
            new_logo.append((255, 255, 255, 0))
        else:
            new_logo.append(item)


    logo.putdata(new_logo)

    # logo.show()
    original_duration = img.info['duration']

    final_frames = []
    ctr = 0

    font_path = os.path.join(settings.BASE_DIR, "matching/norwester/norwester.otf")
    font_size = 28
    for final_frame in ImageSequence.Iterator(img):
        font = ImageFont.truetype(font_path, font_size)

        d1 = ImageDraw.Draw(final_frame)
        d1.text((190, 150), user1_name, fill=(255, 255, 255), font=font)
        d1.text((190, 350), user2_name, fill=(255, 255, 255), font=font)
        final_frame.paste(logo, (195, 215), logo)

        del d1

        # final_frame.show()
        # exit(1)
        b = io.BytesIO()
        final_frame.save(b, format="GIF")
        final_frame = Image.open(b)
        final_frames.append(final_frame)
        ctr += 1

    in_mem_file = io.BytesIO()
    # in_mem_file = os.path.join(settings.BASE_DIR, "matching/doug.gif")
    final_frames[0].save(in_mem_file, format='GIF',
                         append_images = final_frames[1:],
                         save_all = True,
                         duration = original_duration,
                         loop = 0,
                         optimize=True)
    in_mem_file.seek(0)
    return in_mem_file

