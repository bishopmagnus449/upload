import asyncio
import base64
import json
import os
import queue
import random
import re
import smtplib
import socket
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate
from email import encoders
from io import BytesIO
from typing import Union, List, Optional
from threading import Lock

import dkim
import imgkit
import pdfkit
import socks
from PyPDF2 import PdfReader, PdfWriter
from faker import Faker
from icalendar import Event, Alarm, vCalAddress, vText, vUri, Calendar
import traceback
import config
import enums
import functions
import random_data
from enums import Contact
from functions import safe_print
import colorama
import textwrap
import time
colorama.init()
d_print = functions.d_print(config.debug)
GENERATOR_LOCK = Lock()


class MailData:
    faker_us = Faker()
    faker_fr = Faker('fr_FR')
    faker_de = Faker('de_DE')
    faker_jp = Faker('ja_JP')
    faker_ca = Faker('en_CA')

    def __init__(self, message: EmailMessage, receiver, smtp_config):
        self.date = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.old_date = (datetime.now() - timedelta(days=random.randint(1, 3), hours=random.randint(1, 24),
                                                    minutes=random.randint(1, 60))).strftime("%m/%d/%Y %I:%M:%S %p")
        self.email = receiver.get(Contact.EMAIL, '') or message['To']
        self.csv_firstname = receiver.get(Contact.FIRST_NAME, '')
        self.csv_lastname = receiver.get(Contact.LAST_NAME, '')
        self.csv_address = receiver.get(Contact.ADDRESS, '')
        self.csv_birth = receiver.get(Contact.BIRTH_DATE, '')
        self.csv_phone = receiver.get(Contact.PHONE_NUMBER, '')
        self.company = receiver.get(Contact.EMAIL, '').split('@')[1].split('.')[0].capitalize()
        self.email_base64 = base64.b64encode(self.email.encode('utf-8')).decode('utf-8')
        self.email_id = ' '.join(re.split(r'[._]', self.email.split('@')[0])).title()
        self.receiver_id: str = self.email.split('@')[0]
        self.word = random.choice(random_data.words)
        self.us_name = self.faker_us.name()
        self.fr_name = self.faker_fr.name()
        self.de_name = self.faker_de.name()
        self.jp_name = self.faker_jp.name()
        self.ca_name = self.faker_ca.name()
        self.us_address = self.faker_us.address()
        self.fr_address = self.faker_fr.address()
        self.de_address = self.faker_de.address()
        self.jp_address = self.faker_jp.address()
        self.ca_address = self.faker_ca.address()
        self.us_phone = self.faker_us.phone_number()
        self.fr_phone = self.faker_fr.phone_number()
        self.de_phone = self.faker_de.phone_number()
        self.jp_phone = self.faker_jp.phone_number()
        self.ca_phone = self.faker_ca.phone_number()
        self.fake_text = self.faker_us.text()
        self.fake_email = self.faker_us.email()
        self.lipsum = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit' + self.faker_us.paragraph(5)
        self.giftcode = functions.generate_random_string('#LETNUM-UP-16#')
        self.letter_up = functions.generate_random_string(f'#LET-UP-{random.randint(4, 8)}#')
        self.letter_mix = functions.generate_random_string(f'#LET-MIX-{random.randint(4, 8)}#')
        self.letter_low = functions.generate_random_string(f'#LET-LOW-{random.randint(4, 8)}#')
        self.letter_number = functions.generate_random_string(f'#LETNUM-LOW-{random.randint(14, 16)}#')
        self.letter_number_up = functions.generate_random_string(f'#LETNUM-UP-{random.randint(10, 12)}#')
        self.letter_number_mix = functions.generate_random_string(f'#LETNUM-MIX-{random.randint(10, 12)}#')
        self.number = functions.generate_random_string(f'#NUM-{random.randint(7, 9)}#')
        self.dolar = f'&dollar;{random.randint(100, 250)}.{random.randint(10, 99)}'
        self.dolar_ca = f'C&dollar;{random.randint(100, 250)}.{random.randint(10, 99)}'
        self.euro = f'&euro;{random.randint(100, 250)}.{random.randint(10, 99)} EUR'
        self.jpy = f'&yen;{random.randint(3000, 5000)}'
        self.cash_tag = f'&dollar;{self.faker_us.name().replace(" ", "")}'
        self.ip = random_data.random_ip
        self.amz_ip = random.choice(random_data.amazon_ips)
        self.ovh_ip = random.choice(random_data.ovh_ips)
        self.ionos_ip = random.choice(random_data.ionos_ips)
        self.chimp_ip = random.choice(random_data.chimp_ips)
        self.os = random.choice(random_data.operating_systems)
        self.country = random.choice(random_data.countries)
        self.browser = random.choice(random_data.browsers)
        self.user_agent_mac = random.choice(random_data.user_agents_mac)
        self.user_agents_windows = random.choice(random_data.user_agents_windows)
        self.tld = random.choice(random_data.tlds)
        self.local_domain = f'{random.choice(random_data.words)}.{random.choice(random_data.words)}.{self.tld}'
        self.domain_local = f'{random.choice(random_data.words)}.{random.choice(random_data.words)}.{self.tld}'
        self.domain_smtp = smtp_config['host']
        self.domain_receiver = self.email.split('@')[-1]
        self.short = ''
        self.pdf_password = ''


