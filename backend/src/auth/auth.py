import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen

AUTH0_DOMAIN = 'samajeste-digho-fsnd.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'Coffee'

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header
'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    auth = request.headers.get('Authorization', None)
    # If the Authorization header is not available
    if auth is None:
        raise AuthError({
            'code': 'AUTHORIZATION_HEADER_ABSENT',
            'description': 'Authorization header is expected in the request. Check request header !'
        }, 401)

    # Split the header and collect the different parts (Bearer, token)
    entities = auth.split(' ')
    # Check if the Bearer keyword is present
    if entities[0].lower() != 'bearer':
        raise AuthError({
            'code': 'INVALID_HEADER',
            'description': 'Authorization must start with the key word <BEARER>'
        }, 401)
    # Check if token is also present
    if len(entities) == 1:
        raise AuthError({
            'code': 'MALFORMED_HEADER',
            'description': 'Authorization malformed !'
        }, 401)
    # If all is correct return the token
    return entities[1]


'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    # Check if the permissions are contained in the payload
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'NO_PERMISSIONS',
            'description': 'No permission available for this user.'
        }, 401)
    # Verify if the user have the permissions
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'PERMISSION_REFUSED',
            'description': 'Probably don\'t have the required permissions to access this ressource.'
        }, 401)
    # If permission present, return True
    return True


'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    # Put in place the token verification environment
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token=token)
    rsa_key = {}
    # Verify if the token header have a key id (kid)
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'INVALID_TOKEN_HEADER',
            'description': 'Token not conform'
        }, 401)
    # Collect important attributes from the token header
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    # If the RSA_KEY is set
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://'+AUTH0_DOMAIN+'/'
            )
            return payload
        except jwt.ExpiredSignatureError:
            # If the token has expired
            raise AuthError({
                'code': 'EXPIRED_TOKEN',
                'description': 'The token you are using is not more valid.'
            }, 401)
        except jwt.JWTClaimsError:
            # If there is claims error
            raise AuthError({
                'code': 'INVALID_TOKEN_CLAIMS',
                'description': 'Incorrect claims. Please check the audience'
            }, 401)
        except Exception:
            # If any other error is found
            raise AuthError({
                'code': 'INVALID_TOKEN_HEADER',
                'description': 'Unable to parse authentication token'
            }, 401)
    raise AuthError({
        'code': 'INVALID_TOKEN_HEADER',
        'description': 'Unable to find the appropriate key.'
    }, 401)


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
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
