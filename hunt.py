#!/usr/bin/env python3

import os
import math
import time
import sys
import smtplib
import binascii
import multiprocessing
import ctypes
import ssl
import re
import signal
from email.message import EmailMessage
from bitcoinlib.keys import HDKey
from bitcoinlib.services.services import Service

try:
    import psutil
except ImportError:
    psutil = None

try:
    import termios
    import tty
    import select
    HAVE_TERMIOS = True
except ImportError:
    HAVE_TERMIOS = False

try:
    import msvcrt
    HAVE_MSVCRT = True
except ImportError:
    HAVE_MSVCRT = False

# import our configs
import addresses
try:
    import env
except ImportError:
    print("Error: 'env.py' configuration file not found.")
    print("Please copy 'env.example' to 'env.py' and adjust your settings:")
    print("  cp env.example env.py")
    sys.exit(1)

# ANSI terminal styles
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')


def visual_len(s):
    return len(ANSI_REGEX.sub('', s))


def pad_box_line(content, inner_width=65):
    vlen = visual_len(content)
    pad = max(0, inner_width - vlen)
    return f"  │  {content}{' ' * pad}│"


def make_bar(percent, bar_len=24, color=CYAN):
    p = max(0.0, min(100.0, percent))
    filled = int(round(bar_len * p / 100.0))
    empty = bar_len - filled
    return f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"


def make_sparkline(per_cpu):
    if not per_cpu:
        return ""
    blocks = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    res = []
    for p in per_cpu:
        idx = min(7, int(p / 12.5))
        c = GREEN if p < 70 else (YELLOW if p < 85 else RED)
        res.append(f"{c}{blocks[idx]}{RESET}")
    return "".join(res)


def format_seconds(seconds):
    secs = int(max(0, seconds))
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def get_keypress():
    """Non-blocking keyboard check for quit keys ('q', 'x', etc.)"""
    if HAVE_MSVCRT:
        if msvcrt.kbhit():
            try:
                ch = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                return ch
            except Exception:
                return None
    elif HAVE_TERMIOS or not sys.platform.startswith('win'):
        try:
            r, _, _ = select.select([sys.stdin], [], [], 0)
            if r:
                return sys.stdin.read(1).lower()
        except Exception:
            return None
    return None


# send email
def send_email(lucky_text):
    text = env.email_text + "\n" + lucky_text
    msg = EmailMessage()
    msg.set_content(text)
    msg['Subject'] = env.subject
    msg['From'] = env.SEND_FROM
    msg['To'] = env.SEND_TO
    context = ssl.create_default_context()
    s = smtplib.SMTP(env.SMTP_HOST, env.SMTP_PORT)
    s.starttls(context=context)
    s.login(env.USER, env.PASS)
    s.send_message(msg)
    s.quit()
    print('Lucky Email sent!')


# worker process
def hunter(worker_idx, num_seconds, shared_counts, stop_event, sample_buf, match_count):
    # Ignore SIGINT in worker child processes so only the parent handles Ctrl+C cleanly
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        addresses_set = set(addresses.addresses)
        i = 0
        start = time.time()

        while not stop_event.is_set():
            # generate a random BTC private key
            private_key = binascii.hexlify(os.urandom(32)).decode('utf-8')
            key = HDKey(private_key)

            # derive both compressed and uncompressed legacy P2PKH addresses
            addr_compressed = key.address(encoding='base58')
            addr_uncompressed = key.address_uncompressed(encoding='base58')

            # check both address representations against the dormant set
            for address, key_type in ((addr_compressed, "COMPRESSED"), (addr_uncompressed, "UNCOMPRESSED")):
                if address in addresses_set:
                    with match_count.get_lock():
                        match_count.value += 1

                    try:
                        balance = str((Service().getbalance(address)) / 1e8) + " BTC"
                    except Exception:
                        balance = "UNKNOWN"

                    lucky_text = "--------------------------------------\n"
                    lucky_text += f"FOUND A LUCKY PAIR ({key_type}):\n"
                    lucky_text += f"PRIVATE KEY = {private_key}\n"
                    lucky_text += f"ADDRESS = {address}\n"
                    lucky_text += f"BALANCE = {balance}\n"
                    lucky_text += "--------------------------------------\n"

                    if getattr(env, "SEND_EMAILS", False):
                        try:
                            send_email(lucky_text)
                        except Exception as e:
                            print("Sending email failed:", e)

                    out_file = getattr(env, "OUT_FILE", "./keys-found.txt")
                    try:
                        with open(out_file, "a") as fl:
                            fl.write(lucky_text)
                    except Exception:
                        pass

            i += 1
            # periodically report progress to minimize IPC lock contention
            if i % 250 == 0:
                shared_counts[worker_idx] = i
                if worker_idx == 0:
                    sample_data = f"{private_key}|{addr_compressed}|{addr_uncompressed}".encode('utf-8')[:255]
                    sample_buf.value = sample_data
                if num_seconds > 0 and (time.time() - start) >= num_seconds:
                    break

        shared_counts[worker_idx] = i
    except (KeyboardInterrupt, SystemExit):
        pass


