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
        logging.debug("Initializing IDCS client with the following params:")
        logging.debug("IDCS URL: {}".format(idcsURL))
        logging.debug("Client ID: {}".format(clientID))
        logging.debug("Client Secret: {}".format(clientSecret))

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

    # def GetUsers(self):
    #     logging.debug("GetUsers() called")
    #     response = self.oauthClient.get(self.idcsUrl + "/admin/v1/Users")
    #     print("Status code: {}".format(response.status_code))
    #     if response.ok:
    #         print( "Response indicates success" )
    #     else:
    #         print( "Error!" )

    # def GetApps(self):
    #     logging.debug("GetApps() called")
    #     response = self.oauthClient.get(self.idcsUrl + "/admin/v1/Apps")
    #     print("Status code: {}".format(response.status_code))
    #     if response.ok:
    #         print( "Response indicates success" )
    #     else:
    #         print( "Error!" )

    def CreateApp(self, clientName, redirectUris):
        logging.debug("CreateApp() called")
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

        logging.debug("Getting id from response")
        id = createResponse.get("id")
        if not id:
            logging.debug("ID not present in response!")
            raise Exception("Failed to get ID for newly created app!" )

        logging.debug("Activating newly created app with id {}".format(id))
        self.SetAppActiveStatus( id, True)

        # The caller needs the client ID + secret
        logging.debug("Returning client ID + client secret")
        return (createResponse.get("name"), createResponse.get("clientSecret"))

    def SetAppActiveStatus(self, id, status):
        appActivatePayload = {"active": status, "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:AppStatusChanger"]}
        activateResponse = self._sendRequest( "PUT", "/admin/v1/AppStatusChanger/" + id, appActivatePayload )

    def DeleteApp(self, id):
        logging.debug("Deleting app with ID {}".format(id))
        # in order to delete an app you need to be sure it's deactivated
        self.SetAppActiveStatus(id,False)
        self._sendRequest( "DELETE", "/admin/v1/Apps/" + id, None)
        return

    def DeleteAppWithClientID(self, clientID):
        # IDCS will not allow more than one app to have the same "name"
        # so this will return either 0 or 1 results.
        response = self._sendRequest("GET",
                                     "/admin/v1/Apps?filter=name+eq+%22" + clientID + "%22",
                                     None)

        if response and 1 == response.get("totalResults"):
            #response.get("name") and response.get("id"):
            #return self.DeleteApp(response.get("id"))
            id = response.get("Resources")[0].get("id")
            logging.debug( "Found app to delete - IDCS id is {}".format(id))
            self.DeleteApp(id)
        else:
            logging.error("Could not find app to delete!")
            raise Exception("Unable to find app to delete")

        return

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
        # logging.debug(response.headers)
        # logging.debug(response.text)
        if response.ok:
            logging.debug( "Response indicates success" )
            if response.content:
                logging.debug(response.content)
                if response.text:
                    logging.debug(json.dumps(response.json()))
                    return response.json()
            else:
                return None
        else:
            # anything other than "OK" from IDCS means error
            logging.error("Error making HTTP request")
            if response.text:
                logging.debug(response.text)
            else:
                logging.debug("No content to log")

            raise Exception( "HTTP request failed" )
