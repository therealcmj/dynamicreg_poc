import io
import json
import logging
import time

from fdk import response
from IDCSClient import IDCSClient

#TODO: make the IDCSClient a global variable and initialize it only once

def handler(ctx, data: io.BytesIO=None):
    logging.getLogger().info("Inside handler")

    # we need to initialize the IDCS client using the URL, Client ID, and Client Secret from the config
    idcsURL = ctx.Config().get("IDCSURL")
    clientID = ctx.Config().get("CLIENTID")
    clientSecret = ctx.Config().get("CLIENTSECRET")
    client = IDCSClient(idcsURL, clientID, clientSecret)

    # default to assuming an error occurred
    # and 500 is as good a default error code as any
    statuscode = 500
    responseBody = {}

    if ctx.Method() == "POST":

        try:
            logging.debug("Parsing post payload: '{}'".format(data.getvalue()))
            requestBody = json.loads(data.getvalue())
        except (Exception, ValueError) as ex:
            logging.getLogger().info('error parsing json payload: ' + str(ex))
            raise

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
            logging.debug("Creating app with the following params:")
            logging.debug("Client Name: {}".format(clientName))
            logging.debug("Redirect URLs: {}".format(json.dumps(redirect_uris)))
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

    elif ctx.Method() == "DELETE":
        logging.debug("DELETE request received")
        # get the last part of the URI
        clientID = ctx.RequestURL().split("/")[-1]
        client.DeleteAppWithClientID(clientID)
        statuscode = 200
        responseBody = {"result": "success"}

    return response.Response(
        ctx, status_code=statuscode,
        response_data=json.dumps( responseBody ),
        headers={"Content-Type": "application/json"}
    )