class PrepareMessage:
    message: EmailMessage
    message_body: str

    def __init__(self, _config, _receiver: dict, smtp_config: dict = None, init_message=False):
        """Create a new PrepareMessage
        :param config _config:
        """
        self.config = _config

        if self.config.raw_letter['enabled']:
            self.message = functions.load_raw_email(self.config.raw_letter['file_path'])
        else:
            self.message = EmailMessage()
            self.message.make_mixed()
            self.message.set_param('charset', 'utf-8')
            self.message.add_header('MIME-Version', '1.0')

        self.related_message = MIMEMultipart('related')
        self.related_message.set_param('charset', 'utf-8')
        self.inline_attachments = []

        self.receiver = _receiver
        self.smtp_config = smtp_config
        self.data = MailData(self.message, self.receiver, self.smtp_config)

        if init_message:
            self.init_message()
            self.data = MailData(self.message, self.receiver, self.smtp_config)

    def init_message(self):
        self._prepare_short()
        if self.config.raw_letter['enabled']:
            self.message_body = functions.export_html(self.message)
        else:
            with open(config.letter, 'r+') as f:
                self.message_body = f.read()
        self._prepare_contacts()
        self._prepare_pdf_password()
        self._prepare_subject()
        self._prepare_config_attachments()
        self._prepare_body()
        self._prepare_inline_attachments()
        self._prepare_headers()
        if self.config.html_to_pdf_options['enabled']:
            self._convert_to_pdf()
        if self.config.icalendar_options['enabled']:
            self._prepare_icalendar()

    def get_subject(self):
        return random.choice(self.config.subjects)

    @staticmethod
    def _get_unique_id():
        return str(uuid.uuid4()).split('-')[0]

    def attach_file(self, attachment_path=None, attachment_data=None, filename=None, content_type=None):
        if attachment_path:
            with open(attachment_path, 'rb') as file:
                attachment_data = file.read()
        if not attachment_path and not attachment_data:
            raise ValueError('A file path or data is required')
        if not attachment_path and not filename:
            filename = 'attachment'
        attachment = MIMEApplication(attachment_data)
        attachment.add_header('Content-Disposition', 'attachment',
                              filename=filename or os.path.basename(attachment_path))
        if content_type:
            attachment.add_header('Content-Type', content_type, name=filename or os.path.basename(attachment_path))

        self.message.attach(attachment)

    def attach_inline_image(self, data, cid=None, mime='image/png'):
        image = MIMEImage(BytesIO(data).read(), _subtype=mime.split('/')[-1])
        if not cid:
            cid = 'ii_' + self._get_unique_id()
        image.add_header('Content-ID', f'<{cid}>')
        image.add_header('X-Attachment-Id', cid)
        image.add_header('Content-Type', mime, filename=f'{cid}.{mime.split("/")[-1].split("+")[0]}')
        self.inline_attachments.append(image)
        return cid

    def get_qrcode(self, force_base64=False):
        short: str = self.data.short
        inline = False if force_base64 else self.config.qr_settings['inline']
        qr_data: str = functions.generate_qr(short, logo_path=self.config.qr_settings['logo_path'],
                                             include_data_attr=not inline)
        if inline:
            return 'cid:' + self.attach_inline_image(qr_data)
        else:
            return qr_data

    def _prepare_smtp(self):
        self.smtp_config['sender_email'] = functions.str_replace(
            self.smtp_config['sender_email'], self.base_search_params)

    def _prepare_short(self) -> str:
        with GENERATOR_LOCK:
            short = functions.str_replace(next(self.config.get_short), self.subject_search_params)
        short = functions.generate_random_string(short)
        short = functions.replace_encoder_fields(short)
        short = functions.replace_base64_fields(short)
        if self.config.shorts_settings['use_shortener']:
            short = functions.url_shortener(self.config.shorts_settings['api_key'], short)
        self.data.short = short
        return short

    def _prepare_body(self):
        self.message_body = functions.str_replace(self.message_body, self.body_search_params)
        self.message_body = functions.obfuscate_links(self.message_body)
        self.message_body = functions.generate_random_string(self.message_body)
        self.message_body = functions.replace_base64_fields(self.message_body)
        self.message_body = functions.replace_zero_pattern(self.message_body)
        self.message_body = functions.replace_hidden_dash(self.message_body)
        self.message_body = functions.replace_encrypted_short(self.message_body, self.data.short)
        self.message_body = functions.replace_encoder_fields(self.message_body)
        self.message_body = self._prepare_text_to_image()
        self._prepare_local_images()
        if self.config.raw_letter['enabled']:
            functions.import_html(self.message, self.message_body)
        else:
            html_part = MIMEText(self.message_body, 'html', 'utf-8')
            plain_part = MIMEText(self._prepare_replace_tags(self.config.plain_message_content), 'plain', 'utf-8')
            plain_part["Content-Disposition"] = "inline"
            if self.config.content_encoding == 'quoted-printable':
                encoders.encode_quopri(html_part)
                encoders.encode_quopri(plain_part)
                html_part.replace_header('Content-Transfer-Encoding', 'quoted-printable')
                plain_part.replace_header('Content-Transfer-Encoding', 'quoted-printable')
            elif self.config.content_encoding in ['7bit', '8bit']:
                encoders.encode_7or8bit(html_part)
                encoders.encode_7or8bit(plain_part)
            elif self.config.content_encoding == 'binary':
                content = html_part.get_payload(decode=True)
                html_part['Content-Transfer-Encoding'] = 'binary'
                html_part.set_payload(content)
                content = plain_part.get_payload(decode=True)
                plain_part['Content-Transfer-Encoding'] = 'binary'
                plain_part.set_payload(content)

            self.related_message.attach(html_part)
            # self.related_message.attach(plain_part)
            self.message.attach(self.related_message)

    def _prepare_replace_tags(self, _string):
        _string = functions.str_replace(_string, self.body_search_params)
        _string = functions.generate_random_string(_string)
        _string = functions.replace_hidden_dash(_string)
        _string = functions.replace_base64_fields(_string)
        _string = functions.replace_encoder_fields(_string)
        return _string

    def _prepare_contacts(self):
        sender = functions.str_replace(self.smtp_config['sender_email'], self.base_search_params)
        sender = functions.generate_random_string(sender)
        self.smtp_config['sender_email'] = sender
        sender_string = "{}{}".format(self.config.smtp_configuration['sender_name'],
                                      '' if self.config.smtp_configuration['hide_sender'] else f' <{sender}>')
        sender_string = functions.generate_random_string(sender_string)
        sender_string = functions.str_replace(sender_string, self.base_search_params)
        sender_string = functions.replace_hidden_dash(sender_string, True)
        if pattern:=self.config.receivers_csv['name_format']:
            receiver_string = functions.str_replace(pattern, self.base_search_params)
            receiver_string = functions.generate_random_string(receiver_string)
            receiver_string = functions.replace_hidden_dash(receiver_string, True)
            receiver_string = f'{receiver_string} <{self.receiver[Contact.EMAIL]}>'
        else:
            receiver_string = self.receiver[Contact.EMAIL]

        self.set_contacts(receiver_string, sender_string)

    def _prepare_headers(self):
        if 'Message-Id' in self.message:
            del self.message['Message-Id']
        if 'Date' in self.message:
            del self.message['Date']

        self.message['Message-Id'] = make_msgid(domain=self.data.domain_local)
        self.message['Date'] = formatdate()

        if not self.config.headers_settings['enabled']:
            return

        d = datetime.now() - timedelta(weeks=random.randint(3, 11), days=random.randint(1, 30),
                                       hours=random.randint(1, 24), minutes=random.randint(1, 60))
        expMail = datetime.now() + timedelta(days=1, hours=random.randint(1, 12), minutes=random.randint(1, 60))
        if self.config.headers_settings['organization']:
            self.message.add_header('Sensitivity', 'Company-Confidential')
            self.message.add_header("Expires", expMail.strftime("%a, %d %b %Y %H:%M:%S %z"))
            self.message.add_header("Organization",
                                    f"{random.choice(random_data.words)} {random.choice(random_data.words)} Ltd.")
            self.message.add_header('X-Auto-Response-Suppress', 'OOF, DR, RN, NRN, AutoReply')
            self.message.add_header('Auto-Submitted', 'auto-replied')
            x_msys_api = {
                "bcc": ["noreply@" + self.data.local_domain],
                "archive": ["archive@" + self.data.local_domain]
            }
            self.message.add_header('X-MSYS-API', json.dumps(x_msys_api))

            # if self.config.headers_settings['mode'] in ['cc', 'bcc']:
            #     self.message.add_header("Require-Recipient-Valid-Since",
            #                            f"{','.join(bccArrayToSend)}; {d.strftime('%a, %d %b %Y %H:%M:%S %z')}")
            # else:
            self.message.add_header("Require-Recipient-Valid-Since",
                                    f"{self.receiver[Contact.EMAIL]}; {d.strftime('%a, %d %b %Y %H:%M:%S %z')}")
        else:
            self.message.add_header('Sensitivity', 'Private')

        if self.config.headers_settings['unsubscribe'] and not self.message.get('List-Unsubscribe'):
            unsubscribe_link = f"https://{self.data.domain_local}/unsubscribe?sid={self.data.letter_number_mix}"
            self.message.add_header("Unsubscribe", "<{}>".format(unsubscribe_link))
            self.message.add_header("List-Unsubscribe", "<{}>".format(unsubscribe_link))

    def _prepare_subject(self):
        if config.raw_letter['enabled'] and config.raw_letter['use_subject']:
            subject = self.message["Subject"]
            del self.message["Subject"]
        else:
            subject = random.choice(self.config.subjects)

        subject = functions.str_replace(subject, self.subject_search_params)
        subject = functions.generate_random_string(subject)
        subject = functions.replace_base64_fields(subject)
        subject = functions.replace_encoder_fields(subject)
        subject = functions.replace_hidden_dash(subject, True)
        if self.config.subject_encode:
            subject = f"=?UTF-8?B?{base64.b64encode(subject.encode('utf-8')).decode('utf-8')}?="
        self.message["Subject"] = subject

    def _prepare_icalendar(self):
        with open(self.config.icalendar_options['file_path'], 'r') as file:
            html_content = file.read()
        config.spam_target = functions.str_replace(config.spam_target, self.subject_search_params)
        html_content = functions.str_replace(html_content, self.convertor_search_params)
        html_content = functions.obfuscate_links(html_content)
        html_content = functions.generate_random_string(html_content)
        html_content = functions.replace_base64_fields(html_content)
        html_content = functions.replace_encoder_fields(html_content)
        html_content = functions.replace_zero_pattern(html_content)
        html_content = functions.replace_hidden_dash(html_content)
        html_content = self._prepare_text_to_image(html_content, force_base64=True)

        # Generate iCalendar event
        event = Event()
        event.add('summary', f"{config.spam_target.split('.')[0].upper()} - support@{config.spam_target}")
        event.add('description', html_content)

        # Set start and end time
        start_time = datetime.now() + timedelta(minutes=random.randint(1, 10))
        end_time = start_time + timedelta(hours=1, minutes=random.randint(1, 60))
        event.add('dtstart', start_time)
        event.add('dtend', end_time)

        # Add an alarm
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f"{config.spam_target.split('.')[0].upper()} - support@{config.spam_target}")
        alarm.add('trigger', timedelta(minutes=30))
        event.add_component(alarm)

        # Set organizer
        organizer = vCalAddress('MAILTO:support@account.' + config.spam_target)
        organizer.params['cn'] = vText(str.upper(config.spam_target.split(".")[0]))
        event['organizer'] = organizer

        # Set URL if 'short' is not empty
        if short := self.data.short:
            event.add('url', vUri(short))

        # Create iCalendar container
        icalendar = Calendar()
        icalendar.add_component(event)

        self.attach_file(attachment_data=icalendar.to_ical().replace(b'DESCRIPTION:', b'X-ALT-DESC;FMTTYPE=text/html:'),
                         filename=f'{self.message["To"].split(",")[0]}-cal.ics',
                         content_type='text/calendar')

    def _prepare_config_attachments(self, message=None, force_base64=False):
        message = message or self.message_body
        if not self.config.extra_attachments.get('enabled'):
            return message
        for attachment in self.config.extra_attachments['list']:

            attachment: Union[enums.Attachment.File, enums.Attachment.InlineImage, enums.Attachment.Base64Image]

            with open(attachment.file_path, 'rb') as file:
                if isinstance(attachment,
                              enums.Attachment.InlineImage) and not force_base64 and attachment.custom_tag in message:
                    self.attach_inline_image(file.read(), attachment.custom_tag.strip('# '))
                    message = message.replace(attachment.custom_tag, 'cid:%s' % attachment.custom_tag.strip('# '))

                elif isinstance(attachment, enums.Attachment.Base64Image) or (
                        isinstance(attachment, enums.Attachment.InlineImage) and force_base64):
                    message = message.replace(attachment.custom_tag, functions.image_to_base64(image_data=file.read()))

                elif isinstance(attachment, enums.Attachment.File):
                    filename = functions.str_replace(attachment.file_name, self.subject_search_params)
                    filename = filename or attachment.file_path.split('/')[-1]
                    mime_type = attachment.mime_type or functions.get_mime_type(filename)
                    self.attach_file(attachment_data=file.read(), filename=filename or None, content_type=mime_type)
        if not force_base64:
            self.message_body = message
        return message

    def _prepare_text_to_image(self, message=None, font_path=None, force_base64=False):
        message = message or self.message_body
        font_path = font_path or self.config.text_to_image['font_path']
        pattern = r"#tti-(\d+)#\[(.*?)\]"

        def generate_image_tag(match):
            font_size = int(match.group(1))
            words = match.group(2)
            images = functions.words_to_images(words, font_size, font_path)
            image_tags = []

            for image in images:
                img_id = self._get_unique_id()
                if not force_base64 and self.config.text_to_image['inline']:
                    image_tag = f'<img id={img_id} src="cid:{self.attach_inline_image(base64.b64decode(image))}" />'
                else:
                    image_tag = f'<img id={img_id} src="data:image/png;base64,{image}" />'
                # image_tags.append(f"""
                # <style>
                #     #{img_id} {{
                #         margin-bottom: calc(-{font_size}*0.3px);
                #     }}
                # </style>
                # """)
                image_tags.append(image_tag)

            return "".join(image_tags)

        result_html = re.sub(pattern, generate_image_tag, message)
        return result_html

    def _prepare_local_images(self, message=None, force_base64=False):
        pattern = r"#local_image#\[(.*?)\]"
        input_string = message or self.message_body

        def replace_src(match):
            image_path = match.group(1)
            mime_type = functions.get_mime_type(image_path)
            with open(image_path, 'rb') as file:
                image = file.read()
            if not force_base64 and config.local_images['inline']:
                return f'cid:{self.attach_inline_image(image, mime=mime_type)}'
            else:
                return functions.image_to_base64(image_data=image, mime=mime_type)

        result = re.sub(pattern, replace_src, input_string)
        if not message:
            self.message_body = result
        return result

    def _prepare_inline_attachments(self):
        for attachment in self.inline_attachments:
            if attachment['X-Attachment-Id'] not in self.message_body:
                continue
            self.related_message.attach(attachment)

    def _prepare_sign_dkim(self):
        if not self.config.sign_dkim["enabled"]:
            return

        with open(self.config.sign_dkim["private_key"], "r") as file:
            private_key = file.read()

        # Create the DKIM signature
        sig = dkim.sign(
            self.message_body.encode('utf-8'), self.config.sign_dkim["selector"].encode('utf-8'),
            self.data.local_domain.encode('utf-8'), private_key.encode('utf-8')
        )

        # Add the DKIM signature to the message
        # self.message.add_header('DKIM-Signature', sig.decode('utf-8'))
        # You can ignore specific headers if required
        self.message.add_header('DKIM-Signature', sig.decode('utf-8'), ignore_headers=['MyTrackingID', 'Return-Path'])

    def _prepare_pdf_password(self):
        pdf_password = self.config.html_to_pdf_options.get('password', '')
        pdf_password = functions.generate_random_string(pdf_password)
        pdf_password = functions.str_replace(pdf_password, self.subject_search_params)
        self.data.pdf_password = pdf_password

    def _convert_to_pdf(self, html_content=None):
        if not self.config.html_to_pdf_options['enabled']:
            return
        if not html_content:
            with open(self.config.html_to_pdf_options['file_path'], 'r+') as f:
                html_content = f.read()
        html_content = functions.str_replace(html_content, self.convertor_search_params)
        html_content = functions.generate_random_string(html_content)
        html_content = functions.replace_zero_pattern(html_content)
        html_content = functions.replace_base64_fields(html_content)
        html_content = functions.replace_encoder_fields(html_content)
        html_content = self._prepare_local_images(html_content, True)
        html_content = self._prepare_config_attachments(html_content, True)
        html_content += f'\n<span style="opacity: 0.01">{self._get_unique_id()}</span>\n'
        filename = functions.str_replace(config.html_to_pdf_options['file_name'], self.subject_search_params)
        output_path = f'temp/{random.randint(1000, 3000)}.pdf'
        pdfkit.from_string(html_content, output_path, options=self.config.html_to_pdf_options['generator_settings'])

        if self.config.html_to_pdf_options['encrypt']:
            writer = PdfWriter()
            reader = PdfReader(output_path)
            for page in reader.pages:
                writer.add_page(page)
            writer.encrypt(self.data.pdf_password)
            writer.write(output_path)

        self.attach_file(output_path, filename=filename, content_type='application/pdf')
        os.remove(output_path)

    def _convert_to_image(self, html_content=None, force_base64=False):
        if not self.config.html_to_image_options['enabled']:
            return
        if not html_content:
            with open(self.config.html_to_image_options['file_path'], 'r+') as f:
                html_content = f.read()
        html_content = functions.str_replace(html_content, self.convertor_search_params)
        html_content = functions.generate_random_string(html_content)
        html_content = self._prepare_local_images(html_content, True)
        html_content = self._prepare_config_attachments(html_content, True)
        html_content += f'\n<span style="opacity: 0.01">{self._get_unique_id()}</span>\n'
        output_path = f'temp/{random.randint(1000, 3000)}.png'
        imgkit.from_string(html_content, output_path, options=self.config.html_to_image_options['generator_settings'])

        with open(output_path, 'rb') as f:
            image_content = f.read()
        os.remove(output_path)
        inline = False if force_base64 else self.config.html_to_image_options['inline']
        if inline:
            return 'cid:' + self.attach_inline_image(image_content)
        else:
            return 'data:image/png;base64,' + base64.b64encode(image_content).decode('utf-8')

    def set_contacts(self, _receivers: Union[str, List[str]], sender: str):
        if 'To' in self.message:
            del self.message['To']
        if 'From' in self.message:
            del self.message['From']

        self.message['To'] = ', '.join(receivers if isinstance(_receivers, list) else [_receivers])
        self.message['From'] = sender

    @property
    def base_search_params(self):
        return {
            '#date#': self.data.date,
            '#old_date#': self.data.old_date,
            '#email#': self.data.email,
            '#email_base64#': self.data.email_base64,
            '#email_id#': self.data.email_id,
            '#receiver_id#': self.data.receiver_id,
            '#target_username#': self.data.receiver_id,
            '#csv_firstname#': self.data.csv_firstname,
            '#csv_lastname#': self.data.csv_lastname,
            '#csv_address#': self.data.csv_address,
            '#csv_birth#': self.data.csv_birth,
            '#csv_phone#': self.data.csv_phone,
            '#word#': self.data.word,
            '#us_name#': self.data.us_name,
            '#fr_name#': self.data.fr_name,
            '#de_name#': self.data.de_name,
            '#jp_name#': self.data.jp_name,
            '#ca_name#': self.data.ca_name,
            '#us_address#': self.data.us_address,
            '#fr_address#': self.data.fr_address,
            '#de_address#': self.data.de_address,
            '#jp_address#': self.data.jp_address,
            '#ca_address#': self.data.ca_address,
            '#us_phone#': self.data.us_phone,
            '#fr_phone#': self.data.fr_phone,
            '#de_phone#': self.data.de_phone,
            '#jp_phone#': self.data.jp_phone,
            '#ca_phone#': self.data.ca_phone,
            '#fake_text#': self.data.fake_text,
            '#fake_email#': self.data.fake_email,
            '#company#': self.data.company,
            '#lipsum#': self.data.lipsum,
            '#giftcode#': self.data.giftcode,
            '#letter_up#': self.data.letter_up,
            '#letter_mix#': self.data.letter_mix,
            '#letter_low#': self.data.letter_low,
            '#letter_number#': self.data.letter_number,
            '#letter_number_up#': self.data.letter_number_up,
            '#letter_number_mix#': self.data.letter_number_mix,
            '#number#': self.data.number,
            "#dolar#": self.data.dolar,
            "#dolar_ca#": self.data.dolar_ca,
            "#euro#": self.data.euro,
            "#jpy#": self.data.jpy,
            "#cash_tag#": self.data.cash_tag,
            '#ip#': self.data.ip,
            '#amz_ip#': self.data.amz_ip,
            '#ovh_ip#': self.data.ovh_ip,
            '#ionos_ip#': self.data.ionos_ip,
            '#chimp_ip#': self.data.chimp_ip,
            '#os#': self.data.os,
            '#country#': self.data.country,
            '#browser#': self.data.browser,
            '#user_agent_mac#': self.data.user_agent_mac,
            '#user_agents_windows#': self.data.user_agents_windows,
            '#local_domain#': self.data.local_domain,
            '#domain_local#': self.data.domain_local,
            '#domain_receiver#': self.data.domain_receiver,
            '#domain_smtp#': self.data.domain_smtp,
            '#short#': self.data.short,
            '#pdf_password#': self.data.pdf_password,
        }

    @property
    def body_search_params(self):
        return {
            **self.base_search_params,
            '#qrcode#': self.get_qrcode(),
            '#unicode_qrcode#': self.get_unicode_qrcode(),
            '#html2image#': self._convert_to_image(),
        }

    @property
    def subject_search_params(self):
        return {
            **self.base_search_params,
        }

    @property
    def convertor_search_params(self):
        return {
            **self.base_search_params,
            '#qrcode#': self.get_qrcode(True),
        }

    def get_unicode_qrcode(self):
        short = self.data.short
        return functions.generate_unicode_qr_code(short,
                                                  self.config.unicode_qr_settings['font_size'],
                                                  self.config.unicode_qr_settings['foreground_color'],
                                                  self.config.unicode_qr_settings['background_color'],)


