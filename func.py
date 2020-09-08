import io
import json
import logging
import time

from fdk import response
from IDCSClient import IDCSClient


# these should come from config
# TODO: that!
idcsURL = "https://idcs-f29b958a146e4bdd9fef12a2e6a9ebcb.identity.oraclecloud.com"
clientID = "95b06d3627a045bfb9f8c9bd8efa1d68"
clientSecret = "1658b892-9d24-4f03-9af2-ded5d48496f4"

# the idcs client code
client = IDCSClient(idcsURL, clientID, clientSecret)

def handler(ctx, data: io.BytesIO=None):
    logging.getLogger().info("Inside handler")

    # default to assuming an error occurred
    # and 500 is as good a default error code as any
    statuscode = 500
    responseBody = {}

    try:
        requestBody = json.loads(data.getvalue())
    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))

    # the only things I get from the Dynamic Client Request body are:
    # 1: token_endpoint_auth_method (which had better be client_secret_basic)
    # 2: client_name
    # 3: redirect_uris
    ram             = requestBody.get("token_endpoint_auth_method")
    clientName      = requestBody.get("client_name")
    redirect_uris   = requestBody.get("redirect_uris")

    if ram != "client_secret_basic":
        # CMJ:
        # per the DCR spec we actually should ignore this input and create the client
        # as we want and return it back to the caller for them to deal with.
        # I'm ignoring that because I don't want to pollute IDCS with lots of bad clients
        raise Exception( "Only client_basic_secret is supported for token_endpoint_auth_method" )
    else:
        (id, secret) = client.CreateApp(clientName, redirect_uris)

        print("Client ID     : {}".format(id))
        print("Client secret : {}".format(secret))

        responseBody = {
            "client_id": id,
            "client_secret": secret,
            "client_id_issued_at": int(time.time()),
            "client_secret_expires_at": 0,

            "client_name": clientName,
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code"],
            "token_endpoint_auth_method": "client_secret_basic"
        }

        statuscode = 200

    return response.Response(
        ctx, status_code=statuscode,
        response_data=json.dumps( responseBody ),
        headers={"Content-Type": "application/json"}
    )
