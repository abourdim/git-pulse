#!/bin/bash
#═══════════════════════════════════════════════════════════════
#  GitPulse - Super Installer & Launcher
#  Platforms: macOS (Homebrew)
#             MSYS2 (UCRT64/MINGW64/CLANG64/MSYS)
#             Git Bash (Git for Windows)
#             Linux (Debian/Ubuntu, Fedora/RHEL, Arch)
#═══════════════════════════════════════════════════════════════

set -e

# ─── Constants ────────────────────────────────────────────────
APP_NAME="GitPulse"
APP_DIR="$HOME/.gitpulse"
APP_SCRIPT="$APP_DIR/gitpulse.py"
CONFIG_FILE="$APP_DIR/config.json"
LOG_FILE="$APP_DIR/install.log"
VERSION="6.0"

# ─── Colors (safe for all terminals) ─────────────────────────
setup_colors() {
    if [[ -t 1 ]] && command -v tput &>/dev/null && [[ $(tput colors 2>/dev/null || echo 0) -ge 8 ]]; then
        RED='\033[0;91m'
        GREEN='\033[0;92m'
        YELLOW='\033[0;93m'
        BLUE='\033[0;94m'
        CYAN='\033[0;96m'
        BOLD='\033[1m'
        DIM='\033[2m'
        RESET='\033[0m'
    else
        RED='' GREEN='' YELLOW='' BLUE='' CYAN='' BOLD='' DIM='' RESET=''
    fi
}

# ─── Logging ──────────────────────────────────────────────────
info()    { echo -e "  ${CYAN}i${RESET}  $1"; }
success() { echo -e "  ${GREEN}+${RESET}  $1"; }
warn()    { echo -e "  ${YELLOW}!${RESET}  $1"; }
fail()    { echo -e "  ${RED}x${RESET}  $1"; }
header()  { echo -e "\n  ${BOLD}${CYAN}$1${RESET}\n"; }
sep()     { printf "  ${DIM}"; printf -- '-%.0s' $(seq 1 50); printf "${RESET}\n"; }

pause_key() {
    echo ""
    read -n 1 -s -r -p "  Press any key to continue..."
    echo ""
}

