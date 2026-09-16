import bcrypt
print(bcrypt.hashpw(b"pass123", bcrypt.gensalt()).decode())