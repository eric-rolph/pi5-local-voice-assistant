#!/bin/bash

################################################################################
# GLADOS Voice Assistant - Automated Installation Script
# For Raspberry Pi 5 with Adafruit Voice Bonnet
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/voice_ai_env"
LOG_FILE="$PROJECT_DIR/install.log"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║            🤖 GLADOS Voice Assistant Installer 🤖              ║"
    echo "║                                                                ║"
    echo "║              \"The Enrichment Center reminds you               ║"
    echo "║               that the installation process is safe.\"         ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')]${NC} ${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')]${NC} ${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')]${NC} ${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')]${NC} ${RED}✗${NC} $1"
}

check_system() {
    print_step "Checking system requirements..."
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
        print_warning "Not running on a Raspberry Pi - hardware features may not work"
    else
        print_success "Raspberry Pi detected"
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.9+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_success "Python $PYTHON_VERSION detected"
    
    # Check available memory
    TOTAL_MEM=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 3500 ]; then
        print_warning "Less than 4GB RAM detected ($TOTAL_MEM MB). Performance may be limited."
    else
        print_success "Sufficient RAM detected (${TOTAL_MEM}MB)"
    fi
}

install_system_dependencies() {
    print_step "Installing system dependencies..."
    
    sudo apt update >> "$LOG_FILE" 2>&1
    
    PACKAGES=(
        python3-pip
        python3-venv
        python3-dev
        git
        portaudio19-dev
        libasound2-dev
        build-essential
        cmake
        libopenblas-dev
        libsndfile1
        ffmpeg
        wget
        curl
    )
    
    for package in "${PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii.*$package"; then
            print_step "Installing $package..."
            sudo apt install -y "$package" >> "$LOG_FILE" 2>&1
            print_success "$package installed"
        else
            print_success "$package already installed"
        fi
    done
}

create_virtual_environment() {
    print_step "Creating Python virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists, recreating..."
        rm -rf "$VENV_DIR"
    fi
    
    python3 -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1
    print_success "Virtual environment created"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    print_step "Upgrading pip..."
    pip install --upgrade pip >> "$LOG_FILE" 2>&1
    print_success "Pip upgraded"
}

install_python_dependencies() {
    print_step "Installing Python dependencies (this may take 10-15 minutes)..."
    
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        print_error "requirements.txt not found!"
        exit 1
    fi
    
    pip install -r "$PROJECT_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
    print_success "Python dependencies installed"
}

install_ollama() {
    print_step "Checking Ollama installation..."
    
    if command -v ollama &> /dev/null; then
        print_success "Ollama already installed"
    else
        print_step "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh >> "$LOG_FILE" 2>&1
        print_success "Ollama installed"
    fi
    
    # Start Ollama service
    print_step "Starting Ollama service..."
    sudo systemctl enable ollama >> "$LOG_FILE" 2>&1 || true
    sudo systemctl start ollama >> "$LOG_FILE" 2>&1 || true
    sleep 2
    print_success "Ollama service started"
    
    # Download LLM model
    print_step "Downloading Gemma 2 2B model (this may take 5-10 minutes)..."
    ollama pull gemma2:2b-instruct-q4_0 >> "$LOG_FILE" 2>&1
    print_success "LLM model downloaded"
}

download_voice_models() {
    print_step "Downloading GLaDOS voice model..."
    
    PIPER_DIR="$PROJECT_DIR/models/piper"
    mkdir -p "$PIPER_DIR"
    
    cd "$PIPER_DIR"
    
    if [ -f "glados.onnx" ]; then
        print_success "GLaDOS voice model already exists"
    else
        wget -q --show-progress \
            https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/glados/medium/glados.onnx \
            >> "$LOG_FILE" 2>&1
        print_success "GLaDOS voice model downloaded"
    fi
    
    if [ -f "glados.onnx.json" ]; then
        print_success "GLaDOS config already exists"
    else
        wget -q --show-progress \
            https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/glados/medium/glados.onnx.json \
            >> "$LOG_FILE" 2>&1
        print_success "GLaDOS config downloaded"
    fi
    
    cd "$PROJECT_DIR"
}

