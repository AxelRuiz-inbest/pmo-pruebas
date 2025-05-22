import requests

organizacion= "Inbest"
proyecto="DevOps Hub"
workitem_id="14187"
token_pat="aVVQb5k9hWmUr12AZl8g6XV9rtsnKGKBihU9tBEM8alymuJJiLB0JQQJ99BEACAAAAAbRvkPAAASAZDO1VMj"

url= f"https://dev.azure.com/{tu-organizacion}/{tu-proyecto}/_apis/wit/workitems/{id}?api-version=7.0"

headers = {
    "Content-Type": "application/json-patch+json"
    "Authorization": f"Basic {requests.auth._basic_auth_str('',token_pat)}"
}

payload = [
  {
    "op": "add"
    "path": "fields/Custom.HorasRegistrada"
    "value": 5
  }
]
Content-Type: application/json-patch+json

[
  {
    "op": "add",
    "path": "/fields/Custom.HorasRegistradas",
    "value": 5
  }
]

response = requests.patch(url, json=padload, headers=headers)

if response.status_code = 200:
  print ("Item actualizado")
  print (response.json())
else:
  print(f"Error en {status_code}: {response.text}")
