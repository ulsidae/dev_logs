## 🔢 Strassen Algorithm (Reconstructed)

🍯 [Code](https://github.com/ulsidae/dev_logs/blob/main/Mathematics/Strassen%20Algorithm/Strassen.cpp)

---

<img src="https://github.com/ulsidae/dev_logs/blob/main/Mathematics/Strassen%20Algorithm/img/img2.png" height="400"/>

> Originally written as a high school research report and later translated into English.

---

## 💡 Summary

This repository contains a reconstructed implementation of the Strassen matrix multiplication algorithm,
originally developed as part of a high school research project on time efficiency.

The original implementation and materials were lost.
This version was reconstructed based on conceptual understanding and reference material.

---

## 🔢 Strassen Algorithm

Strassen’s algorithm improves matrix multiplication efficiency by recursively partitioning matrices into quadrants and reducing the number of multiplication operations from 8 to 7 at each step, which becomes increasingly beneficial as matrix size grows.

✅ ***Efficiency***

The algorithm has a theoretical time complexity of $O(n^{2.81})$

However, in practical implementations, it is not always faster due to overhead such as recursion, additional additions/subtractions, and memory operations.


✅ ***Core idea***

By assuming matrices of size $2^n \times 2^n$, the algorithm trades an increased number of additions and subtractions for a reduction in the most expensive operation: multiplication.


✅***Limitations***

When matrix dimensions do not match this form, the algorithm can be applied theoretically through zero padding, though this may further reduce practical efficiency.

---

## 🍯 Background

This project was implemented strictly for educational purposes, with a focus on understanding algorithmic principles.

In current practical or professional work, high-level numerical libraries are used instead.
This implementation exists solely to demonstrate conceptual understanding rather than practical performance.

---

## ✅ Notes

0. This implementation assumes matrices of size $2^n \times 2^n$
  
1. Performance optimizations (such as minimizing memory copies or cache-aware techniques) were intentionally omitted.

2. In real-world scenarios, this implementation may be slower than standard matrix multiplication.

---

## Why this repo exists

This repository exists as a record of learning.

Today, I rely on calculators and high-level numerical libraries.
Back then, I wanted to understand what happens underneath.

This code is not about performance.
It is about curiosity.



