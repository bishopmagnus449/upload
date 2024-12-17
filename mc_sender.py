import asyncio
import base64
import os
import random
import re
import sys
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Lock

import colorama
import imgkit
import requests
from faker import Faker

import config
import functions
import random_data

colorama.init()
d_print = functions.d_print(config.debug)
GENERATOR_LOCK = Lock()


class MailData:
    faker_us = Faker()
    faker_fr = Faker('fr_FR')
    faker_de = Faker('de_DE')
    faker_jp = Faker('ja_JP')
    faker_ca = Faker('en_CA')

    def __init__(self, receiver):
        self.date = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.old_date = (datetime.now() - timedelta(days=random.randint(1, 3), hours=random.randint(1, 24),
                                                    minutes=random.randint(1, 60))).strftime("%m/%d/%Y %I:%M:%S %p")
        self.email = receiver
        self.company = receiver.split('@')[1].split('.')[0].capitalize()
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
        self.domain_receiver = self.email.split('@')[-1]
        self.short = ''
        self.pdf_password = ''

class Counter:
    def __init__(self, count):
        self.count = count

    def lower(self):
        self.count -= 1
        return self.count

    def upper(self):
        self.count += 1
        return self.count


class PrepareMessage:
    def __init__(self, _config, _receiver: str, init_message=False):

        self.receiver = _receiver
        self.config = _config
        self.message = {
            "from": {
                "name": self.config.mailchannels['sender_name'],
                "email": self.config.mailchannels['sender_address']
            },
            "to": {
                "email": self.receiver
            },
            "content": {
                "subject": '',
                "html": '',
            }
        }

        self.data = MailData(self.receiver)

        if init_message:
            self.init_message()
            self.data = MailData(self.receiver)

    def init_message(self):
        self._prepare_short()
        with open(config.letter, 'r+') as f:
            self.message['content']['html'] = f.read()
        self._prepare_subject()
        self._prepare_body()

    def get_qrcode(self):
        short: str = self.data.short
        qr_data: str = functions.generate_qr(short, logo_path=self.config.qr_settings['logo_path'],
                                             include_data_attr=True)
        return qr_data

    def _prepare_local_images(self, message=None):
        pattern = r"#local_image#\[(.*?)\]"
        input_string = message

        def replace_src(match):
            image_path = match.group(1)
            mime_type = functions.get_mime_type(image_path)
            with open(image_path, 'rb') as file:
                image = file.read()
            return functions.image_to_base64(image_data=image, mime=mime_type)

        result = re.sub(pattern, replace_src, input_string)
        if not message:
            self.message['content']['html'] = result
        return result

    def _prepare_subject(self):
        subject = functions.str_replace(random.choice(self.config.subjects), self.subject_search_params)
        subject = functions.generate_random_string(subject)
        subject = functions.replace_base64_fields(subject)
        subject = functions.replace_encoder_fields(subject)
        if self.config.subject_encode:
            subject = f"=?UTF-8?B?{base64.b64encode(subject.encode('utf-8')).decode('utf-8')}?="
        self.message['content']['subject'] = subject

    def _prepare_body(self):
        message_body = functions.str_replace(self.message['content']['html'], self.body_search_params)
        message_body = functions.obfuscate_links(message_body)
        message_body = functions.generate_random_string(message_body)
        message_body = functions.replace_base64_fields(message_body)
        message_body = functions.replace_encoder_fields(message_body)
        message_body = functions.replace_zero_pattern(message_body)
        message_body = self._prepare_local_images(message_body)
        self.message['content']['html'] = message_body

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

    def _convert_to_image(self, html_content=None):
        if not self.config.html_to_image_options['enabled']:
            return
        if not html_content:
            with open(self.config.html_to_image_options['file_path'], 'r+') as f:
                html_content = f.read()
        html_content = functions.str_replace(html_content, self.convertor_search_params)
        html_content = functions.generate_random_string(html_content)
        html_content = self._prepare_local_images(html_content)
        html_content += f'\n<span style="opacity: 0.01">{self._get_unique_id()}</span>\n'
        output_path = f'temp/{random.randint(1000, 3000)}.png'
        imgkit.from_string(html_content, output_path, options=self.config.html_to_image_options['generator_settings'])

        with open(output_path, 'rb') as f:
            image_content = f.read()
        os.remove(output_path)
        return 'data:image/png;base64,' + base64.b64encode(image_content).decode('utf-8')


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
            '#short#': self.data.short,
            '#pdf_password#': self.data.pdf_password,
        }

    @property
    def body_search_params(self):
        return {
            **self.base_search_params,
            '#qrcode#': self.get_qrcode(),
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
            '#qrcode#': self.get_qrcode(),
        }

    @staticmethod
    def _get_unique_id():
        return str(uuid.uuid4()).split('-')[0]


def run_config(_receiver: str):
    try:
        _receiver = _receiver.strip('\n ')
        d_print([], 'Preparing for:', _receiver)
        config.get_short = functions.rotate_list(config.shorts_settings['list'], config.shorts_settings['rotate'])

        message = PrepareMessage(config, _receiver, True)
        result = requests.post(config.mailchannels['worker_url'], json=message.message)
        print(result.text)

        log = functions.text_blue(f"[{receivers_count.lower()}]")
        functions.safe_print(f'{functions.text_green("[Sent]")} {log} [{_receiver}]')

    except Exception as e:
        log_file_fail.write(f'{_receiver}\n')
        functions.safe_print(f'{functions.text_red("[Error]")} [{_receiver}] {e}')
        functions.safe_print(f'{functions.text_red("[Trace]")} {traceback.format_exc()}')
        exit()

def run_from_csv():
    d_print([], 'Loading receivers')
    with open(config.receivers_csv['file_path'], 'r+') as f:
        receivers = f.readlines()
    receivers_count.count = len(receivers)
    functions.safe_print(f'{functions.text_blue("[Info]")} Loaded receivers count: {len(receivers)}')
    # run_config(receivers[0])

    with ThreadPoolExecutor(config.multi_thread_settings['max_workers']) as executor:
        executor.map(run_config, receivers)


async def run_from_csv_async():
    d_print([], 'Loading receivers')
    with open(config.receivers_csv['file_path'], 'r+') as f:
        receivers = f.readlines()
    receivers_count.count = len(receivers)
    functions.safe_print(f'{functions.text_blue("[Info]")} Loaded receivers count: {len(receivers)}')

    with ThreadPoolExecutor(config.multi_thread_settings['max_workers']) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, run_config, receiver) for receiver in receivers]

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    receivers_count = Counter(0)
    directories = ['letter', 'receivers', 'temp', 'smtp', 'log_files']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    date = datetime.now()
    log_file_done = open(f'log_files/done_{date.strftime("%Y-%m-%d_%H-%M-%S")}.txt', 'a')
    log_file_fail = open(f'log_files/fail_{date.strftime("%Y-%m-%d_%H-%M-%S")}.txt', 'a')

    try:
        if config.multi_thread_settings['use_asyncio']:
            asyncio.run(run_from_csv_async())
        else:
            run_from_csv()
    except KeyboardInterrupt:
        functions.safe_print(f'{functions.text_magenta("[Exit]")} Process exited by user')
        sys.exit(0)

    functions.safe_print(f'{functions.text_magenta("[Exit]")} Process done!')