# ─── Platform Detection ──────────────────────────────────────
detect_platform() {
    PLATFORM="unknown"
    PKG_MGR="none"
    PYTHON_CMD=""
    PIP_CMD=""
    PYTHON_PKG=""
    PIP_PKG=""
    REQUESTS_PKG=""
    GIT_PKG="git"
    SUDO_CMD=""
    CAN_INSTALL=true

    local uname_s
    uname_s="$(uname -s)"

    # ── MSYS2 environments ────────────────────────────────────
    if [[ -n "${MSYSTEM:-}" ]]; then
        PKG_MGR="pacman"

        case "$MSYSTEM" in
            UCRT64)
                PLATFORM="msys2-ucrt64"
                PYTHON_PKG="mingw-w64-ucrt-x86_64-python"
                PIP_PKG="mingw-w64-ucrt-x86_64-python-pip"
                REQUESTS_PKG="mingw-w64-ucrt-x86_64-python-requests"
                ;;
            MINGW64)
                PLATFORM="msys2-mingw64"
                PYTHON_PKG="mingw-w64-x86_64-python"
                PIP_PKG="mingw-w64-x86_64-python-pip"
                REQUESTS_PKG="mingw-w64-x86_64-python-requests"
                ;;
            MINGW32)
                PLATFORM="msys2-mingw32"
                PYTHON_PKG="mingw-w64-i686-python"
                PIP_PKG="mingw-w64-i686-python-pip"
                REQUESTS_PKG="mingw-w64-i686-python-requests"
                ;;
            CLANG64)
                PLATFORM="msys2-clang64"
                PYTHON_PKG="mingw-w64-clang-x86_64-python"
                PIP_PKG="mingw-w64-clang-x86_64-python-pip"
                REQUESTS_PKG="mingw-w64-clang-x86_64-python-requests"
                ;;
            CLANGARM64)
                PLATFORM="msys2-clangarm64"
                PYTHON_PKG="mingw-w64-clang-aarch64-python"
                PIP_PKG="mingw-w64-clang-aarch64-python-pip"
                REQUESTS_PKG="mingw-w64-clang-aarch64-python-requests"
                ;;
            MSYS)
                PLATFORM="msys2-msys"
                PYTHON_PKG="python"
                PIP_PKG="python-pip"
                REQUESTS_PKG=""
                ;;
            *)
                PLATFORM="msys2-$MSYSTEM"
                PKG_MGR="none"
                CAN_INSTALL=false
                ;;
        esac

    # ── Git Bash (Git for Windows without MSYS2) ──────────────
    elif [[ "$uname_s" == MINGW* || "$uname_s" == MSYS_NT* ]]; then
        PLATFORM="gitbash"
        PKG_MGR="none"
        CAN_INSTALL=false

    # ── macOS ──────────────────────────────────────────────────
    elif [[ "$uname_s" == "Darwin" ]]; then
        PLATFORM="macos"
        if command -v brew &>/dev/null; then
            PKG_MGR="brew"
            PYTHON_PKG="python@3"
            PIP_PKG=""
            REQUESTS_PKG=""
            GIT_PKG="git"
        else
            PKG_MGR="none"
            CAN_INSTALL=false
        fi

    # ── Linux ─────────────────────────────────────────────────
    elif [[ "$uname_s" == "Linux" ]]; then
        if command -v apt-get &>/dev/null; then
            PLATFORM="linux-debian"
            PKG_MGR="apt"
            SUDO_CMD="sudo"
            PYTHON_PKG="python3"
            PIP_PKG="python3-pip"
            REQUESTS_PKG="python3-requests"
        elif command -v dnf &>/dev/null; then
            PLATFORM="linux-fedora"
            PKG_MGR="dnf"
            SUDO_CMD="sudo"
            PYTHON_PKG="python3"
            PIP_PKG="python3-pip"
            REQUESTS_PKG="python3-requests"
        elif command -v yum &>/dev/null; then
            PLATFORM="linux-rhel"
            PKG_MGR="yum"
            SUDO_CMD="sudo"
            PYTHON_PKG="python3"
            PIP_PKG="python3-pip"
            REQUESTS_PKG="python3-requests"
        elif command -v pacman &>/dev/null; then
            PLATFORM="linux-arch"
            PKG_MGR="pacman"
            SUDO_CMD="sudo"
            PYTHON_PKG="python"
            PIP_PKG="python-pip"
            REQUESTS_PKG="python-requests"
        elif command -v zypper &>/dev/null; then
            PLATFORM="linux-suse"
            PKG_MGR="zypper"
            SUDO_CMD="sudo"
            PYTHON_PKG="python3"
            PIP_PKG="python3-pip"
            REQUESTS_PKG="python3-requests"
        elif command -v apk &>/dev/null; then
            PLATFORM="linux-alpine"
            PKG_MGR="apk"
            SUDO_CMD="sudo"
            PYTHON_PKG="python3"
            PIP_PKG="py3-pip"
            REQUESTS_PKG="py3-requests"
        else
            PLATFORM="linux-unknown"
            PKG_MGR="none"
            CAN_INSTALL=false
        fi
    else
        PLATFORM="$uname_s"
        CAN_INSTALL=false
    fi

    # ── Detect Python command ─────────────────────────────────
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
    fi

    # ── Detect pip command ────────────────────────────────────
    if command -v pip3 &>/dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &>/dev/null; then
        PIP_CMD="pip"
    fi
}

# ─── Utility Functions ────────────────────────────────────────

cmd_exists() {
    command -v "$1" &>/dev/null
}

python_module_exists() {
    [[ -n "$PYTHON_CMD" ]] && $PYTHON_CMD -c "import $1" 2>/dev/null
}

get_python_ver() {
    [[ -n "$PYTHON_CMD" ]] && $PYTHON_CMD --version 2>/dev/null | awk '{print $2}' || echo "N/A"
}

get_git_ver() {
    cmd_exists git && git --version 2>/dev/null | awk '{print $3}' || echo "N/A"
}

get_pip_ver() {
    [[ -n "$PIP_CMD" ]] && $PIP_CMD --version 2>/dev/null | awk '{print $2}' || echo "N/A"
}

cls() {
    if cmd_exists clear; then
        clear
    elif cmd_exists cls; then
        cls
    else
        printf "\033c"
    fi
}

# Cross-platform sed in-place (GNU vs BSD)
sed_inplace() {
    local expr="$1"
    local file="$2"
    if sed --version &>/dev/null 2>&1; then
        sed -i "$expr" "$file"
    else
        sed -i '' "$expr" "$file"
    fi
}

# ─── Package Install Abstraction ─────────────────────────────

