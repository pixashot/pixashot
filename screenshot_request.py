from pydantic import BaseModel, HttpUrl

class ScreenshotRequest(BaseModel):
    url: HttpUrl
    windowWidth: int = 1280
    windowHeight: int = 720