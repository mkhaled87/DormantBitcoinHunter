# 🪙 Dormant Bitcoin Hunter

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/mkhaled87/DormantBitcoinHunter/pulls)

An educational, multi-process Bitcoin private key generator and dormant address hunter written in Python.

**Dormant Bitcoin Hunter** generates random 256-bit Bitcoin private keys, derives their corresponding public addresses (legacy P2PKH), and matches them in real time against a target dataset of ~42,400 high-value dormant Bitcoin addresses (derived from early Bitcoin blocks and the [BitInfoCharts Dormant List](https://bitinfocharts.com/top-100-dormant_8y-bitcoin-addresses.html)). If a match is found, it queries the live blockchain balance, writes the key pair to disk, and can optionally dispatch an instant email alert via SMTP.

> This project is inspired by [Henshall/BitcoinPrivateKeyHunter](https://github.com/Henshall/BitcoinPrivateKeyHunter) and [dodiitt/bitcoin_finder_python](https://github.com/dodiitt/bitcoin_finder_python), with enhancements for correctness and multiprocessing throughput.

---

> [!NOTE]
> **Cryptographic Feasibility & The Law of Large Numbers:**
> The Bitcoin private keyspace is $2^{256}$ ($\approx 1.15 \times 10^{77}$ combinations). Even generating tens of thousands of keys per second across multiple machines, the probability of finding a collision with an existing address is astronomically close to zero. This project is created for educational and experimental purposes to explore cryptography, key derivation, and multiprocessing.

---

## ✨ Features

- **Multi-Process Concurrency:** Automatically detects and saturates all available CPU cores.
- **Fast Lookups:** Utilizes $O(1)$ set lookups against 42,000+ dormant addresses.
- **Cryptographically Secure RNG:** Uses Python's `os.urandom(32)` to generate unbiased 256-bit entropy.
- **Balance Verification:** Live balance queries on hits via `bitcoinlib`.
- **Instant Alerts:** Configurable SMTP email notifications with TLS.
- **Continuous Execution:** Included shell and batch scripts for 24/7 background operation.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.8+** (tested up to Python 3.13)
- `pip`

### 2. Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/mkhaled87/DormantBitcoinHunter.git
cd DormantBitcoinHunter

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy the example configuration file:

```bash
cp env.example env.py
```

Edit `env.py` to match your preferences:
- `MAX_SECONDS`: Duration of each hunt cycle before reporting key generation rates.
- `NUM_INSTANCES`: Number of worker processes (`0` = auto-detect all CPU cores).
- `SEND_EMAILS`: Set to `True` if you want email alerts on a match (requires SMTP credentials).

### 4. Running the Hunter

**Single Timed Run:**
```bash
python3 hunt.py
```

**Continuous Mode:**
- **Linux / macOS:**
  ```bash
  chmod +x run_forever.sh
  ./run_forever.sh
  ```
- **Windows:**
  ```cmd
  run_forever.bat
  ```

---

## ⚙️ Configuration Reference

All settings are configured inside `env.py`:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `NUM_INSTANCES` | integer | `0` | Number of parallel worker processes (`0` uses all detected CPU cores). |
| `MAX_SECONDS` | integer | `60` | Duration (in seconds) of each execution cycle before printing statistics. |
| `OUT_FILE` | string | `"./keys-found.txt"` | File destination where matched private keys and balances are saved. |
| `SEND_EMAILS` | boolean | `True` | Whether to send an email alert when a match is found. |
| `SEND_TO` | list | `["email@email.com"]` | Recipient email address(es). |
| `SEND_FROM` | string | `"email@email.com"` | Sender email address. |
| `USER` | string | `"email@email.com"` | SMTP username. |
| `PASS` | string | `"password_goes_here"` | SMTP password or app password. |
| `SMTP_HOST` | string | `"my_smtp.host.com"` | SMTP relay server host. |
| `SMTP_PORT` | integer | `587` | SMTP port (typically `587` for STARTTLS). |

---

## 📊 How It Works

```mermaid
flowchart TD
    A["os.urandom(32)"] --> B["256-bit Private Key"]
    B --> C["Base58 P2PKH Address"]
    C --> D{"In Dormant Addresses List?"}
    D -- No --> E["Increment Counter & Loop"]
    E --> A
    D -- Yes --> F["Query Live Balance (bitcoinlib)"]
    F --> G["Append to keys-found.txt"]
    G --> H{"SEND_EMAILS enabled?"}
    H -- Yes --> I["Send SMTP Email Alert"]
    H -- No --> J["Continue Searching"]
    I --> J
```

---

## ☕ Donations

If you find this project interesting or educational, feel free to support:

- **BTC:** `1MKHALEDqXhBzqa86hj8FbDGW5HvDdA5Tq`
- **ETH:** `0x14551935EDf4aF06909336084412dd805aE14b26`

---

## ⚖️ Disclaimer

This software is provided for educational, research, and entertainment purposes only. The author accepts no responsibility for any misuse, damage, or loss resulting from running or modifying this software.