pkg_update() {
    case "$PKG_MGR" in
        pacman)  $SUDO_CMD pacman -Sy --noconfirm >> "$LOG_FILE" 2>&1 ;;
        apt)     $SUDO_CMD apt-get update -y >> "$LOG_FILE" 2>&1 ;;
        dnf)     $SUDO_CMD dnf check-update >> "$LOG_FILE" 2>&1 || true ;;
        yum)     $SUDO_CMD yum check-update >> "$LOG_FILE" 2>&1 || true ;;
        zypper)  $SUDO_CMD zypper refresh >> "$LOG_FILE" 2>&1 ;;
        apk)     $SUDO_CMD apk update >> "$LOG_FILE" 2>&1 ;;
        brew)    brew update >> "$LOG_FILE" 2>&1 ;;
        *)       return 1 ;;
    esac
}

pkg_install() {
    local pkg="$1"
    [[ -z "$pkg" ]] && return 1

    case "$PKG_MGR" in
        pacman)  $SUDO_CMD pacman -S --noconfirm --needed "$pkg" >> "$LOG_FILE" 2>&1 ;;
        apt)     $SUDO_CMD apt-get install -y "$pkg" >> "$LOG_FILE" 2>&1 ;;
        dnf)     $SUDO_CMD dnf install -y "$pkg" >> "$LOG_FILE" 2>&1 ;;
        yum)     $SUDO_CMD yum install -y "$pkg" >> "$LOG_FILE" 2>&1 ;;
        zypper)  $SUDO_CMD zypper install -y "$pkg" >> "$LOG_FILE" 2>&1 ;;
        apk)     $SUDO_CMD apk add "$pkg" >> "$LOG_FILE" 2>&1 ;;
        brew)    brew install "$pkg" >> "$LOG_FILE" 2>&1 ;;
        *)       return 1 ;;
    esac
}

pip_install() {
    local mod="$1"
    if [[ -n "$PIP_CMD" ]]; then
        $PIP_CMD install $mod --break-system-packages >> "$LOG_FILE" 2>&1 \
            || $PIP_CMD install $mod >> "$LOG_FILE" 2>&1
    else
        return 1
    fi
}

# ─── 1. Check Installation ───────────────────────────────────