class ConnectionPool:
    def __init__(self, pool_size=100, max_retries=3):
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.connection_queue = queue.Queue(maxsize=pool_size)
        # self._create_connections()

    def _create_connections(self):
        for _ in range(self.pool_size):
            self._create_new_connection()

    def _create_new_connection(self):
        smtp_configuration: dict = next(config.get_smtp_configuration)
        proxy = None
        if config.proxy_configuration['enabled']:
            proxy: Optional[dict] = next(config.get_proxy).copy()
        connection = create_smtp_connection(smtp_configuration.copy(), proxy=proxy, starttls=config.smtp_configuration['starttls'])
        connection.smtp_configuration = smtp_configuration
        connection.usage = 0
        self.connection_queue.put(connection)

    def get_connection(self):
        try:
            return self.connection_queue.get(block=False)
        except queue.Empty:
            self._create_new_connection()
            return self.get_connection()

    def release_connection(self, connection):
        connection.usage += 1
        if connection.usage < config.smtp_configuration.get('connection_recycle_limit', 10):
            self.connection_queue.put(connection)
        else:
            connection.close()


class Counter:
    def __init__(self, start=0):
        self.value = start

    def increase(self, value=1):
        self.value += value
        return self.value

    def decrease(self, value=1):
        self.value -= value
        return self.value + value


