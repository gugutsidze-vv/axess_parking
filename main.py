import logging
from logging.handlers import TimedRotatingFileHandler
import requests
import os
from xml.etree import ElementTree
from dotenv import load_dotenv
import base64
from http import HTTPStatus
import messages

load_dotenv()

soap_link_login = 'http://teamaxess.com/IAxCounterMSI/login'

URL = 'http://pps-app01.rskh.local:16351/CounterMSI/CounterMSIService.svc/soap'

LOGIN_NAME = base64.b64decode(os.getenv('LOGIN')).decode('utf-8')
PASSWORD = base64.b64decode(os.getenv('PASSWORD')).decode('utf-8')
BODY_SESSION_INFO = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
 xmlns:team="http://teamaxess.com/">
   <soapenv:Header/>
   <soapenv:Body>
      <team:login>
         <team:i_szUsername>{}</team:i_szUsername>
         <team:i_szPassword>{}</team:i_szPassword>
      </team:login>
   </soapenv:Body>
</soapenv:Envelope>""".format(LOGIN_NAME, PASSWORD)
NAMESPACES = {
    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
    'a': 'http://www.etis.fskab.se/v1.0/ETISws'
}


def prepare_log_folder():
    if os.path.isdir('logs') is False:
        os.mkdir('logs')


def get_session_id(url, body, soap_action):
    HEADERS = {
        'content-type': 'text/xml',
        'charset': 'UTF-8',
        'SOAPAction': soap_action
    }
    try:
        response = requests.post(url, data=body, headers=HEADERS)
    except requests.RequestException as error:
        logging.critical(messages.NETWORK_ERROR_MESSAGE.format(url, error))
    if response.status_code != HTTPStatus.OK:
        logging.error(
            messages.SERVER_ERROR_MESSAGE.format(
                response.status_code
            )
        )
    session_id = ElementTree.fromstring(response.content).findall(
        './/{http://schemas.datacontract.org/2004/07/AxWebServices}NSESSIONID'
    )
    if session_id[0].text is None:
        logging.error(messages.SESSION_ID_ERROR)
        raise TypeError
    return session_id[0].text


if __name__ == '__main__':
    prepare_log_folder()
    logdir = os.path.join(
        os.path.normpath(os.getcwd() + os.sep),
        'logs'
    )
    log_filename = os.path.join(logdir, 'parkings.log')
    handler = TimedRotatingFileHandler(
        log_filename,
        when='midnight',
        encoding='utf-8',
        backupCount=31,
    )
    handler.suffix = '%d-%m-%Y'
    logging.basicConfig(
        format=(
            '%(asctime)s [%(levelname)s]: '
            '[%(funcName)s:%(lineno)d] - %(message)s'
        ),
        handlers=[handler],
        level=logging.INFO

    )
    logging.info(messages.START_MESSAGE)
    try:
        id = get_session_id(URL, BODY_SESSION_INFO, soap_link_login)
    except Exception as error:
        logging.error(error)
