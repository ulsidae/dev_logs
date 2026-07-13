## 🔢 Goldbach's conjecture

🌐 [Related video](https://www.youtube.com/watch?app=desktop&v=VBBFYJ-HbKw)

---

## 🍯 Introduction

Back in high school, I attempted a simple experiment to explore Goldbach's conjecture.

Below is the code I wrote at the time:

```python
# 소수 찾기 함수
def find_Prime(count):
    pfL = []  # prime factor list
    startNum = 2  # 시작하는 수
    while len(pfL) < count:
        if all(startNum % prime != 0 for prime in pfL):
            pfL.append(startNum)
        startNum += 1  # startNum에 1을 더하기
    return pfL  # 계속 진행

# 소수 쌍 매칭 함수
def match_Prime(even, prime_List):
    primeSet = set(prime_List)
    for i in range(len(prime_List)):
        for j in range(i, len(prime_List)):
            if prime_List[i] + prime_List[j] == even:
                return prime_List[i], prime_List[j]
    return None

# 소수 쌍 출력 함수
def print_Value(even, prime_List):
    matchV = match_Prime(even, prime_List)
    if matchV:
        print(f"{even} = {matchV[0]} + {matchV[1]}")
    else:
        print(f"{even} => 성립 X")

# 예제 실행
even = 100  # n = x + y에서 앞의 마지막 n이 될 짝수
prime_List = find_Prime(20)  # 소수 리스트 (count 개수)

# 2부터 even까지 반복
for startNum in range(2, even + 1, 2):  # even까지 반복, 2씩 증가
    if startNum in prime_List:
        print(f"{startNum} = {startNum}/2면 pass 아니면 확인!")
    else:
        print_Value(startNum, prime_List)
```

Because the prime list was limited, even small changes in the range produced very different results.
Also, the nested loops resulted in $O(n^2)$ complexity.

Ultimately, this approach revealed little about the underlying nature of prime numbers, but it taught me a great deal about algorithms, computational limits, and mathematical experimentation.

---

## 🔢 Prime Visualization

To gain a better intuition, I decided to try a simple visual experiment:

> Whenever a prime number is encountered, turn 90° to the left.

🍯 [code](https://github.com/ulsidae/dev_logs/blob/main/Mathematics/Goldbach-Conjecture/line.py)

<img src="https://github.com/ulsidae/dev_logs/blob/main/Mathematics/Goldbach-Conjecture/Capture.PNG" height="400"/>

I created a simple turtle graphics visualization of prime numbers.
The visualization suggested that primes appear unpredictable, yet patterns emerge amid the chaos.

---

## 🍯 Paradoxically...

This visualization gave me a sense of why Goldbach's conjecture feels plausible.

Of course, intuition is not a mathematical proof.

---

## 🔢 Improved Code

The high school implementation was later improved using a Sieve of Eratosthenes for better efficiency.

🍯 [code](https://github.com/ulsidae/dev_logs/blob/main/Mathematics/Goldbach-Conjecture/main.py)

It can now handle much larger ranges automatically.

---

## 🔢 Conclusion

> No matter how many finite cases we verify, we cannot establish Goldbach's conjecture for all even numbers through computation alone.

Thus, this code has practical meaning only for supercomputers and remains highly inefficient.

While largely theoretical, this approach was a great exercise in applying Python and practicing algorithmic thinking.

Still, I’m sharing it here for anyone interested in this thought experiment.
