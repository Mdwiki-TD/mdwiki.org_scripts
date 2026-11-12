import os

import requests

API_URL = "https://api.svc.tools.eqiad1.wikimedia.cloud:30003"

HOME_DIR = os.environ.get("TOOL_DATA_DIR", ".")

result = requests.post(
    f"{API_URL}/jobs/v1/tool/mdw/jobs/arsql/restart",
    cert=(f"{HOME_DIR}/.toolskube/client.crt", f"{HOME_DIR}/.toolskube/client.key"),
    verify=False,  # the cert is currently self-signed, internal to k8s as we use the internal endpoint
)

print("status_code: ", result.status_code)  # 400
print("json: ", result.json())  # {'error': ['Unable to restart a one-off job']}
