# 🔒 Time-based One-Time Password (RFC 6238)

> **A minimal, reference-style implementation of TOTP (RFC 6238).**

This log documents the implementation of the Time-based One-Time Password (TOTP) algorithm, the global standard for 2FA (Two-Factor Authentication).

---
🍯 [Example](https://github.com/ulsidae/dev_logs/blob/main/Security%20%26%20Crypto/totp/totp.py)
---

### ⚙️ Technical Specifications
GitHub and most 2FA systems rely on these exact parameters defined in **RFC 6238**:

| Parameter | Specification |
| :--- | :--- |
| **Algorithm** | TOTP (RFC 6238) |
| **Hash Function** | HMAC-SHA1 |
| **Time Step** | 30 Seconds |
| **Digits** | 6-digit output |
| **Reference Time** | UTC |
| **Technical Specifications** | Base32 Encoding |

> **Why Base32?**
>
>  It skips confusing characters like 0, 1, O, and I, so it’s easier to read and less likely to cause typos when typed manually.

---

### 📜 What is RFC 6238?
RFC 6238 is the official "blueprint" for TOTP. 
* **RFC (Request for Comments):** A series of documents defining international Internet standards.
* **Core Logic:** It precisely defines how to turn a shared secret and a time-counter into a temporary, 6-digit code.

**Key Constraints:**
* Built upon **HOTP (RFC 4226)**: TOTP is basically HOTP, but instead of an event-based counter, it uses a time-based counter.
```bash
  In short: TOTP = HOTP ( 𝐾 , 𝑇 ) where 𝑇 is the number of time steps since the epoch.
```
* **HMAC** as Primitive: Uses HMAC as the cryptographic building block.
* **Threat Model**: Assumes the attacker knows 100% of the algorithm; security depends entirely on keeping the Secret Key secret.

---

### ⚠️ The SHA-1 Misconception
"A lot of developers call SHA-1 'broken'." While true in certain contexts, it's crucial to distinguish between **Raw SHA-1** and **HMAC-SHA1**.

#### ❌ Why Raw SHA-1 is retired:
* Vulnerable to **Collision Attacks** (finding two different inputs with the same hash).
* Unsafe for Digital Signatures, Certificates, and File Integrity.

#### ✅ Why HMAC-SHA1 remains secure for TOTP:
TOTP operates on the formula: $$HMAC(secret, message)$$
1. **Secret is Key:** Without the shared secret, an attacker cannot manipulate the input to trigger a collision.
2. **Fixed Message:** The message is a 64-bit time counter, not a user-controlled arbitrary string.
3. **Current Standard:** Cryptographically, SHA-1 collision vulnerabilities do not translate to HMAC breaks. Both **NIST** and **RFC 6238** continue to authorize HMAC-SHA1 for this specific use case.

---

# 🍯 Comment

<img src="https://docs.github.com/assets/cb-23826/mw-1440/images/help/2fa/ghes-3.8-and-higher-2fa-wizard-app-click-code.webp" height="400"/>

> [!WARNING]
> Make sure to **Keep your setup key secure.**
> * This value is the **shared secret** used by TOTP authenticators.

*Image source & Reference:
[GitHub 2FA Documentation](https://docs.github.com/en/authentication/securing-your-account-with-two-factor-authentication-2fa/configuring-two-factor-authentication)

---

### 💡 Summary
* TOTP security depends entirely on **Secret Key Protection**.
* Algorithm transparency is a feature, not a bug.
* This is a deliberate, **conservative cryptographic choice** that remains robust in modern security environments.
