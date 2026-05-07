# PKbrute Installation Guide for Kali Linux

## Method 1: Direct Git Clone (Recommended)

### On Kali Linux Terminal:

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/PKbrute.git
cd PKbrute

# 2. Make installer executable
chmod +x setup.sh

# 3. Run installer (as root)
sudo ./setup.sh

# 4. Run the tool
python3 pkbrute.py
