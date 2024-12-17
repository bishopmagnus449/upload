import base64
import hashlib
import io
import mimetypes
import random
import re
import string
from email.message import EmailMessage
from urllib.parse import quote
from itertools import cycle
from typing import Union, Optional
from email import encoders

import requests
from PIL import Image, ImageDraw, ImageFont
import qrcode

import csv
from colorama import Fore, Style
from threading import Lock

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

import base64

import config

print_lock = Lock()


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)


def text_red(text):
    return f"{Fore.RED}{text}{Style.RESET_ALL}"


def text_blue(text):
    return f"{Fore.BLUE}{text}{Style.RESET_ALL}"


def text_green(text):
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def text_magenta(text):
    # To create an "orange-like" color, we can use a combination of Fore.RED and Fore.YELLOW
    return f"{Fore.MAGENTA}{text}{Style.RESET_ALL}"


def d_print(debug):
    def wrapper(*args, **kwargs):
        if debug:
            safe_print(*args, **kwargs)

    return wrapper


def check_smtp_connection(conn):
    try:
        status = conn.noop()[0]
    except:  # smtplib.SMTPServerDisconnected
        status = -1
    return True if status == 250 else False


def rotate_list(_list, _rotate=False):
    if _rotate:
        rotating_cycle = cycle(_list)
    else:
        rotating_cycle = cycle([_list[0]])

    while True:
        yield next(rotating_cycle)


def extract_smtp(smtp_line):
    smtp_info = smtp_line.strip().split('|')
    require_login = len(smtp_info) > 4
    return {
        'host': smtp_info[0],
        'port': smtp_info[1],
        'user': smtp_info[2] if require_login else None,
        'pass': smtp_info[3] if require_login else None,

        'sender_email': smtp_info[-1],
    }

def extract_proxy(proxy_line):
    pattern = (r'^(?:(?P<protocol>[^:/$]+)(?::\/\/|\$))?(?P<host>[^:@]+):(?P<port>\d+)'
               r'(?:[@:](?P<user>[^:]+):(?P<pass>[^:@]+))?$')
    result = re.match(pattern, proxy_line).groupdict()
    return {
        'protocol': (result['protocol'] or config.proxy_configuration.get('default_protocol', 'http')).lower(),
        'addr': result['host'],
        'port': int(result['port']),
        'username': result['user'],
        'password': result['pass'],
    }


def load_smtp_file(file_path: Union[str, dict]):
    data = []
    if isinstance(file_path, dict):
        file_path = file_path['file_path']
    with open(file_path, 'r') as f:
        for line in f:
            if not line:
                continue
            data.append(extract_smtp(line))
    return data


def load_proxy_file(file_path: Union[str, dict]):
    proxies = []
    if isinstance(file_path, dict):
        file_path = file_path['file_path']
    with open (file_path, 'r') as f:
        for line in f:
            if not line:
                continue
            proxies.append(extract_proxy(line.strip()))
    return proxies


def load_csv_file(file_path, column_titles, *_, **__):
    data = []
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            data.append(dict(zip(column_titles, row)))
    return data


def image_to_base64(image_path=None, *, image_data=None, mime='image/png'):
    if image_path:
        with open(image_path, 'rb') as file:
            image_data = file.read()
    return f'data:{mime};base64,{base64.b64encode(image_data).decode("utf-8")}'


