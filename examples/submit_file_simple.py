""" Example file submission script

Requires the `aws` command line utility: http://aws.amazon.com/cli/
"""
import sys
sys.path.append("/usr/local/lib/python3.6/site-packages")
sys.path.append("/usr/local/lib/python3.6/site-packages/PIL")
import hashlib
import json
import os
import requests
import subprocess
import sys
import time

host = 'https://www.lungepigenome.org'
encoded_access_key = ''
encoded_secret_access_key = ''
#host = ''
#encoded_access_key = 'SXRSUEHQ'
#encoded_secret_access_key = 'ukmnc4w6d4hx2laq'

path = '/Users/parulkudtarkar/Downloads/DFF352TAW.bigWig'
my_lab = '/labs/kyle-gaulton/'
my_award = '/awards/LungMap/'

# From http://hgwdev.cse.ucsc.edu/~galt/encode3/validatePackage/validateEncode3-latest.tgz
encValData = '/Users/parulkudtarkar/Desktop/Encode/encoded/examples/encValData'
assembly = 'hg19'

# ~2s/GB
print("Calculating md5sum.")
md5sum = hashlib.md5()
with open(path, 'rb') as f:
    for chunk in iter(lambda: f.read(1024*1024), b''):
        md5sum.update(chunk)

data = {
    "dataset": "/annotations/LEBSR324EVV",
    "file_format": "bigWig",
    "assembly": "hg19",
    #"file_format_type": "bed3+",
    "file_size": os.path.getsize(path),
    "md5sum": md5sum.hexdigest(),
    "output_type": "signal",
    "submitted_file_name": path,
    "lab": my_lab,
    "award": my_award
}


####################
# POST metadata

headers = {
    'Content-type': 'application/json',
    'Accept': 'application/json',
}

print("Submitting metadata.")
r = requests.post(
    host + '/file',
    auth=(encoded_access_key, encoded_secret_access_key),
    data=json.dumps(data),
    headers=headers,
)
try:
    r.raise_for_status()
except:
    print('Submission failed: %s %s' % (r.status_code, r.reason))
    print(r.text)
    raise
item = r.json()['@graph'][0]
print(json.dumps(item, indent=4, sort_keys=True))


####################
# POST file to S3

creds = item['upload_credentials']
env = os.environ.copy()
env.update({
    'AWS_ACCESS_KEY_ID': creds['access_key'],
    'AWS_SECRET_ACCESS_KEY': creds['secret_key'],
    'AWS_SECURITY_TOKEN': creds['session_token'],
})

# ~10s/GB from Stanford - AWS Oregon
# ~12-15s/GB from AWS Ireland - AWS Oregon
print("Uploading file.")
start = time.time()
try:
    subprocess.check_call(['aws', 's3', 'cp', path, creds['upload_url']], env=env)
except subprocess.CalledProcessError as e:
    # The aws command returns a non-zero exit code on error.
    print("Upload failed with exit code %d" % e.returncode)
    sys.exit(e.returncode)
else:
    end = time.time()
    duration = end - start
    print("Uploaded in %.2f seconds" % duration)
