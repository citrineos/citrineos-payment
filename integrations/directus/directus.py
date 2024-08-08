from io import BytesIO
import threading
import requests

from config import Config
from logging import exception, warning
from integrations.integration import FileIntegration

REFRESH_TOKEN_REQUEST_BUFFER = 500  # in milliseconds


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, access_token):
        self.access_token = access_token

    def __call__(self, request):
        request.headers["Authorization"] = f"Bearer {self.access_token}"
        return request


class DirectusIntegration(FileIntegration):
    def __init__(
        self,
        url: str,
        email: str = None,
        password: str = None,
        static_token: str = None,
    ):
        self.url: str = url
        self.email: str = email
        self.password: str = password
        self.static_token: str = static_token
        self.login()

    def login(self):
        if self.static_token:
            self._token = self.static_token
            return

        try:
            endpoint = "auth/login"
            payload = {"email": self.email, "password": self.password}
            request_url = f"{self.url}/{endpoint}"

            response = requests.post(request_url, json=payload)

            response_payload = response.json().get("data")
            self._token = response_payload["access_token"]
            self.refresh_token = response_payload["refresh_token"]
            expires = (
                response_payload["expires"] - REFRESH_TOKEN_REQUEST_BUFFER
            )  # in milliseconds
            timer = threading.Timer(expires / 1000, self.refresh_auth)
            timer.start()
        except Exception as e:
            exception(
                " [CitrineOS - Directus] Processing error for Directus login: %r",
                e.__str__,
            )
            raise e

    def refresh_auth(self):
        try:
            endpoint = "auth/refresh"
            payload = {"refresh_token": self.refresh_token, "mode": "json"}

            request_url = f"{self.url}/{endpoint}"
            response = requests.post(request_url, json=payload)
            response_payload = response.json().get("data")

            self._token = response_payload["access_token"]
            self.refresh_token = response_payload["refresh_token"]
            expires = (
                response_payload["expires"] - REFRESH_TOKEN_REQUEST_BUFFER
            )  # in milliseconds
            timer = threading.Timer(expires / 1000, self.refresh_auth)
            timer.start()
        except Exception as e:
            warning(
                " [CitrineOS - Directus] Error for Directus refresh auth: %r", e.__str__
            )
            warning(" [CitrineOS - Directus] Attempting to relogin.")
            self.login()

    """
    Uploads a file to Directus.
    
    Parameters:
        self: DirectusIntegration - The DirectusIntegration instance.
        file: BytesIO - The file to upload.
        mime_type: str - The MIME type of the file.
        filename: str - The name of the file.
        filetitle: str - The title of the file.
    
    Returns:
        str - A url to the uploaded file. Custom access permissions for the QR folder will make it public.
    """

    def upload_file(
        self, file: BytesIO, mime_type: str, filename: str, filetitle: str
    ) -> str:
        data = {
            "filename_disk": filename,
            "filename_download": filename,
            "title": filetitle,
            "type": mime_type,
            "folder": Config.CITRINEOS_DIRECTUS_QR_CODE_FOLDER,
        }
        files = {"file": (filename, file, mime_type)}
        request_url = f"{self.url}/files"
        response = requests.post(
            request_url, data=data, files=files, auth=BearerAuth(self._token)
        )
        response_payload = response.json().get("data")
        return f"{self.url}/assets/{response_payload['id']}"  # Query params could be added for image transformations, such as width/height
