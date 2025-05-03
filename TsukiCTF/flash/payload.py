import hmac, hashlib

# Подставь из файла
with open('./static/seed.txt', 'r') as f:
    SEED = bytes.fromhex(f.read().strip())

session_id = input("Введи session_id из куки: ").strip()

TOTAL_ROUNDS = 10
DIGITS_PER_ROUND = 7

def lcg_params(seed: bytes, session_id: str):
    m = 2147483693
    raw_a = hmac.new(seed, (session_id + "a").encode(), hashlib.sha256).digest()
    a = (int.from_bytes(raw_a[:8], 'big') % (m - 1)) + 1
    raw_c = hmac.new(seed, (session_id + "c").encode(), hashlib.sha256).digest()
    c = (int.from_bytes(raw_c[:8], 'big') % (m - 1)) + 1
    return m, a, c

def generate_round_digits(seed: bytes, session_id: str, round_index: int):
    LCG_M, LCG_A, LCG_C = lcg_params(seed, session_id)
    h0 = hmac.new(seed, session_id.encode(), hashlib.sha256).digest()
    state = int.from_bytes(h0, 'big') % LCG_M

    for _ in range(DIGITS_PER_ROUND * round_index):
        state = (LCG_A * state + LCG_C) % LCG_M

    digits = []
    for _ in range(DIGITS_PER_ROUND):
        state = (LCG_A * state + LCG_C) % LCG_M
        digits.append(state % 10)

    return digits

# Генерация всех чисел
total = 0
print("\nЧисла по раундам:")
for i in range(TOTAL_ROUNDS):
    digits = generate_round_digits(SEED, session_id, i)
    number = int(''.join(map(str, digits)))
    print(f"Раунд {i+1}: {digits} → {number}")
    total += number

print(f"\nИТОГОВАЯ СУММА: {total}")