def render_dashboard(elapsed, max_seconds, total_keys, key_rate, addr_rate, matches, sample_str, inst_count, is_final=False, stop_status=None):
    if psutil:
        cpu_pct = psutil.cpu_percent(interval=None)
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        ram = psutil.virtual_memory()
        ram_pct = ram.percent
        ram_used = ram.used / (1024 ** 3)
        ram_total = ram.total / (1024 ** 3)
        ram_str = f"{ram_used:.1f}G / {ram_total:.1f}G"
    else:
        cpu_pct = 100.0 if not is_final else 0.0
        per_cpu = []
        ram_pct = 0.0
        ram_str = "N/A"

    cpu_color = GREEN if cpu_pct < 70 else (YELLOW if cpu_pct < 85 else RED)
    cpu_bar = make_bar(cpu_pct, 24, cpu_color)
    ram_bar = make_bar(ram_pct, 24, CYAN)
    spark = make_sparkline(per_cpu)

    if matches > 0:
        status_str = f"{BOLD}{RED}🚨 {matches} MATCH FOUND! 🚨{RESET}"
    elif is_final:
        if stop_status == "STOPPED":
            status_str = f"{BOLD}{YELLOW}⏹ STOPPED (User){RESET}"
        else:
            status_str = f"{BOLD}{CYAN}✔ COMPLETED{RESET}"
    else:
        status_str = f"{BOLD}{GREEN}● HUNTING{RESET}"

    if max_seconds > 0:
        time_pct = min(100.0, (elapsed / max_seconds) * 100.0)
        time_bar = make_bar(time_pct, 24, YELLOW)
        time_disp = f"[{time_bar}] {BOLD}{format_seconds(elapsed)} / {format_seconds(max_seconds)}{RESET} ({time_pct:.0f}%)"
    else:
        time_disp = f"{BOLD}{format_seconds(elapsed)}{RESET} (continuous mode)"

    sample_pk = "Initializing..."
    sample_c = "Searching..."
    sample_u = "Searching..."
    if sample_str and "|" in sample_str:
        parts = sample_str.split("|")
        sample_pk = parts[0]
        if len(sample_pk) > 24:
            sample_pk = f"{sample_pk[:10]}...{sample_pk[-10:]}"
        if len(parts) > 1:
            sample_c = parts[1]
        if len(parts) > 2:
            sample_u = parts[2]

    total_addrs = total_keys * 2
    num_targets = len(addresses.addresses)

    output = []
    output.append(f"{BOLD}{CYAN}╔════════════════════════════════════════════════════════════════════╗{RESET}")
    output.append(f"{BOLD}{CYAN}║                     🪙  DORMANT BITCOIN HUNTER                     ║{RESET}")
    output.append(f"{BOLD}{CYAN}╚════════════════════════════════════════════════════════════════════╝{RESET}")
    output.append("")
    output.append(f"  {BOLD}Status:{RESET}  {status_str:<26} {BOLD}Workers:{RESET} {inst_count} processes")
    output.append(f"  {BOLD}Targets:{RESET} {num_targets:,} addresses loaded      {BOLD}Matches:{RESET} {BOLD}{GREEN if matches == 0 else RED}{matches}{RESET}")
    output.append(f"  {BOLD}Cycle Progress:{RESET} {time_disp}")
    if not is_final:
        output.append(f"  {DIM}Controls: Press {BOLD}[q]{RESET}{DIM} or {BOLD}[Ctrl+C]{RESET}{DIM} to stop gracefully{RESET}")
    else:
        output.append("")
    output.append("")
    output.append(f"  {DIM}┌─ SYSTEM UTILIZATION ──────────────────────────────────────────────┐{RESET}")
    output.append(pad_box_line(f"{BOLD}CPU Usage:{RESET}  [{cpu_bar}] {BOLD}{cpu_pct:5.1f}%{RESET}"))
    if spark:
        core_count = len(per_cpu)
        output.append(pad_box_line(f"{BOLD}Per-Core:{RESET}   [{spark}] {BOLD}({core_count} Cores){RESET}"))
    output.append(pad_box_line(f"{BOLD}RAM Usage:{RESET}  [{ram_bar}] {BOLD}{ram_pct:5.1f}%{RESET} ({ram_str})"))
    output.append(f"  {DIM}└───────────────────────────────────────────────────────────────────┘{RESET}")
    output.append("")
    output.append(f"  {DIM}┌─ SEARCH THROUGHPUT ───────────────────────────────────────────────┐{RESET}")
    output.append(pad_box_line(f"{BOLD}Keys Rate:{RESET}      {CYAN}{math.floor(key_rate):>9,}{RESET} keys/sec"))
    output.append(pad_box_line(f"{BOLD}Address Rate:{RESET}   {GREEN}{math.floor(addr_rate):>9,}{RESET} addr/sec (compressed + uncompressed)"))
    output.append(pad_box_line(f"{BOLD}Total Keys:{RESET}     {total_keys:>9,}"))
    output.append(pad_box_line(f"{BOLD}Total Addrs:{RESET}    {total_addrs:>9,}"))
    output.append(f"  {DIM}└───────────────────────────────────────────────────────────────────┘{RESET}")
    output.append("")
    output.append(f"  {DIM}┌─ LIVE ACTIVITY SAMPLE ────────────────────────────────────────────┐{RESET}")
    output.append(pad_box_line(f"{BOLD}Private Key:{RESET}  {DIM}{sample_pk}{RESET}"))
    output.append(pad_box_line(f"{BOLD}Address (C):{RESET}  {sample_c}"))
    output.append(pad_box_line(f"{BOLD}Address (U):{RESET}  {sample_u}"))
    output.append(f"  {DIM}└───────────────────────────────────────────────────────────────────┘{RESET}")

    return "\n".join(output)


