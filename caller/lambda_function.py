import gevent
from gevent import monkey, pool
monkey.patch_all()

import json
import os
import boto3

jobs = []
res_array = []

def do_req(payload, region):

    client = boto3.client('lambda',region_name=region)

    response = client.invoke(
        FunctionName='platcurl',
        InvocationType='RequestResponse',
        LogType='None',
        Payload=json.dumps(payload)
    )
    
    res_obj = json.loads(response['Payload'].read().decode('utf-8'))
    
    res_array.append(res_obj)


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        # expected in body:
        # 'url' = string: the url to curl
        # 'headers' = dict: the headers to include in the request
        # 'regions' = array: list of regions to run the function in
        
        if 'headers' in body:
            if not type(body['headers']) is dict:
                raise ValueError('"headers" key is not in dictionary format.')

    except json.decoder.JSONDecodeError:
        return {
            'statusCode': 422,
            'body': json.dumps({'result':'Fail','response':'Input error: request body not in expected JSON format.'})
        }
    except ValueError as ve:
        print(ve)
        return {
            'statusCode': 422,
            'body': json.dumps({'result':'Fail','response':'Input error: headers key passed, but not in dictionary format.'})
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 400,
            'body': json.dumps({'result':'Fail','response':'Unexpected error: An unknown error has occurred while reading input body.'})
        }

    p = pool.Pool(17)

    main_regions_list = os.environ['regions'].split(',')

    if 'regions' in body and type(body['regions']) is list:
        # sanitize input to only include regions from the body input that actually exist irl
        regions = []
        regions_input = body['regions']
        for region in regions_input:
            if region in main_regions_list:
                regions.append(region)
    else:
        # if no regions are specified in a list/array, make it ALL regions from the envvar
        regions = main_regions_list
    
    # last check to see if the url was included in the request body
    if not 'url' in body:
        return {
            'statusCode': 422,
            'body': json.dumps({'result':'Fail','response':'Input Error: No url parameter passed.'})
        }

    if len(regions) == 0:
        return {
            'statusCode': 422,
            'body': json.dumps({'result':'Fail','response':'No valid regions were found in the input body.'})
        }

    try:
        url = body['url']
        
        print(f'requesting {url} from the following regions: {regions}') 
        
        jobs.clear()
        res_array.clear()
        
        for region in regions:
            jobs.append(p.spawn(do_req, body, region))
        gevent.joinall(jobs)
        
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'result':'Fail','response':'A server-side error has occurred.'})
        }

    res_json = {
        'url': url,
        'data': res_array
    }
    
    return {
        'statusCode': 200,
        'body': json.dumps(res_json)
    }
