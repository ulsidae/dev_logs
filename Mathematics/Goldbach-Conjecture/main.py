import time


def is_prime(n, prime_list):
    """Efficiently check primality using existing prime list (O(sqrt(N)))"""
    if n < 2: return False
    limit = int(n ** 0.5)
    for p in prime_list:
        if p > limit: break
        if n % p == 0: return False
    return True


def goldbach_infinite_runner():
    """Verify Goldbach's Conjecture by increasing numbers indefinitely"""
    primes = [2, 3]  # Initial list of primes
    prime_set = {2, 3}
    current_even = 4
    last_num_checked = 3

    print("Press Ctrl+C to stop the process.\n")

    try:
        while True:
            # 0. Automatically expand the prime list as needed for the current even number
            while last_num_checked < current_even:
                last_num_checked += 1
                if is_prime(last_num_checked, primes):
                    primes.append(last_num_checked)
                    prime_set.add(last_num_checked)

            # 1. Find Goldbach partition (O(N) approach using set lookup)
            found = False
            for p in primes:
                if p > current_even / 2:
                    break
                target = current_even - p
                if target in prime_set:
                    print(f"[Success] {current_even:5} = {p:4} + {target:4}")
                    found = True
                    break

            if not found:
                print(f"{current_even}!")
                break

            current_even += 2  # Move to the next even number
            time.sleep(0.05)  # Slight delay for readability

    except KeyboardInterrupt:
        print("\n Pause")


# Execute the runner
if __name__ == "__main__":
    goldbach_infinite_runner()