setup_configuration() {
    print_step "Setting up configuration..."
    
    # Create secrets.py if it doesn't exist
    if [ ! -f "$PROJECT_DIR/config/secrets.py" ]; then
        cp "$PROJECT_DIR/config/secrets.py.example" "$PROJECT_DIR/config/secrets.py"
        print_success "Created secrets.py from template"
        print_warning "Remember to edit config/secrets.py if you need WiFi or API integration"
    else
        print_success "secrets.py already exists"
    fi
    
    # Set proper permissions
    chmod 600 "$PROJECT_DIR/config/secrets.py" 2>/dev/null || true
}

create_launcher_script() {
    print_step "Creating launcher script..."
    
    cat > "$PROJECT_DIR/start_assistant.sh" << 'EOF'
#!/bin/bash
# GLADOS Voice Assistant Launcher

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Activate virtual environment
source voice_ai_env/bin/activate

# Run the assistant
python src/voice_ai_assistant.py

EOF
    
    chmod +x "$PROJECT_DIR/start_assistant.sh"
    print_success "Launcher script created"
}

run_system_test() {
    print_step "Running system tests..."
    
    # Test imports
    print_step "Testing Python imports..."
    python3 << 'PYTHON_EOF' >> "$LOG_FILE" 2>&1
import sys
try:
    import pyaudio
    import numpy
    import yaml
    import ollama
    print("✓ Core imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
PYTHON_EOF
    
    if [ $? -eq 0 ]; then
        print_success "Python imports OK"
    else
        print_error "Python import test failed - check $LOG_FILE"
        exit 1
    fi
    
    # Test Ollama
    print_step "Testing Ollama connection..."
    if ollama list | grep -q "gemma2"; then
        print_success "Ollama connection OK"
    else
        print_warning "Could not verify Ollama models"
    fi
}

print_completion_message() {
    echo ""
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║                  ✅ Installation Complete! ✅                  ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${CYAN}🚀 To start the GLADOS Voice Assistant:${NC}"
    echo ""
    echo -e "   ${YELLOW}cd $PROJECT_DIR${NC}"
    echo -e "   ${YELLOW}./start_assistant.sh${NC}"
    echo ""
    echo -e "${CYAN}📝 Configuration:${NC}"
    echo -e "   Edit ${YELLOW}config/voice_ai_config.yaml${NC} for settings"
    echo -e "   Edit ${YELLOW}config/secrets.py${NC} for credentials (optional)"
    echo ""
    echo -e "${CYAN}📚 Documentation:${NC}"
    echo -e "   README: ${YELLOW}$PROJECT_DIR/README.md${NC}"
    echo -e "   Logs: ${YELLOW}$PROJECT_DIR/logs/voice_ai.log${NC}"
    echo ""
    echo -e "${PURPLE}\"The Enrichment Center is pleased to inform you"
    echo -e " that installation was a complete success.\"${NC}"
    echo ""
}

################################################################################
# Main Installation Flow
################################################################################

main() {
    # Clear log file
    > "$LOG_FILE"
    
    print_header
    
    echo -e "${YELLOW}This script will install:${NC}"
    echo "  • System dependencies"
    echo "  • Python virtual environment"
    echo "  • Python packages"
    echo "  • Ollama LLM server"
    echo "  • GLaDOS voice model"
    echo ""
    echo -e "${YELLOW}Installation log:${NC} $LOG_FILE"
    echo ""
    read -p "Continue with installation? (y/N) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo ""
    
    # Run installation steps
    check_system
    install_system_dependencies
    create_virtual_environment
    install_python_dependencies
    install_ollama
    download_voice_models
    setup_configuration
    create_launcher_script
    run_system_test
    
    # Completion
    print_completion_message
}

# Run main installation
main
