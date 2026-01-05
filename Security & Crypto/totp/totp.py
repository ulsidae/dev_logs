import base64, hmac, hashlib, struct, time

def totp(secret, interval=30, digits=6):

    key = base64.b32decode(secret, casefold=True)

    # timer
    counter = int(time.time() // interval)
    msg = struct.pack(">Q", counter)

    # HMAC-SHA1
    h = hmac.new(key, msg, hashlib.sha1).digest()

    # Dynamic truncation
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset:offset+4])[0] & 0x7fffffff

    return str(code % (10 ** digits)).zfill(digits)

if __name__ == "__main__":
    SECRET = "IAmnot4hiddenkey"
    # Base32-encoded shared secret (example value)
    print(f"OTP: {totp(SECRET)}")