if __name__ == '__main__':
    if env.NUM_INSTANCES == 0:
        inst_count = multiprocessing.cpu_count()
    else:
        inst_count = env.NUM_INSTANCES

    shared_counts = multiprocessing.RawArray(ctypes.c_uint64, inst_count)
    sample_buf = multiprocessing.Array(ctypes.c_char, 256)
    match_count = multiprocessing.Value('i', 0)
    stop_event = multiprocessing.Event()

    processes = []
    for i in range(inst_count):
        p = multiprocessing.Process(
            target=hunter,
            args=(i, env.MAX_SECONDS, shared_counts, stop_event, sample_buf, match_count)
        )
        processes.append(p)
        p.start()

    is_tty = sys.stdout.isatty()
    old_term_settings = None

    if is_tty:
        # Hide cursor & clear screen
        sys.stdout.write("\033[2J\033[H\033[?25l")
        sys.stdout.flush()

        # Set terminal to cbreak mode so single keystrokes like 'q' can be read immediately
        if HAVE_TERMIOS and sys.stdin.isatty():
            try:
                old_term_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except Exception:
                old_term_settings = None

    start_time = time.time()
    last_log_time = start_time
    interrupted_by_user = False

    try:
        while True:
            time.sleep(0.15)
            elapsed = time.time() - start_time
            total_keys = sum(shared_counts)
            key_rate = total_keys / elapsed if elapsed > 0 else 0
            addr_rate = (total_keys * 2) / elapsed if elapsed > 0 else 0
            matches = match_count.value

            # Check for keyboard shortcut to stop
            key = get_keypress()
            if key in ('q', 'x', '\x03'):
                interrupted_by_user = True
                break

            try:
                sample_str = sample_buf.value.decode('utf-8')
            except Exception:
                sample_str = ""

            if is_tty:
                dashboard = render_dashboard(
                    elapsed, env.MAX_SECONDS, total_keys, key_rate, addr_rate,
                    matches, sample_str, inst_count, is_final=False
                )
                sys.stdout.write("\033[H" + dashboard + "\n")
                sys.stdout.flush()
            else:
                if elapsed - last_log_time >= 10.0:
                    last_log_time = elapsed
                    cpu_str = f"CPU: {psutil.cpu_percent(interval=None):.1f}%" if psutil else ""
                    print(f"[{format_seconds(elapsed)}] {total_keys:,} keys ({total_keys*2:,} addr) | {math.floor(key_rate):,} keys/s | {cpu_str}")

            # Check if cycle time is reached
            if env.MAX_SECONDS > 0 and elapsed >= env.MAX_SECONDS:
                break

            # If all processes terminated early
            if not any(p.is_alive() for p in processes):
                break

    except KeyboardInterrupt:
        interrupted_by_user = True
    finally:
        # Signal all workers to stop immediately
        stop_event.set()

        # Restore terminal settings immediately
        if old_term_settings is not None:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_term_settings)
            except Exception:
                pass

        # Join worker processes cleanly
        for p in processes:
            p.join(timeout=0.5)
            if p.is_alive():
                p.terminate()

        elapsed = time.time() - start_time
        total_keys = sum(shared_counts)
        key_rate = total_keys / elapsed if elapsed > 0 else 0
        addr_rate = (total_keys * 2) / elapsed if elapsed > 0 else 0
        matches = match_count.value

        try:
            sample_str = sample_buf.value.decode('utf-8')
        except Exception:
            sample_str = ""

        if is_tty:
            sys.stdout.write("\033[?25h")  # restore cursor
            final_status = "STOPPED" if interrupted_by_user else "COMPLETED"
            dashboard = render_dashboard(
                elapsed, env.MAX_SECONDS, total_keys, key_rate, addr_rate,
                matches, sample_str, inst_count, is_final=True, stop_status=final_status
            )
            sys.stdout.write("\033[H" + dashboard + "\n\n")
            sys.stdout.flush()
        else:
            reason = "Stopped by user" if interrupted_by_user else "Completed"
            print(f"\n{reason}: {total_keys:,} keys ({total_keys*2:,} addr) in {format_seconds(elapsed)} ({math.floor(key_rate):,} keys/s). Matches: {matches}")

        if interrupted_by_user:
            sys.exit(130)
