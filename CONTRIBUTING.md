# Contributing to AIPI 🚀

Thank you for your interest in contributing to **AIPI (AI Protocol Interface)**! We welcome contributions from developers, researchers, and AI enthusiasts worldwide.

Developed by **Ghulam Nabi Kalhoro** | Copyright © 2026 **gnonymous pvt ltd**.

---

## 🌟 How Can You Contribute?

You can contribute to AIPI in many ways:
* 💡 **Add New Providers & Models**: Integrate emerging LLM APIs (Mistral, Cohere, DeepSeek, xAI, Local LLM backends).
* ⚡ **Performance & Latency Optimization**: Optimize token streaming, caching algorithms, and HTTP connection reuse.
* 🛡️ **Security & Privacy Enhancements**: Expand PII redaction patterns, guardrails, and compliance audits.
* 🖥️ **UI/UX Improvements**: Enhance the web portal, playground arena, dark-mode animations, and live charts.
* 📝 **Documentation & Guides**: Write tutorials, translation guides, agent setups, and blog articles.
* 🐛 **Bug Reports & Feedback**: Report issues and test edge cases on diverse platforms.

---

## 🛠️ Development Setup

1. **Fork and Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/AIPI.git
   cd AIPI
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Verification Test Suite:**
   ```bash
   python test_suite.py
   ```
   Ensure all 18 test phases pass before creating your pull request.

---

## 🌿 Branching & Commit Conventions

* **Branch naming:**
  * `feature/your-feature-name`
  * `fix/issue-description`
  * `docs/improvement-details`
  * `perf/optimization-focus`

* **Commit messages:**
  * `feat: add provider adapter for Mistral AI`
  * `fix: resolve token parsing in streamGenerateContent`
  * `docs: update quickstart guide with Docker instructions`
  * `perf: reduce gateway routing latency with session reuse`

---

## 📬 Pull Request Process

1. Ensure code adheres to PEP 8 standards and maintains backward compatibility.
2. Never commit personal API keys, credentials, or `.env` / `config.json` files.
3. Run `python test_suite.py` to verify that all automated unit and integration tests pass 100%.
4. Submit your PR with a clear summary of changes, motivation, and testing steps.
5. Our maintainers will review and merge promptly!

---

## 💬 Community & Questions

Have an idea or question? Open a GitHub Discussion or submit an issue to start a conversation with Ghulam Nabi Kalhoro and the maintainer team.
