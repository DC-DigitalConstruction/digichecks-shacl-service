from fastapi.param_functions import Form


class CustomOAuth2PasswordRequestForm:

    def __init__(
        self,
        client_id: str = Form(...),
        client_secret: str = Form(...),
        grant_type: str = Form(None, regex="password"),
        scope: str = Form(""),
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.grant_type = grant_type
        self.scopes = scope.split()
