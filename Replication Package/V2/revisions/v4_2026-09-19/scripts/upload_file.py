"""Complete one Notion-provided single-use upload using a local file."""
import json
import mimetypes
import sys
import urllib.request
import uuid
from pathlib import Path

spec=json.load(sys.stdin)
file=Path(sys.argv[1])
boundary='v4-'+uuid.uuid4().hex
mime=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{spec["filename"]}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+file.read_bytes()+f'\r\n--{boundary}--\r\n'.encode())
headers=dict(spec['upload_headers']);headers['Content-Type']='multipart/form-data; boundary='+boundary
request=urllib.request.Request(spec['upload_url'],data=body,headers=headers,method='POST')
with urllib.request.urlopen(request,timeout=60) as response:
    result=json.load(response)
print(json.dumps(result))