def create_smtp_connection(smtp_server: Union[str, dict], *,
                           smtp_port: int = None,
                           smtp_user: str = None, smtp_pass: str = None, proxy: dict = None, starttls=True):
    # Configure the smtp server info
    if isinstance(smtp_server, dict):
        smtp_port = smtp_server['port']
        smtp_user = smtp_server.get('user')
        smtp_pass = smtp_server.get('pass')
        smtp_server = smtp_server['host']

    d_print([], 'Current Config:', {
        'host': smtp_server,
        'port': smtp_port,
        'user': smtp_user,
        'pass': smtp_pass,
    })

    original_socket = socket.socket
    # Configure proxy if provided
    if proxy:
        if proxy['protocol'] in ['http', 'https']:
            proxy_type = socks.HTTP
        elif proxy['protocol'] == 'socks4':
            proxy_type = socks.SOCKS4
        elif proxy['protocol'] == 'socks5':
            proxy_type = socks.SOCKS5
        else:
            proxy_type = socks.HTTP
        del proxy['protocol']

        socks.set_default_proxy(proxy_type, **proxy)

    safe_print(f'{functions.text_blue("[Connect]")} Creating new SMTP connection...')
    # Create an SMTP connection
    try:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=config.multi_thread_settings['timeout'])
    finally:
        socket.socket = original_socket
    if config.debug:
        server.set_debuglevel(1)

    d_print(['Info'], 'Sending SMTP hello command')
    server.ehlo('mylowercasehost')

    d_print(['Info'], 'Starting TLS connection')
    # Enable TLS encryption

    try:
        if starttls:
            server.starttls()
    except smtplib.SMTPNotSupportedError:
        safe_print(f"{functions.text_red('[Error]')} Server doesn't support STARTTLS, "
                   f'please disable it and try again.')
        exit(1)

    try:
        server.ehlo('mylowercasehost')

        # Authenticate with SMTP credentials if provided
        if smtp_user and smtp_pass:
            d_print(['Info'], 'Logging in with SMTP')
            server.login(smtp_user, smtp_pass)

    except smtplib.SMTPAuthenticationError as e:
        if 'STARTTLS' in e.smtp_error.decode():
            error = 'STARTTLS is required, please enable it and try again.'
        else:
            error = e.smtp_error.decode()
        safe_print(f'{functions.text_red("[Error]")} {error}')
        exit(1)

    return server


