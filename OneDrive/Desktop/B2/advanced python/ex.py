import math
n = int(input("Enter a number: "))
for a in range (2, n):
    for b in range (2, n):
        if math.gcd(a, b) == 1:
            print(f"{a}/{b}")

