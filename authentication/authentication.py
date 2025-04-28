# authentication/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication

class JWTAuthentication(BaseJWTAuthentication):
    # Add any custom behavior if needed; otherwise, simply pass.
    pass

def default_user_authentication_rule(user):
    # Example rule: allow all users (customize as needed)
    return True