action_check() {
    header ":: System Check"

    echo -e "  ${BOLD}Platform:${RESET}       $PLATFORM"
    echo -e "  ${BOLD}Pkg Manager:${RESET}    $PKG_MGR"
    echo -e "  ${BOLD}Can install:${RESET}    $CAN_INSTALL"
    echo -e "  ${BOLD}App directory:${RESET}  $APP_DIR"
    echo ""
    sep

    local all_ok=true

    if [[ -n "$PYTHON_CMD" ]]; then
        success "Python:      $(get_python_ver)  ($PYTHON_CMD)"
    else
        fail "Python:      NOT FOUND"
        all_ok=false
    fi

    if [[ -n "$PIP_CMD" ]]; then
        success "pip:         $(get_pip_ver)  ($PIP_CMD)"
    else
        fail "pip:         NOT FOUND"
        all_ok=false
    fi

    if cmd_exists git; then
        success "Git:         $(get_git_ver)"
    else
        fail "Git:         NOT FOUND"
        all_ok=false
    fi

    if cmd_exists curl; then
        success "curl:        $(curl --version 2>/dev/null | head -1 | awk '{print $2}')"
    else
        warn "curl:        NOT FOUND (optional)"
    fi

    sep

    if python_module_exists requests; then
        local rver
        rver=$($PYTHON_CMD -c "import requests; print(requests.__version__)" 2>/dev/null)
        success "requests:    $rver"
    else
        fail "requests:    NOT INSTALLED"
        all_ok=false
    fi

    sep

    if [[ -f "$APP_SCRIPT" ]]; then
        success "App script:  installed"
    else
        fail "App script:  NOT FOUND"
        all_ok=false
    fi

    if [[ -f "$CONFIG_FILE" ]]; then
        if [[ -n "$PYTHON_CMD" ]]; then
            local token_status
            token_status=$($PYTHON_CMD -c "
import json
try:
    c = json.load(open('$CONFIG_FILE'))
    t = c.get('token', '')
    print('set (****' + t[-4:] + ')' if len(t) > 4 else 'empty')
except:
    print('error')
" 2>/dev/null)
            success "Config:      $token_status"
        else
            success "Config:      exists"
        fi
    else
        warn "Config:      not yet created"
    fi

    sep
    echo ""

    if $all_ok && [[ -f "$APP_SCRIPT" ]]; then
        echo -e "  ${GREEN}${BOLD}+ Ready to launch!${RESET}"
    else
        echo -e "  ${YELLOW}${BOLD}! Some components missing. Run Install (option 2).${RESET}"
    fi
}

# ─── 2. Install Everything ───────────────────────────────────

action_install() {
    header ":: Install"

    mkdir -p "$APP_DIR"
    echo "=== Install $(date) ===" >> "$LOG_FILE"

    # ── Git Bash: manual guidance ─────────────────────────────
    if [[ "$PLATFORM" == "gitbash" ]]; then
        warn "Git Bash detected -- no package manager available."
        echo ""
        info "Install manually:"
        echo ""
        echo -e "    1. ${BOLD}Python${RESET}: https://www.python.org/downloads/"
        echo -e "       Check 'Add to PATH' during install."
        echo ""
        echo -e "    2. Reopen Git Bash, then run:"
        echo -e "       ${CYAN}pip install requests${RESET}"
        echo ""
        echo -e "    Or switch to MSYS2 for full package management:"
        echo -e "       ${CYAN}https://www.msys2.org/${RESET}"
        echo ""
        _install_app_script
        return
    fi

    # ── macOS without Homebrew ────────────────────────────────
    if [[ "$PLATFORM" == "macos" && "$PKG_MGR" == "none" ]]; then
        warn "macOS detected but Homebrew not found."
        echo ""
        info "Install Homebrew first:"
        echo -e "    ${CYAN}/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${RESET}"
        echo ""
        info "Then re-run this installer."
        echo ""
        _install_app_script
        return
    fi

    # ── No package manager ────────────────────────────────────
    if [[ "$PKG_MGR" == "none" ]]; then
        fail "No supported package manager found."
        info "Install Python 3, pip, and git manually."
        _install_app_script
        return
    fi

    # Step 1: Update
    info "Updating package index..."
    if pkg_update; then
        success "Package index updated"
    else
        warn "Package update had warnings (continuing)"
    fi

    # Step 2: Python
    if [[ -n "$PYTHON_CMD" ]]; then
        success "Python already installed ($(get_python_ver))"
    else
        info "Installing Python..."
        if pkg_install "$PYTHON_PKG"; then
            success "Python installed"
            if command -v python3 &>/dev/null; then PYTHON_CMD="python3"
            elif command -v python &>/dev/null; then PYTHON_CMD="python"
            fi
        else
            fail "Python install failed (see $LOG_FILE)"
        fi
    fi

    # Step 3: pip
    if [[ -n "$PIP_CMD" ]]; then
        success "pip already installed ($(get_pip_ver))"
    elif [[ -n "$PIP_PKG" ]]; then
        info "Installing pip..."
        if pkg_install "$PIP_PKG"; then
            success "pip installed"
            if command -v pip3 &>/dev/null; then PIP_CMD="pip3"
            elif command -v pip &>/dev/null; then PIP_CMD="pip"
            fi
        else
            fail "pip install failed (see $LOG_FILE)"
        fi
    fi

    # Step 4: Git
    if cmd_exists git; then
        success "Git already installed ($(get_git_ver))"
    else
        info "Installing Git..."
        if pkg_install "$GIT_PKG"; then
            success "Git installed"
        else
            fail "Git install failed (see $LOG_FILE)"
        fi
    fi

    # Step 5: requests
    if python_module_exists requests; then
        success "requests already installed"
    else
        if [[ -n "$REQUESTS_PKG" ]]; then
            info "Installing requests (system package)..."
            if pkg_install "$REQUESTS_PKG"; then
                success "requests installed"
            else
                info "Falling back to pip..."
                if pip_install requests; then
                    success "requests installed via pip"
                else
                    fail "requests install failed"
                fi
            fi
        else
            info "Installing requests via pip..."
            if pip_install requests; then
                success "requests installed"
            else
                fail "requests install failed"
            fi
        fi
    fi

    # Step 6: App script
    _install_app_script

    # Step 7: Auto-create gp alias (no prompts)
    _auto_alias

    sep
    echo ""
    success "Install complete!"
    echo ""
    info "Type ${BOLD}gp${RESET} to launch (or restart your terminal first)"
}

_auto_alias() {
    # Find shell rc file
    local rc_file=""
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
        if [[ -f "$rc" ]]; then
            rc_file="$rc"
            break
        fi
    done

    if [[ -z "$rc_file" ]]; then
        rc_file="$HOME/.bashrc"
        touch "$rc_file"
    fi

    # Skip if alias already exists
    if grep -q "alias gp=" "$rc_file" 2>/dev/null; then
        success "Alias 'gp' already exists in $rc_file"
        return
    fi

    # Point alias to INSTALLED copy (survives zip deletion)
    local launcher_path="$APP_DIR/gitpulse.sh"

    {
        echo ""
        echo "# gitpulse aliases"
        echo "alias gp='bash \"$launcher_path\"'"
        echo "alias gp-run='${PYTHON_CMD:-python3} \"$APP_SCRIPT\"'"
    } >> "$rc_file"

    success "Alias 'gp' added to $rc_file"
}

_install_app_script() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local local_script="$script_dir/gitpulse.py"

    if [[ -f "$local_script" ]]; then
        info "Copying project files -> $APP_DIR/"

        # Copy main script
        cp "$local_script" "$APP_SCRIPT"
        chmod +x "$APP_SCRIPT" 2>/dev/null || true

        # Copy all project folders
        for dir in lib web docs portable; do
            if [[ -d "$script_dir/$dir" ]]; then
                rm -rf "$APP_DIR/$dir"
                cp -r "$script_dir/$dir" "$APP_DIR/$dir"
                success "Copied $dir/"
            fi
        done

        # Copy docs
        for f in README.md ROADMAP.md; do
            [[ -f "$script_dir/$f" ]] && cp "$script_dir/$f" "$APP_DIR/$f"
        done

        # Copy launcher itself (so alias survives zip folder deletion)
        local launcher_src="$script_dir/$(basename "${BASH_SOURCE[0]}")"
        if [[ -f "$launcher_src" ]]; then
            cp "$launcher_src" "$APP_DIR/gitpulse.sh"
            chmod +x "$APP_DIR/gitpulse.sh" 2>/dev/null || true
            success "Copied launcher"
        fi

        success "All project files installed"
    elif [[ -f "$APP_SCRIPT" ]]; then
        success "App script already in place"
    else
        warn "gitpulse.py not found next to this launcher."
        warn "Place it in: $script_dir/"
        warn "Or copy manually to: $APP_SCRIPT"
    fi
}

