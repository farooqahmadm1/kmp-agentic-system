# 🤝 Contributing to KMP Agentic System

Thank you for your interest in contributing to the **KMP Agentic System**!

---

## 🛠️ Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/farooqahmadm1/kmp-agentic-system.git
   cd kmp-agentic-system
   ```

2. Install dependencies:
   ```bash
   make install
   ```

3. Run the automated test suite:
   ```bash
   make test
   ```

---

## 📚 Adding a New KMP Domain Skill

To add a new specialized domain skill:
1. Create a new folder under `skills/` (e.g., `skills/kmp-camera/`).
2. Add a `SKILL.md` with YAML frontmatter:
   ```markdown
   ---
   name: kmp-camera
   description: Best practices for CameraX (Android) and AVFoundation (iOS) in KMP.
   triggers:
     - "camera"
     - "photo"
     - "capture"
   ---

   # Camera Standards in KMP:
   1. Use expect/actual bridge for native camera capture session.
   2. Ensure Android CameraX LifecycleCameraController binds to LifecycleOwner.
   ```
3. Register the skill trigger in `skills/skill_registry.py`.

---

## 🧪 Submitting a Pull Request

1. Create a feature branch (`git checkout -b feat/my-new-feature`).
2. Ensure all unit tests pass (`make test`).
3. Commit your changes with descriptive messages following Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`).
4. Push to your branch and submit a Pull Request!
