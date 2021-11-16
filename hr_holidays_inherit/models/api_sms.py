# -*- coding: utf-8 -*-

import requests

def send(message, to):
	if message and to:
		payload='accountid=AIBD&password=5y3rJPwkU69P&text='+message+'&sender=AIBD&to='+to+'&ret_url=https%3A%2F%2Fvotre-entreprise.com%2Freception'
		url = "https://lampush-tls.lafricamobile.com/api"
		headers = {
  		'Content-Type': 'application/x-www-form-urlencoded'
		}
		response = requests.request("POST", url, headers=headers, data=payload)
	return