# ─── 3. Launch ────────────────────────────────────────────────

action_launch() {
    local errors=()

    [[ -z "$PYTHON_CMD" ]]          && errors+=("Python not found")
    [[ ! -f "$APP_SCRIPT" ]]        && errors+=("App not installed ($APP_SCRIPT)")
    ! python_module_exists requests && errors+=("'requests' module missing")

    if [[ ${#errors[@]} -gt 0 ]]; then
        echo ""
        for e in "${errors[@]}"; do
            fail "$e"
        done
        echo ""
        warn "Run Install (option 2) first."
        return
    fi

    echo ""
    echo -e "  ${BOLD}Launch Mode${RESET}"
    echo -e "  --------------------------------------------------"
    echo -e "  ${GREEN} 1${RESET}   CLI"
    echo -e "  ${GREEN} 2${RESET}   Web UI (opens browser)"
    echo -e "  ${GREEN} 3${RESET}   CLI — Demo (no token)"
    echo -e "  ${GREEN} 4${RESET}   Web UI — Demo (no token)"
    echo -e "  ${GREEN} 0${RESET}   Back"
    echo -e "  --------------------------------------------------"
    read -rp "  > Mode: " launch_mode

    local args=""
    case "$launch_mode" in
        1) args="" ;;
        2) args="--web" ;;
        3) args="--demo" ;;
        4) args="--web --demo" ;;
        0|"") return ;;
        *) warn "Invalid option"; return ;;
    esac

    echo ""
    success "Launching $APP_NAME $args..."
    echo ""
    $PYTHON_CMD "$APP_SCRIPT" $args
}

# ─── 4. Configure ────────────────────────────────────────────

action_configure() {
    while true; do
        header ":: Configuration"

        if [[ -f "$CONFIG_FILE" && -n "$PYTHON_CMD" ]]; then
            info "Current config:"
            echo ""
            $PYTHON_CMD -c "
import json
with open('$CONFIG_FILE') as f:
    c = json.load(f)
for k, v in c.items():
    if k == 'token':
        v = '****' + v[-4:] if len(v) > 4 else '(not set)'
    print(f'    {k:<22} {v}')
" 2>/dev/null || true
            echo ""
        fi

        sep
        echo -e "  ${GREEN}1${RESET}  Set GitHub token"
        echo -e "  ${GREEN}2${RESET}  Set clone directory"
        echo -e "  ${GREEN}3${RESET}  Set default sort"
        echo -e "  ${GREEN}4${RESET}  View raw config"
        echo -e "  ${GREEN}5${RESET}  Open config in editor"
        echo -e "  ${GREEN}6${RESET}  Reset config to defaults"
        echo -e "  ${GREEN}7${RESET}  Create shell alias (gp)"
        echo -e "  ${GREEN}0${RESET}  Back"
        echo ""
        read -r -p "  > Option: " opt

        case "$opt" in
            1) _config_token ;;
            2) _config_clone_dir ;;
            3) _config_sort ;;
            4) _config_view ;;
            5) _config_edit ;;
            6) _config_reset ;;
            7) _config_alias ;;
            0|"") break ;;
            *) warn "Invalid option" ;;
        esac
        echo ""
    done
}

