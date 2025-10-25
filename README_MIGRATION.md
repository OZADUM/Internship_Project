cd ~/Projects/Internship_Project

cat > README_MIGRATION.md <<'EOF'
# Migration & Dev Setup (Internship_Project)

This doc captures everything needed to run the project on a new Mac after migration.

---

## 1) Overview

- **Repo**: Internship_Project  
- **Goal**: Be able to run Behave tests locally (Reelly flows + utilities)  
- **Interpreter**: Python **3.14** (Homebrew)  
- **Venv**: Project-local `venv/`  
- **Browser**: Chrome (driver handled by `webdriver-manager`)  

---

## 2) Prerequisites (macOS)

1. **Homebrew**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
   eval "$(/opt/homebrew/bin/brew shellenv)"
