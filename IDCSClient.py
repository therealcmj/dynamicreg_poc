import json
import logging

# OAuth stuff
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

# # debug HTTP
# import http.client as http_client
# http_client.HTTPConnection.debuglevel = 1

class IDCSClient:
    idcsUrl = None
    clientID = None
    clientSecret = None
    accessToken = None

    oauthClient = None

    def __init__(self, idcsURL, clientID, clientSecret):
        self.idcsUrl = idcsURL
        # save these just in case
        self.clientID = clientID
        self.clientSecret = clientSecret

        auth = HTTPBasicAuth(clientID, clientSecret)
        client = BackendApplicationClient(client_id=clientID)
        self.oauthClient = OAuth2Session(client=client)

        # if this fails it will throw an exception.
        # and that's a good thing
        token = self.oauthClient.fetch_token(   token_url=idcsURL + '/oauth2/v1/token',
                                                auth=auth,
                                                scope=["urn:opc:idm:__myscopes__"])
        logging.debug( "Access Token: {}".format(token.get("access_token")))
        self.accessToken = token.get("access_token")
        return

    def GetUsers(self):
        response = self.oauthClient.get(self.idcsUrl + "/admin/v1/Users")
        print("Status code: {}".format(response.status_code))
        if response.ok:
            print( "Response indicates success" )
        else:
            print( "Error!" )

    def GetApps(self):
        response = self.oauthClient.get(self.idcsUrl + "/admin/v1/Apps")
        print("Status code: {}".format(response.status_code))
        if response.ok:
            print( "Response indicates success" )
        else:
            print( "Error!" )

    def GetAppsPost(self):
        response = self.oauthClient.post(self.idcsUrl + "/admin/v1/Apps/.search",
                                         json=json.dumps({
                                             "schemas": [ "urn:ietf:params:scim:api:messages:2.0:SearchRequest" ]
                                                        })
                                         )
        print("Status code: {}".format(response.status_code))
        if response.ok:
            print( "Response indicates success" )
        else:
            print( "Error!" )


    def CreateApp(self, clientName, redirectUris):
        appPayload = {
            "displayName": clientName,
            "redirectUris": redirectUris,

            # the rest of these are more or less "fixed" values needed for an OAuth app
            "allUrlSchemesAllowed": True,
            "description": "created via DCR PoC code",
            "clientType": "confidential",
            "allowedGrants": [
                "authorization_code"
            ],
            "isOAuthClient": True,
            "basedOnTemplate": {
                "value": "CustomWebAppTemplateId"
            },
            "schemas": [
                "urn:ietf:params:scim:schemas:oracle:idcs:App"
            ]
        }

        createResponse = self._sendRequest( "POST", "/admin/v1/Apps", appPayload )

        id = createResponse.get("id")
        if not id:
            raise Exception("Failed to get ID for newly created app!" )

        # we need client ID, secret


        appActivatePayload = {"active": True, "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:AppStatusChanger"]}
        activateResponse = self._sendRequest( "PUT", "/admin/v1/AppStatusChanger/" + id, appActivatePayload )

        return (createResponse.get("name"), createResponse.get("clientSecret"))

    def _sendRequest(self, verb, uri, jsonpayload):
        logging.debug("Sending POST payload:")
        logging.debug(json.dumps(jsonpayload))

        # response = self.oauthClient.post(self.idcsUrl + uri,
        response = self.oauthClient.request(verb, self.idcsUrl + uri,
                                     json = jsonpayload,
                                     headers = {
                                         "Content-Type":"application/scim+json",
                                         "Accept":"application/scim+json,application/json"
                                     })

        logging.debug("Status code: {}".format(response.status_code))
        logging.debug(response.headers)
        logging.debug(response.text)
        if response.ok:
            logging.debug( "Response indicates success" )
            logging.debug(response.content)
            logging.debug(json.dumps(response.json()))
            return response.json()
        else:
            # anything other than "OK" from IDCS means error
            logging.error("Error making HTTP request")
            raise Exception( "HTTP request failed" )