_config_write() {
    local key="$1"
    local value="$2"

    [[ -z "$PYTHON_CMD" ]] && { fail "Python required"; return; }
    mkdir -p "$APP_DIR"

    $PYTHON_CMD -c "
import json, os
path = '$CONFIG_FILE'
try:
    with open(path) as f:
        config = json.load(f)
except:
    config = {
        'token': '',
        'default_sort': 'updated',
        'default_direction': 'desc',
        'default_repo_type': 'all',
        'clone_directory': os.path.expanduser('~/repos'),
        'commits_count': 10
    }
config['$key'] = '$value'
with open(path, 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null

    chmod 600 "$CONFIG_FILE" 2>/dev/null || true
}

_config_token() {
    echo ""
    echo -e "  ${DIM}Create token: https://github.com/settings/tokens${RESET}"
    echo -e "  ${DIM}Scopes: repo, delete_repo${RESET}"
    echo ""
    read -r -p "  > GitHub token: " token
    [[ -z "$token" ]] && { warn "Cancelled"; return; }

    _config_write "token" "$token"
    success "Token saved"

    if cmd_exists curl; then
        info "Verifying..."
        local user
        user=$(curl -s -H "Authorization: token $token" https://api.github.com/user 2>/dev/null \
            | grep '"login"' | head -1 | cut -d'"' -f4)
        if [[ -n "$user" ]]; then
            success "Authenticated as: $user"
        else
            fail "Token verification failed"
        fi
    fi
}

_config_clone_dir() {
    echo ""
    read -r -p "  > Clone directory [$HOME/repos]: " dir
    dir="${dir:-$HOME/repos}"
    mkdir -p "$dir" 2>/dev/null || true
    _config_write "clone_directory" "$dir"
    success "Clone directory: $dir"
}

_config_sort() {
    echo ""
    echo "  Options: updated | created | pushed | full_name"
    read -r -p "  > Default sort [updated]: " val
    val="${val:-updated}"
    _config_write "default_sort" "$val"
    success "Default sort: $val"

    echo ""
    echo "  Options: desc (newest first) | asc (oldest first)"
    read -r -p "  > Direction [desc]: " dir
    dir="${dir:-desc}"
    _config_write "default_direction" "$dir"
    success "Direction: $dir"
}

_config_view() {
    echo ""
    if [[ -f "$CONFIG_FILE" ]]; then
        info "File: $CONFIG_FILE"
        echo ""
        cat "$CONFIG_FILE"
    else
        warn "No config file yet"
    fi
}

_config_edit() {
    [[ ! -f "$CONFIG_FILE" ]] && { warn "No config file. Set token first."; return; }

    local editor=""
    for e in "${EDITOR:-}" nano vim vi notepad; do
        if [[ -n "$e" ]] && cmd_exists "$e"; then
            editor="$e"
            break
        fi
    done

    if [[ -z "$editor" ]]; then
        warn "No editor found. Edit manually: $CONFIG_FILE"
        return
    fi

    if [[ "$editor" == "notepad" ]] && cmd_exists cygpath; then
        "$editor" "$(cygpath -w "$CONFIG_FILE")"
    else
        "$editor" "$CONFIG_FILE"
    fi
}

_config_reset() {
    echo ""
    read -r -p "  > Reset config (token will be cleared)? [y/N]: " yn
    [[ "$yn" != "y" && "$yn" != "Y" ]] && { info "Cancelled"; return; }

    [[ -z "$PYTHON_CMD" ]] && { fail "Python required"; return; }

    $PYTHON_CMD -c "
import json, os
config = {
    'token': '',
    'default_sort': 'updated',
    'default_direction': 'desc',
    'default_repo_type': 'all',
    'clone_directory': os.path.expanduser('~/repos'),
    'commits_count': 10
}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null
    chmod 600 "$CONFIG_FILE" 2>/dev/null || true
    success "Config reset"
}

_config_alias() {
    echo ""

    local rc_file=""
    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
        if [[ -f "$rc" ]]; then
            rc_file="$rc"
            break
        fi
    done

    if [[ -z "$rc_file" ]]; then
        rc_file="$HOME/.bashrc"
        touch "$rc_file"
    fi

    # Point alias to INSTALLED copy
    local launcher_path="$APP_DIR/gitpulse.sh"

    local alias_gp="alias gp='bash \"$launcher_path\"'"
    local alias_run="alias gp-run='${PYTHON_CMD:-python3} \"$APP_SCRIPT\"'"

    if grep -q "alias gp=" "$rc_file" 2>/dev/null; then
        warn "Alias 'gp' already in $rc_file"
        read -r -p "  > Overwrite? [y/N]: " ow
        [[ "$ow" != "y" && "$ow" != "Y" ]] && return
        sed_inplace '/# gitpulse aliases/d' "$rc_file"
        sed_inplace '/alias gp=/d' "$rc_file"
        sed_inplace '/alias gp-run=/d' "$rc_file"
    fi

    {
        echo ""
        echo "# gitpulse aliases"
        echo "$alias_gp"
        echo "$alias_run"
    } >> "$rc_file"

    success "Aliases added to $rc_file"
    info "  gp       = launcher (this menu)"
    info "  gp-run   = launch app directly"
    warn "Run: source $rc_file"
}

# ─── 5. Update ────────────────────────────────────────────────

action_update() {
    header ":: Update"

    _install_app_script

    echo ""
    read -r -p "  > Update system packages too? [y/N]: " yn
    if [[ "$yn" == "y" || "$yn" == "Y" ]]; then
        if [[ "$PKG_MGR" != "none" ]]; then
            info "Upgrading packages..."
            case "$PKG_MGR" in
                pacman)  $SUDO_CMD pacman -Syu --noconfirm >> "$LOG_FILE" 2>&1 ;;
                apt)     $SUDO_CMD apt-get update && $SUDO_CMD apt-get upgrade -y >> "$LOG_FILE" 2>&1 ;;
                dnf)     $SUDO_CMD dnf upgrade -y >> "$LOG_FILE" 2>&1 ;;
                yum)     $SUDO_CMD yum update -y >> "$LOG_FILE" 2>&1 ;;
                zypper)  $SUDO_CMD zypper update -y >> "$LOG_FILE" 2>&1 ;;
                apk)     $SUDO_CMD apk upgrade >> "$LOG_FILE" 2>&1 ;;
                brew)    brew upgrade >> "$LOG_FILE" 2>&1 ;;
            esac
            success "Packages upgraded"
        else
            warn "No package manager (Git Bash?). Skipping."
        fi
    fi

    if [[ -n "$PIP_CMD" ]]; then
        echo ""
        read -r -p "  > Update Python requests? [y/N]: " yn2
        if [[ "$yn2" == "y" || "$yn2" == "Y" ]]; then
            info "Upgrading requests..."
            pip_install "requests --upgrade" && success "requests updated"
        fi
    fi
}

