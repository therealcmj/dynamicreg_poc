import io
import json
import logging

import time
from datetime import datetime

from fdk import response


def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().info("Inside Python handler")

    password = ctx.Config().get("PASSWORD")
    logging.getLogger().debug("Got password {}".format(password))

    try:
        logging.getLogger().debug("Input data: {}".format(data.getvalue()))
        body = json.loads(data.getvalue())
        logging.getLogger().debug("JSON payload parsed:" + json.dumps(body))
        token = body.get("token")

        logging.getLogger().debug("Got token '{}' from request".format(token))

        if token == password:
            logging.getLogger().info("Token matches required password")
            return response.Response(
                ctx, response_data=json.dumps(
                    {
                        "active": True,
                        "expiresAt": datetime.fromtimestamp(time.time()+600).isoformat()
                    }
                ))

    except (Exception, ValueError) as ex:
        logging.getLogger().info('Exception encountered: ' + str(ex))

    logging.getLogger().info("Rejecting access attempt")

    return response.Response(
        ctx, response_data=json.dumps(
            {
                "active": False,
                "expiresAt": datetime.fromtimestamp(time.time()).isoformat(),
                "wwwAuthenticate": "Authentication_required"
            }
        )
    )