def send_email(connection: smtplib.SMTP, message: EmailMessage, receiver_email: Union[str, List[str]],
               smtp_from: str = None):
    smtp_from = smtp_from.replace('#target_username#', receiver_email.split('@')[0])

    # Convert the message to a string
    message_str = message.as_string()

    # Send the email
    result = connection.sendmail(smtp_from, receiver_email, message_str)

    safe_print(f'{functions.text_green("[Sent]")} '+functions.text_magenta(f'[{len(receivers)}/{message_counter.decrease()}]')+f' [{receiver_email}]')
    return result


def run_config(_receiver):
    d_print([], 'Preparing for:', _receiver[Contact.EMAIL])
    try:
        # smtp_configuration: dict = next(config.get_smtp_configuration)
        # connection = create_smtp_connection(preparer.smtp_config, starttls=config.smtp_configuration['starttls'])
        connection = connection_pool.get_connection()
        preparer = PrepareMessage(config, _receiver, connection.smtp_configuration.copy(), True)
        safe_print(f'{functions.text_magenta("[Sending]")} [{_receiver[Contact.EMAIL]}] Sending data to smtp')
        send_email(connection, preparer.message, _receiver[Contact.EMAIL], preparer.smtp_config.get('sender_email'))
        connection_pool.release_connection(connection)
        log_file_done.write(f'{_receiver[Contact.EMAIL]}\n')
    except SystemExit as e:
        exit(e.code)
    except Exception as e:
        log_file_fail.write(f'{_receiver[Contact.EMAIL]}\n')
        safe_print(f'{functions.text_red("[Error]")} [{_receiver[Contact.EMAIL]}] {e}')
        safe_print(f'{functions.text_red("[Trace]")} {traceback.format_exc()}')
        exit()


