"""brand asset pipeline - seal_logo.py (auditor copy).

The brand key is injected at seal time and is not part of this copy.
"""
from Crypto.Cipher import AES

HEADER = 54  # BMP file header + DIB header, left intact for thumbnailers

def seal(path_in, path_out, brand_key):
    raw = open(path_in, "rb").read()
    header, pixels = raw[:HEADER], raw[HEADER:]
    assert len(pixels) % 16 == 0, "logo pixel data is block-aligned by design"
    enc = AES.new(brand_key, AES.MODE_ECB).encrypt(pixels)
    open(path_out, "wb").write(header + enc)
    print("sealed:", path_out)
