"""Repo templating — create repos from boilerplate."""

import os
from datetime import datetime
from .api import GitHubAPI
from .colors import C
from .ui import pick_repo
from .i18n import t

TEMPLATES = {
    "python-basic": {
        "files": {
            "README.md": "# {{PROJECT_NAME}}\n\n{{DESCRIPTION}}\n\n## Setup\n```bash\npip install -r requirements.txt\n```\n\n## Author\n{{AUTHOR}} — {{YEAR}}\n",
            "requirements.txt": "requests\n",
            ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\ndist/\n*.egg-info/\n",
            "main.py": '"""{{PROJECT_NAME}} — {{DESCRIPTION}}"""\n\n\ndef main():\n    print("Hello from {{PROJECT_NAME}}")\n\n\nif __name__ == "__main__":\n    main()\n',
            "LICENSE": "MIT License\n\nCopyright (c) {{YEAR}} {{AUTHOR}}\n",
        }
    },
    "esp32-arduino": {
        "files": {
            "README.md": "# {{PROJECT_NAME}}\n\n{{DESCRIPTION}}\n\n## Hardware\n- ESP32\n\n## Author\n{{AUTHOR}}\n",
            "platformio.ini": "[env:esp32]\nplatform = espressif32\nboard = esp32dev\nframework = arduino\nmonitor_speed = 115200\n",
            "src/main.cpp": '#include <Arduino.h>\n\nvoid setup() {\n    Serial.begin(115200);\n    Serial.println("{{PROJECT_NAME}} started");\n}\n\nvoid loop() {\n    delay(1000);\n}\n',
            ".gitignore": ".pio/\n.vscode/\n",
        }
    },
    "web-basic": {
        "files": {
            "README.md": "# {{PROJECT_NAME}}\n\n{{DESCRIPTION}}\n",
            "index.html": '<!DOCTYPE html>\n<html>\n<head><title>{{PROJECT_NAME}}</title><link rel="stylesheet" href="style.css"></head>\n<body>\n<h1>{{PROJECT_NAME}}</h1>\n<script src="app.js"></script>\n</body>\n</html>\n',
            "style.css": "* { margin: 0; padding: 0; box-sizing: border-box; }\nbody { font-family: sans-serif; }\n",
            "app.js": "// {{PROJECT_NAME}}\nconsole.log('Ready');\n",
            ".gitignore": "node_modules/\n.env\n",
        }
    },
    "node-express": {
        "files": {
            "README.md": "# {{PROJECT_NAME}}\n\n{{DESCRIPTION}}\n\n## Run\n```bash\nnpm install && npm start\n```\n",
            "package.json": '{\n  "name": "{{PROJECT_NAME}}",\n  "version": "1.0.0",\n  "main": "index.js",\n  "scripts": {"start": "node index.js"},\n  "dependencies": {"express": "^4.18.0"}\n}\n',
            "index.js": "const express = require('express');\nconst app = express();\napp.get('/', (req, res) => res.send('{{PROJECT_NAME}}'));\napp.listen(3000, () => console.log('Running on :3000'));\n",
            ".gitignore": "node_modules/\n.env\n",
        }
    },
}


def templates_menu(gh: GitHubAPI):
    while True:
        print(f"""
  {C.BOLD}{'=' * 50}{C.RESET}
  {C.BOLD}{C.CYAN}REPO TEMPLATES{C.RESET}
  {C.BOLD}{'=' * 50}{C.RESET}
""")
        for i, name in enumerate(TEMPLATES, 1):
            print(f"  {C.GREEN}{i}{C.RESET}  {name}")
        print(f"  {C.GREEN}0{C.RESET}  {t('back')}")
        choice = input(f"\n  {C.YELLOW}> Template: {C.RESET}").strip()
        if choice == "0": break
        names = list(TEMPLATES.keys())
        if choice.isdigit() and 1 <= int(choice) <= len(names):
            _create_from_template(gh, names[int(choice) - 1])
            input(f"\n  {C.DIM}{t('press_enter')}{C.RESET}")


def _create_from_template(gh, tpl_name):
    tpl = TEMPLATES[tpl_name]
    repo_name = pick_repo(gh)
    if not repo_name: return
    desc = input(f"  {C.YELLOW}> Description: {C.RESET}").strip()
    private = input(f"  {C.YELLOW}> Private? [Y/n]: {C.RESET}").strip().lower() != "n"

    vars_ = {
        "{{PROJECT_NAME}}": repo_name,
        "{{DESCRIPTION}}": desc or f"A {tpl_name} project",
        "{{AUTHOR}}": gh.username,
        "{{YEAR}}": str(datetime.now().year),
    }

    print(f"\n  {C.DIM}Creating repo '{repo_name}' from template '{tpl_name}'...{C.RESET}")
    result, status = gh.create_repo(repo_name, desc, private, init=True)
    if status != 201:
        print(f"  {C.RED}x Repo creation failed: {result.get('message','?')}{C.RESET}"); return

    import requests as req
    import base64
    import time
    time.sleep(1)  # wait for GitHub to initialize

    ok = 0
    for filepath, content in tpl["files"].items():
        for var, val in vars_.items():
            content = content.replace(var, val)
        encoded = base64.b64encode(content.encode()).decode()
        r = req.put(f"{gh.BASE_URL}/repos/{gh.username}/{repo_name}/contents/{filepath}",
                    headers=gh.headers,
                    json={"message": f"Add {filepath}", "content": encoded})
        if r.status_code in (200, 201):
            print(f"  {C.GREEN}+{C.RESET} {filepath}")
            ok += 1
        else:
            print(f"  {C.RED}x{C.RESET} {filepath} (failed)")

    print(f"\n  {C.GREEN}+ Created {repo_name} with {ok} files from {tpl_name}{C.RESET}")
    print(f"  {C.DIM}URL: https://github.com/{gh.username}/{repo_name}{C.RESET}")
