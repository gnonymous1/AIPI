# Security Policy 🛡️

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## Reporting a Vulnerability

We take the security and confidentiality of AIPI, user credentials, vault secrets, and private data very seriously.

If you discover a security vulnerability or sensitive information exposure:

1. **Do NOT open a public GitHub issue.**
2. Please send a detailed report via private message or email to our maintainers at `security@gnonymous.com` (or create a Private Security Advisory on GitHub).
3. Include:
   * Description of the vulnerability
   * Steps to reproduce the issue
   * Proof-of-concept (PoC) code if applicable
   * Impact assessment

---

## Security Architecture in AIPI

* **Vault Encryption**: All provider API keys and refresh tokens stored in AIPI are encrypted at rest using AES-256 with PBKDF2 HMAC-SHA256 key derivation.
* **PII & Secrets Redaction**: Real-time heuristic redactor automatically masks API tokens, passwords, credit card numbers, and emails before requests leave the local environment.
* **Air-Gapped Stealth Mode**: Blocks all external egress traffic when enterprise local compliance is required.
* **Never Commit Secrets**: Real credentials, `.env`, `*.db`, and `config.json` are excluded from version control via `.gitignore`.