def generate_unicode_qr_code(_data, font_size="7px", foreground='black', background='transparent'):
    qr = qrcode.main.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=0,
    )
    qr.add_data(_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    # img = img.resize((img.width * 2, img.height * 2))  # Resize for better visibility

    qr_unicode = ''
    for y in range(img.height):
        for x in range(img.width):
            qr_unicode += f'<span style="color:{foreground}!important;">&#x2588;&#x2588;</span>' \
                if img.getpixel((x, y)) == 0 else f'<span style="color:{background}!important;">&#x2588;&#x2588;</span>'
        qr_unicode += '<br>'

    return (f'<pre style="font-size:{font_size}; line-height: normal;">'
            f'{qr_unicode}</pre>')


def generate_qr(data: str, save_path=None, logo_path=None, *, include_data_attr=False):
    qr = qrcode.main.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")

    if logo_path:
        try:
            logo = Image.open(logo_path)
            qr_image = add_logo_to_qr(qr_image, logo)
        except Exception as e:
            print("Error adding logo:", e)

    if save_path:
        qr_image.save(save_path, format="PNG")
        return save_path
    else:
        with io.BytesIO() as image_stream:
            qr_image.save(image_stream, format="PNG")
            image_data = image_stream.getvalue()
        return image_to_base64(image_data=image_data) if include_data_attr else image_data


def get_mime_type(file):
    """Returns the MIME type of the given image data."""
    mime_type = mimetypes.guess_type(file)[0]
    if mime_type is None:
        return "application/octet-stream"
    else:
        return mime_type


def add_logo_to_qr(qr_image, logo_image):
    qr_width, qr_height = qr_image.size
    logo_width, logo_height = logo_image.size
    logo_max_size = min(qr_width, qr_height) // 5  # Set the maximum size of the logo to 1/4 of the QR code

    # Resize the logo if it's too big
    if logo_width > logo_max_size or logo_height > logo_max_size:
        logo_image = logo_image.resize((logo_max_size, logo_max_size), Image.ANTIALIAS)

    # Calculate the position to center the logo on the QR code
    pos_x = (qr_width - logo_image.width) // 2
    pos_y = (qr_height - logo_image.height) // 2

    # Create a transparent image the same size as the QR code
    overlay = Image.new("RGBA", (qr_width, qr_height), (0, 0, 0, 0))
    # Paste the logo onto the transparent image at the calculated position
    overlay.paste(logo_image, (pos_x, pos_y))

    # Composite the QR code image and the logo overlay
    qr_image = Image.alpha_composite(qr_image.convert("RGBA"), overlay)

    return qr_image


def calculate_file_hash(file_path, hash_algorithm='sha256'):
    """Calculate the hash of a file using the specified hash algorithm.

    Args:
        file_path (str): Path to the file whose hash needs to be calculated.
        hash_algorithm (str, optional): The hashing algorithm to use. Defaults to 'sha256'.

    Returns:
        str: The hash digest in hexadecimal format.
    """
    # Create a hash object based on the specified algorithm
    hash_object = hashlib.new(hash_algorithm)

    # Open the file in binary mode and read it in chunks for memory efficiency
    with open(file_path, 'rb') as file:
        while True:
            # Read a chunk of data from the file
            chunk = file.read(4096)  # You can adjust the chunk size as per your requirements
            if not chunk:
                break

            # Update the hash object with the data from the current chunk
            hash_object.update(chunk)

    # Get the hexadecimal digest of the hash
    file_hash = hash_object.hexdigest()
    return file_hash


def str_replace(subject: str, search: Union[list, dict], replace: list = None) -> str:
    if isinstance(search, list):
        if replace is None or len(search) != len(replace):
            raise ValueError("The search and replace lists must have the same length.")
        search_replace_pairs = zip(search, replace)
    elif isinstance(search, dict):
        search_replace_pairs = search.items()
    else:
        raise TypeError("Search must be either a list or a dictionary.")

    for _search, _replace in search_replace_pairs:
        subject = subject.replace(_search, _replace or '')

    return subject


def url_shortener(api_key, url):
    url = quote(url)
    r = requests.get(f'http://cutt.ly/api/api.php?key={api_key}&short={url}')
    try:
        short = r.json()['url']['shortLink']
        return short
    except KeyError as e:
        print('Shortening url failed:', e)


def encode_ascii85(input_string):
    # Encode the input string using ASCII85
    encoded_bytes = base64.a85encode(input_string.encode())
    return "<~" + encoded_bytes.decode() + "~>"


def decode_ascii85(encoded_string):
    # Remove the ASCII85 delimiters (<~ and ~>), then decode the string
    encoded_string = encoded_string[2:-2].replace(" ", "").encode()
    decoded_bytes = base64.a85decode(encoded_string)
    return decoded_bytes.decode()


def generate_random_string(data):
    def replace_letter(match: re.Match):
        length = int(match.group(3))
        if match.group(2) == "LOW":
            return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))
        elif match.group(2) == "UP":
            return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))
        elif match.group(2) == "MIX":
            return ''.join(random.choice(string.ascii_letters) for _ in range(length))

    def replace_number(match):
        length = int(match.group(2))
        return ''.join(random.choice(string.digits) for _ in range(length))

    def replace_letter_number(match):
        length = int(match.group(3))
        if match.group(2) == "LOW":
            chars = string.ascii_lowercase + string.digits
        elif match.group(2) == "UP":
            chars = string.ascii_uppercase + string.digits
        else:
            chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    data = re.sub(r"#(LETTER|LET)-(LOW|UP|MIX)-(\d{1,8})#", replace_letter, data)
    data = re.sub(r"#(NUMBER|NUM)-(\d{1,8})#", replace_number, data)
    data = re.sub(r"#(LETTERNUMBER|LETNUM)-(LOW|UP|MIX)-(\d{1,8})#", replace_letter_number, data)

    return data


