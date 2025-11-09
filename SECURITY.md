# Security Policy

## 🔒 Our Security Commitment

The GLADOS Voice Assistant is designed with **privacy and security as core principles**. All voice processing happens locally on your Raspberry Pi—no data leaves your device unless you explicitly configure external integrations.

## 🛡️ Security Features

### Privacy by Design
- ✅ **100% Local Processing**: Speech recognition, language models, and text-to-speech all run on-device
- ✅ **No Telemetry**: We collect zero usage data or analytics
- ✅ **No Cloud Dependencies**: Works completely offline after initial setup
- ✅ **No External APIs**: Default configuration requires no API keys or internet access

### Data Protection
- ✅ **Credentials Protection**: Sensitive data stored in `secrets.py` (git-ignored)
- ✅ **Secure Defaults**: All external integrations are opt-in and disabled by default
- ✅ **Minimal Permissions**: Runs with standard user privileges (no root required for operation)
- ✅ **Temporary Audio**: Voice recordings are processed in memory and immediately deleted

### Code Security
- ✅ **Open Source**: All code is publicly auditable
- ✅ **No Obfuscation**: Clear, readable Python code
- ✅ **Minimal Dependencies**: Only essential, well-maintained packages
- ✅ **No Binary Blobs**: All models are in standard formats (ONNX, PyTorch)

## 🔐 Best Practices for Users

### 1. Protect Your Credentials

**DO:**
- ✅ Keep `secrets.py` file permissions restrictive: `chmod 600 config/secrets.py`
- ✅ Use unique, strong passwords for WiFi and API keys
- ✅ Regularly rotate API keys if you use external services
- ✅ Back up credentials securely (encrypted storage)

**DON'T:**
- ❌ Commit `secrets.py` to version control
- ❌ Share credentials in issues or discussions
- ❌ Use the same API key across multiple projects
- ❌ Store credentials in world-readable files

### 2. Keep Software Updated

```bash
# Update the project
cd glados-voice-assistant
git pull origin main

# Update Python dependencies
source voice_ai_env/bin/activate
pip install --upgrade -r requirements.txt

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Ollama models
ollama pull gemma2:2b-instruct-q4_0
```

### 3. Network Security

If you enable WiFi or external APIs:
- Use WPA3 or WPA2 encryption for WiFi
- Consider running on an isolated network segment
- Use firewall rules to limit outbound connections
- Monitor network traffic if paranoid (totally valid!)

### 4. Physical Security

Your Raspberry Pi has physical access to:
- Microphone (continuous audio access)
- Network connection (if configured)
- GPIO pins (hardware control)

Recommendations:
- Place device in secure location
- Consider LED indicator visibility (know when listening)
- Use hardware switch for microphone if needed
- Lock down physical access in sensitive environments

## 🚨 Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability, please follow responsible disclosure practices.

### What to Report

Please report any issues that could compromise:
- User privacy or data security
- Credential leakage or exposure
- Unauthorized access or privilege escalation
- Code execution vulnerabilities
- Dependencies with known CVEs

### How to Report

**For sensitive security issues, please DO NOT open a public issue.**

Instead:

1. **Email**: Send details to `[YOUR_EMAIL_HERE]` with subject "SECURITY: GLADOS Voice Assistant"
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)
3. **Response**: We'll acknowledge within 48 hours
4. **Timeline**: We aim to patch critical issues within 7 days

### What Happens Next

1. We'll investigate and confirm the issue
2. We'll develop and test a fix
3. We'll release a security update
4. We'll credit you in release notes (if desired)
5. We'll publish a security advisory

## 🔍 Security Auditing

### Self-Audit Checklist

Run these checks periodically:

```bash
# Check file permissions
find . -name "secrets.py" -exec ls -la {} \;

# Check for hardcoded credentials (should return nothing)
grep -r "sk-" src/ --exclude-dir=.git --exclude="*.md"
grep -r "password.*=" src/ --exclude-dir=.git --exclude="*.md"

# Verify .gitignore is working
git status --ignored

# Check for world-readable files
find . -type f -perm -004 | grep -v ".git"

# Review network connections (while running)
sudo netstat -tunapl | grep python

# Check for suspicious processes
ps aux | grep voice_ai
```

### Automated Security Scanning

For contributors:

```bash
# Install security tools
pip install bandit safety

# Scan code for vulnerabilities
bandit -r src/

# Check dependencies for known vulnerabilities
safety check --json

# Update vulnerable packages
pip-audit --fix
```

## 📋 Security Changelog

### Version 1.0.0 (Initial Release)
- ✅ Implemented local-only processing architecture
- ✅ Added `.gitignore` for sensitive files
- ✅ Created `secrets.py.example` template
- ✅ Documented security best practices
- ✅ Zero external API requirements by default

## 🔗 Related Security Resources

- [OWASP IoT Security](https://owasp.org/www-project-internet-of-things/)
- [Raspberry Pi Security](https://www.raspberrypi.com/documentation/computers/configuration.html#securing-your-raspberry-pi)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

## ✅ Security Certifications

While this is an open-source hobby project and not formally certified, we strive to follow:
- OWASP Top 10 guidelines
- Python security best practices
- Principle of least privilege
- Defense in depth strategies
- Privacy by design principles

## 🙏 Responsible Disclosure Hall of Fame

Security researchers who responsibly disclose vulnerabilities will be acknowledged here:

*No reports yet - be the first!*

---

**Your privacy is our priority. Stay secure! 🔐**

*Last updated: November 2025*
