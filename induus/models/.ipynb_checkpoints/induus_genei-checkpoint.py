# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import requests
import json

_logger = logging.getLogger(__name__)

BASE_URL = "https://www.genei.es/json_interface/"


class Genei(object):
    @staticmethod
    def send(url, company, params=None):
        data = {}

        if params:
            data.update(params)
        data.update({
            "usuario_servicio": company.genei_usuario,
            "password_servicio": company.genei_pass,
            "servicio": "api"
        })

        headers = {"Content-type": "application/json", 'Accept': 'text/plain'}

        _logger.warning("%s%s" % (BASE_URL, url))
        _logger.warning(json.dumps(data))
        
        params = {
            'url': "%s%s" % (BASE_URL, url),
            'params': json.dumps(data)
        }
        try:
            _logger.warning("Lanzo llamada a Genei")
#             r = requests.post("%s%s" % (BASE_URL, url), data=json.dumps(data),
#                               headers=headers, timeout=None)
            r = requests.post("http://araniak.net/genei/genei.php", data=params, timeout=None)
            _logger.warning("Responde Genei")
            r.raise_for_status()
#             _logger.warning(r.content)
#             _logger.warning(r.json())
            return r.json() if r.content else False
        except requests.HTTPError:
            _logger.warning("MALLLLLLLLLLL")
        return None
