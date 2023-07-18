import logging
from logging.handlers import TimedRotatingFileHandler
import requests
import os
from xml.etree import ElementTree
from dotenv import load_dotenv
import base64
from http import HTTPStatus
import messages
import time

from settings import SLEEPING_TIME, objects, NB, ALL

load_dotenv()

soap_link_login = 'http://teamaxess.com/IAxCounterMSI/login'
soap_link_info = 'http://teamaxess.com/IAxCounterMSI/getCounterSetList'
soap_link_logout = 'http://teamaxess.com/IAxCounterMSI/logout'

URL = 'http://pps-app01.rskh.local:16351/CounterMSI/CounterMSIService.svc/soap'

LOGIN_NAME = base64.b64decode(os.getenv('LOGIN')).decode('utf-8')
PASSWORD = base64.b64decode(os.getenv('PASSWORD')).decode('utf-8')
PARKING_NAME = (
    './/{http://schemas.datacontract.org/2004/07/AxWebServices}SZNAME'
)
PARKING_VOLUME = (
    './/{http://schemas.datacontract.org/2004/07/AxWebServices}NVALUE'
)
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
BODY_PARKING_INFORMATION = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:team="http://teamaxess.com/">
   <soapenv:Header/>
   <soapenv:Body>
      <team:getCounterSetList>
         <team:i_nSessionId>{}</team:i_nSessionId>
         <team:i_szTimeStamp></team:i_szTimeStamp>
      </team:getCounterSetList>
   </soapenv:Body>
</soapenv:Envelope>
"""
BODY_LOGOUT_SESSION = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:team="http://teamaxess.com/">
   <soapenv:Header/>
   <soapenv:Body>
      <team:logout>
         <team:i_nSessionId>{}</team:i_nSessionId>
         <team:i_szUsername>{}</team:i_szUsername>
         <team:i_szPassword>{}</team:i_szPassword>
      </team:logout>
   </soapenv:Body>
</soapenv:Envelope>
"""
counter = 0


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


def get_parkings_informations(url, body, soap_action):
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
            messages.SERVER_ERROR_MESSAGE.format(response.status_code)
        )
    parking_info = ElementTree.fromstring(response.content).findall(
        './/{http://schemas.datacontract.org/2004/07/AxWebServices}CMSICOUNTER'
    )
    parking_data = {}
    for info in parking_info:
        parking_data[info.findall(PARKING_NAME)[0].text.replace(
            'МестСвободно', ''
        )] = int(info.findall(PARKING_VOLUME)[0].text)
    return parking_data


def logout_session(url, body, soap_action):
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
            messages.SERVER_ERROR_MESSAGE.format(response.status_code)
        )
    print(response.text)


def work_with_cmd(object_list, info, counter):
    for object, val in object_list.items():
        for port_values in val['ports'].values():
            if port_values['object'] in info:
                counter += info[port_values['object']]
            elif port_values['object'] in ('NB',):
                for parking_place in NB:
                    if parking_place in info.keys():
                        counter += info[parking_place]
            elif port_values['object'] in ('ALL',):
                for paprking_place in ALL:
                    if parking_place in info.keys():
                        counter += info[paprking_place]
            os.system(
                'D:/designa/impulse2.exe COM{} {} {} {}'.format(
                    val["COM"],
                    port_values['line'],
                    port_values['window'],
                    counter
                )
            )
            counter = 0


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
    while True:
        try:
            id = get_session_id(URL, BODY_SESSION_INFO, soap_link_login)
            info = get_parkings_informations(
                URL,
                BODY_PARKING_INFORMATION.format(id),
                soap_link_info
            )
            logout_session(
                URL,
                BODY_LOGOUT_SESSION.format(id, LOGIN_NAME, PASSWORD),
                soap_link_logout
            )
            work_with_cmd(objects, info, counter)
            logging.info('{}'.format(info))
        except Exception as error:
            logging.error(error)
        time.sleep(SLEEPING_TIME)