# ─── 6. Diagnostics ──────────────────────────────────────────

action_diagnostics() {
    header ":: Diagnostics"

    echo -e "  ${BOLD}System${RESET}"
    echo -e "    OS:           $(uname -s) $(uname -r)"
    echo -e "    Arch:         $(uname -m)"
    echo -e "    MSYSTEM:      ${MSYSTEM:-N/A}"
    echo -e "    Platform:     $PLATFORM"
    echo -e "    Pkg manager:  $PKG_MGR"
    echo -e "    Shell:        ${SHELL:-unknown}"
    echo -e "    Home:         $HOME"
    echo ""

    echo -e "  ${BOLD}Tools${RESET}"
    echo -e "    Python:       $(get_python_ver) (${PYTHON_CMD:-none})"
    echo -e "    pip:          $(get_pip_ver) (${PIP_CMD:-none})"
    echo -e "    Git:          $(get_git_ver)"
    echo -e "    curl:         $(curl --version 2>/dev/null | head -1 | awk '{print $2}' || echo 'N/A')"
    echo ""

    echo -e "  ${BOLD}Python Modules${RESET}"
    for mod in requests json pathlib subprocess sys os; do
        if python_module_exists "$mod"; then
            echo -e "    ${GREEN}+${RESET} $mod"
        else
            echo -e "    ${RED}x${RESET} $mod"
        fi
    done
    echo ""

    echo -e "  ${BOLD}Files${RESET}"
    for f in "$APP_SCRIPT" "$CONFIG_FILE" "$LOG_FILE"; do
        if [[ -f "$f" ]]; then
            local sz
            sz=$(wc -c < "$f" 2>/dev/null)
            echo -e "    ${GREEN}+${RESET} $f  (${sz}B)"
        else
            echo -e "    ${RED}x${RESET} $f"
        fi
    done
    echo ""

    echo -e "  ${BOLD}Network${RESET}"
    if cmd_exists curl; then
        info "Testing api.github.com..."
        local code
        code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 https://api.github.com 2>/dev/null || echo "000")
        if [[ "$code" == "200" ]]; then
            success "GitHub API reachable (HTTP $code)"
        else
            fail "GitHub API returned HTTP $code"
        fi
    else
        warn "curl not available, skipping network test"
    fi
}

