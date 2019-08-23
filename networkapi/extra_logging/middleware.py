# -*- coding: utf-8 -*-
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import base64
import logging
import uuid

from django.conf import settings

from networkapi.extra_logging import local
from networkapi.extra_logging import NO_REQUEST_CONTEXT
from networkapi.extra_logging import NO_REQUEST_ID
from networkapi.extra_logging import NO_REQUEST_USER
from networkapi.extra_logging import REQUEST_ID_HEADER
from networkapi.util import search_hide_password

logger = logging.getLogger(__name__)


def get_identity(request):
    x_request_id = getattr(settings, REQUEST_ID_HEADER, None)
    if x_request_id:
        return request.META.get(x_request_id, NO_REQUEST_ID)

    identity = uuid.uuid4().bytes
    encoded_id = base64.urlsafe_b64encode(identity)
    safe_id = encoded_id.replace('=', '')

    return safe_id.upper()


def get_context(request):

    context_key = 'HTTP_X_REQUEST_CONTEXT'
    context = NO_REQUEST_CONTEXT

    if context_key in request.META:
        context = request.META.get(context_key)
    return context


def get_username(request):

    user_key = 'HTTP_NETWORKAPI_USERNAME'
    auth_key = 'HTTP_AUTHORIZATION'
    encoding = 'iso-8859-1'
    username = NO_REQUEST_USER

    if user_key in request.META:
        username = request.META.get(user_key)
        request.is_api = False

    elif auth_key in request.META:
        authorization = request.META.get(auth_key, b'')
        auth = authorization.encode(encoding).split()
        auth_parts = base64.b64decode(auth[1]).decode(encoding).partition(':')
        username = auth_parts[0].upper()
        request.is_api = True

    return username


class ExtraLoggingMiddleware(object):

    def process_request(self, request):

        identity = get_identity(request)
        username = get_username(request)
        local.request_id = identity
        local.request_user = username
        local.request_path = request.get_full_path()
        local.request_context = get_context(request)
        request.id = identity

        msg = u'INICIO da requisição %s. Data: [%s].' % (
            request.method, request.body)
        logger.debug(search_hide_password(msg))

    def process_response(self, request, response):

        if 399 < response.status_code < 600:
            # logger.debug(u'Requisição concluída com falha. Conteúdo: [%s].' % response.content)
            logger.warning(u'Requisição concluída com falha. Conteúdo: [].')
        else:
            logger.debug(u'Requisição concluída com sucesso.')

        logger.debug(u'FIM da requisição.')

        return response

    def process_exception(self, request, exception):

        logger.error(u'Erro não esperado.')
