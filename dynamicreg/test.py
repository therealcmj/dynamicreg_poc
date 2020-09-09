#!/usr/local/bin/python3

# turn on logging
import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


#test code
from IDCSClient import IDCSClient

idcsURL = "https://idcs-f29b958a146e4bdd9fef12a2e6a9ebcb.identity.oraclecloud.com"
clientID = "95b06d3627a045bfb9f8c9bd8efa1d68"
clientSecret = "1658b892-9d24-4f03-9af2-ded5d48496f4"

client = IDCSClient(idcsURL, clientID, clientSecret)

client.GetApps()
# client.GetAppsPost()
(id,secret) = client.CreateApp( "foo", ["http://www.example.com"])

print( "Client ID     : {}".format(id))
print( "Client secret : {}".format(secret))