# ─── 7. Uninstall ────────────────────────────────────────────

action_uninstall() {
    header ":: Uninstall"

    warn "This will remove: $APP_DIR"
    echo ""
    read -r -p "  > Continue? [y/N]: " yn
    [[ "$yn" != "y" && "$yn" != "Y" ]] && { info "Cancelled"; return; }

    echo ""
    read -r -p "  > Keep config and token? [Y/n]: " keep

    if [[ "$keep" == "n" || "$keep" == "N" ]]; then
        rm -rf "$APP_DIR"
        success "Removed $APP_DIR (everything)"
    else
        rm -f "$APP_SCRIPT" "$LOG_FILE"
        success "Removed app (config kept at $CONFIG_FILE)"
    fi

    for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile" "$HOME/.profile"; do
        if [[ -f "$rc" ]] && grep -q "gp" "$rc" 2>/dev/null; then
            sed_inplace '/# gitpulse aliases/d' "$rc"
            sed_inplace '/alias gp=/d' "$rc"
            sed_inplace '/alias gp-run=/d' "$rc"
            info "Cleaned aliases from $rc"
        fi
    done

    success "Uninstall complete"
}

# ─── Main Menu ────────────────────────────────────────────────

banner() {
    cls
    echo -e "
${CYAN}${BOLD}+----------------------------------------------------------+
|              GitPulse  v${VERSION}                    |
|              Installer & Launcher                        |
+----------------------------------------------------------+
|  Platform: $(printf '%-45s' "$PLATFORM")|
|  Pkg mgr:  $(printf '%-45s' "$PKG_MGR")|
+----------------------------------------------------------+${RESET}
"
}

main_menu() {
    echo -e "  ${BOLD}MENU${RESET}"
    sep
    echo -e "  ${GREEN} 1${RESET}   Check installation"
    echo -e "  ${GREEN} 2${RESET}   Install everything"
    echo -e "  ${GREEN} 3${RESET}   Launch GitPulse"
    echo -e "  ${GREEN} 4${RESET}   Configure (token, prefs, alias)"
    echo -e "  ${GREEN} 5${RESET}   Update"
    echo -e "  ${GREEN} 6${RESET}   Diagnostics"
    echo -e "  ${GREEN} 7${RESET}   Uninstall"
    echo -e "  ${GREEN} 0${RESET}   Exit"
    sep
    echo ""
    read -r -p "  > Option: " choice
    echo ""
}

main() {
    while true; do
        banner
        main_menu

        case "$choice" in
            1) action_check;       pause_key ;;
            2) action_install;     pause_key ;;
            3) action_launch ;;
            4) action_configure ;;
            5) action_update;      pause_key ;;
            6) action_diagnostics; pause_key ;;
            7) action_uninstall;   pause_key ;;
            0|q|"")
                echo -e "  ${GREEN}Bye!${RESET}"
                echo ""
                exit 0
                ;;
            *)
                fail "Invalid option"
                pause_key
                ;;
        esac
    done
}

# ─── Entry Point ──────────────────────────────────────────────
setup_colors
detect_platform

case "${1:-}" in
    --check)    action_check ;;
    --install)  action_install ;;
    --launch)   action_launch ;;
    --config)   action_configure ;;
    --diag)     action_diagnostics ;;
    --help|-h)
        echo "Usage: $(basename "$0") [option]"
        echo ""
        echo "  (no args)   Interactive menu"
        echo "  --check     Check installation"
        echo "  --install   Install everything"
        echo "  --launch    Launch app"
        echo "  --config    Configure"
        echo "  --diag      Diagnostics"
        ;;
    *)  main ;;
esac
