import base64


ALTCHARS = b'-_'
def url_b64_encode(b: bytes) -> str:
    """
        Encode bytes into a b64 string that is friendly to urls

        This specifically replaces + and / with - and _
    """
    return base64.b64encode(b, altchars=ALTCHARS).decode()

def url_b64_decode(s: str) -> bytes:
    """
        Decode b64 string encoded with `url_b64_encode` into bytes 

        This specifically the encoder replaces + and / with - and _
    """
    return base64.b64decode(s, altchars=ALTCHARS)