def words_to_images(words, font_size, font_path):
    # Create an empty list to store the images
    images = []
    # Create a font object with the given font size
    font = ImageFont.truetype(font_path, font_size)

    def draw_text(text):
        # Create a new image with a white background
        word_width, word_height = font.getsize_multiline(text)
        image = Image.new('RGBA', (word_width, int(word_height * 1.3)), (255, 255, 255, 0))
        # Create a draw object to draw on the image
        draw = ImageDraw.Draw(image)
        # Draw the word on the image with black color
        draw.text((0, 0), text, "black", font)
        # Save the image to a bytes object
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        # Encode the bytes object to base64
        return base64.b64encode(buffer.getvalue()).decode()

    # Split the words by space
    words = words.split()
    # Loop through the words
    for index, word in enumerate(words):
        if index != len(words) - 1:
            word = word + ' '
        images.append(draw_text(word))

    # Return the list of images
    return images


def obfuscate_links(letter_to_obf_link):
    pattern_link = r'<obflink>(http[s]?:\/\/)(.*?)<\/obflink>'
    matches_link = re.findall(pattern_link, letter_to_obf_link, re.IGNORECASE)

    for match in matches_link:
        url = match[1]
        obfuscated_link = ''.join(['&#' + str(ord(c)) + ';' for c in url])
        letter_to_obf_link = str_replace(letter_to_obf_link.replace(match[0], match[0] + obfuscated_link), {
            '<obflink>': '',
            '</obflink>': '',
            match[1]: '',
        })

    return letter_to_obf_link


def replace_base64_fields(letter):
    pattern = r"#base64#\[([^\]]+)\]"
    return re.sub(pattern, lambda match: base64.b64encode(match.group(1).encode()).decode(), letter)


def replace_encoder_fields(letter):
    pattern = r"#encode#\[([^\]]+)\]"
    return re.sub(pattern, lambda match: encrypt(match.group(1)), letter)


def replace_zero_pattern(letter):
    pattern = r"<zero>(.*?)<\/zero>"

    def replace_zero_tag(match):
        return f'<span style="font-size: 0px; color: transparent;">{match.group(1)}</span>'

    # Use re.sub to find and replace the pattern with the span tag
    result_string = re.sub(pattern, replace_zero_tag, letter)
    return result_string


def replace_encrypted_short(letter, short):
    pattern = r"#encrypted_short#\[([^\]]+)\]"
    encrypted_pattern = (f'https://{{}}/'
                         f'{generate_random_string("#LET-LOW-16#")}/'
                         f'{encrypt(short)}/'
                         f'{generate_random_string("#LETNUM-MIX-12#")}')
    return re.sub(pattern, lambda match: encrypted_pattern.format(match.group(1)), letter)


def replace_hidden_dash(letter, force_character=False):
    pattern = r'#hide_dash#\[([^\]]+)\]'

    def generate_str(_string):
        ZWSP = '\u200B'
        ZWJ = '\u200C'
        ZWNJ = '\u200D'
        LRM = '\u200E'
        RLM = '\u200F'
        SHY = '\xad'
        new_string = ""
        for i, char in enumerate(_string):
            if char not in [" ", ".", ",", "!", "?", ":", ";", "(", ")", "[", "]", "{", "}", "<", ">", "/", "_", "-",
                            "+", "=", "*", "&", "%", "$", "#", "’"] and i < len(_string) - 1 and _string[i + 1].isalnum():
                new_string += char + (f'{random.choice([SHY, ZWSP, ZWJ, ZWNJ, LRM, RLM])}'
                                      f'{random.choice([SHY, ZWSP, ZWJ, ZWNJ, LRM, RLM])}' if force_character else "&shy;")
            else:
                new_string += char
        return new_string

    return re.sub(pattern, lambda match: generate_str(match.group(1)), letter)


def encrypt(_string: str, _key: int = 13):
    encoded = ''
    length = len(_string)

    for i in range(length):
        char_code = ord(_string[i]) ^ _key
        encoded += chr(char_code)

    return base64.b64encode(encoded.encode()).decode()


def decrypt(_string: str, _key: int = 13):
    _string = base64.b64decode(_string.encode()).decode()
    encoded = ''
    length = len(_string)

    for i in range(length):
        char_code = ord(_string[i]) ^ _key
        encoded += chr(char_code)

    return encoded


def load_raw_email(file_path: str):
    from email.parser import Parser
    from email.policy import default
    with open(file_path, 'r') as f:
        return Parser(policy=default).parsestr(f.read())


def export_html(email_message: EmailMessage) -> Optional[str]:
    for part in email_message.walk():
        if part.get_content_type() == 'text/html':
            return part.get_payload(decode=True).decode(part.get_content_charset())
    return


def import_html(email_message: EmailMessage, html_body: str):
    for part in email_message.walk():
        if part.get_content_type() == 'text/html':
            if part['Content-Transfer-Encoding'] == 'base64':
                html_body = base64.b64encode(html_body.encode(part.get_content_charset()))
            if part['Content-Transfer-Encoding'] == 'quoted-printable':
                html_body = encoders._qencode(html_body.encode(part.get_content_charset()))

            part.set_payload(html_body)
            break