async def run_config_async(_receiver, semaphore):
    async with semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_config, _receiver)


def run_from_csv():
    safe_print(f'{functions.text_blue("[Info]")} Loaded receivers count: {len(receivers)}')
    # run_config(receivers[0])

    with ThreadPoolExecutor(config.multi_thread_settings['max_workers']) as executor:
        executor.map(run_config, receivers)


async def run_from_csv_async():
    safe_print(f'{functions.text_blue("[Info]")} Loaded receivers count: {len(receivers)}')
    semaphore = asyncio.Semaphore(config.multi_thread_settings['max_workers'])

    await asyncio.gather(*[run_config_async(receiver, semaphore) for receiver in receivers], return_exceptions=True)


if __name__ == '__main__':
    date = datetime.now()
    safe_print(f"{functions.text_blue('[Info]')} Current date: {date.strftime('%Y-%m-%d %H:%M:%S')}")
    d_print([], 'Creating needed directories, if not exist')
    # Create directories if they don't exist
    directories = ['letter', 'receivers', 'temp', 'smtp', 'log_files']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    d_print([], 'Load SMTP list')
    smtp_list = functions.load_smtp_file(config.smtp_configuration)
    config.get_smtp_configuration = functions.rotate_list(smtp_list, config.smtp_configuration.get('rotate_smtp', False))
    config.get_short = functions.rotate_list(config.shorts_settings['list'], config.shorts_settings['rotate'])

    if config.proxy_configuration['enabled']:
        proxy_list = functions.load_proxy_file(config.proxy_configuration)
        config.get_proxy = functions.rotate_list(proxy_list, config.proxy_configuration.get('rotate_list', False))

    safe_print(f'{functions.text_blue("[Info]")} Loaded SMTP count: {len(smtp_list)}')
    connection_pool = ConnectionPool()
    d_print([], 'Loading receivers')
    receivers = functions.load_csv_file(**config.receivers_csv)
    message_counter = Counter(len(receivers))

    log_file_done = open(f'log_files/done_{date.strftime("%Y-%m-%d_%H-%M-%S")}.txt', 'a')
    log_file_fail = open(f'log_files/fail_{date.strftime("%Y-%m-%d_%H-%M-%S")}.txt', 'a')
    try:
        if config.multi_thread_settings['use_asyncio']:
            asyncio.run(run_from_csv_async())
        else:
            run_from_csv()
    except KeyboardInterrupt:
        safe_print(f'{functions.text_magenta("[CTRL+C]")} Stopping...')

    safe_print(f'{functions.text_magenta("[Exit]")} Process done!')
