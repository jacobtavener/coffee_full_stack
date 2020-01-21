import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'coffee-dev.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee_api'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

def get_token_auth_header():
    if "Authorization" not in request.headers:
        raise AuthError({
        'success':False,
        'message':'no JWT provided',
        'error':401   
        }, 401)
    auth = request.headers.get('Authorization')
    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
        'success':False,
        'message':'Authorization must start with "Bearer"',
        'error':401
    }, 401)
    if len(parts)==1:
        raise AuthError({
        'success':False,
        'message':'Invalid header, must contain a token',
        'error':401
    },401)
    if len(parts)>2:
        raise AuthError({
        'success':False,
        'message':'Invalid header, must contain bearer and token only',
        'error':401
    },401)

    token = parts[1]
    return token


def check_permissions(permission, payload):
    if  'permissions' not in payload:
        raise AuthError({
        'success': False,
        'message':'permissions not included in the jwt',
        'error':401
        },401)
    if permission not in payload["permissions"]:
        raise AuthError({
        'success':False,
        'message':'not permitted to use this feature',
        'error':401
    },401)
    
    return True

def verify_decode_jwt(token):
    #get json web key sets for the tenant in Auth0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    #get the data from in the header
    unverified_header = jwt.get_unverified_header(token)

    #checking Auth0 token contains key id
    if 'kid' not in unverified_header:

        raise AuthError({
        'success':False,
        'message':'key id not found in token',
        'error':401
    },401)

    #set up key
    rsa_key={}
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    #verify the key
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 401)

def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator