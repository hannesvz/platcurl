import requests
import json
import os

def lambda_handler(event, context):
    res = None
    res_obj = None
    response = None
    if 'headers' in event:
        req_headers = event['headers']
    else:
        req_headers = {}

    try:
        res = requests.get(event['url'], headers=req_headers, verify=False, allow_redirects=False)
        res_obj = {
            'status_code': res.status_code,
            'response_reason': res.reason,
            'headers': dict(res.headers),
            'elapsed': res.elapsed.total_seconds()
        }
        # only include response body if it is text
        if res.encoding and res.encoding.lower() in ['utf-8','iso-8859-1','ascii']:
            res_obj['body'] = res.text
        else:
            res_obj['body'] = 'binary'
            
        response = {'result': 'OK', 'region': os.environ['AWS_DEFAULT_REGION'], 'response': res_obj}
    
    # this will never trigger if verify=False is set
    except requests.exceptions.SSLError:
        response = {'result': 'SSLError', 'response': 'Connection failed due to expired host certificate.'}
    
    except requests.exceptions.ConnectionError as e:
        response = {'result': 'ConnectionError', 'region': os.environ['AWS_DEFAULT_REGION'], 'response': 'Connection failed:' + str(e)}
    
    except Exception as e:
        print(e)
        response = {'result': 'Fail', 'region': os.environ['AWS_DEFAULT_REGION'], 'response': e}

    return response
