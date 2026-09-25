import http.server
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
import socketserver
import json
import sqlite3
import secrets
import string
import time
import os
import urllib.parse
import hashlib
import base64
import urllib.request
import re

PORT = int(os.environ.get("PORT", 5500))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIRECTORY, "keys.db")

SCRIPT_SECRET = "OVITAR_SECURITY_SHIELD_SECRET_KEY_9921!"
ADMIN_TOKEN = "OVT_ADM_LUNA_984f1a_SECURE"

SCRIPTS_DIR = os.path.join(DIRECTORY, "scripts")
MAIN_SCRIPT_PATH = os.path.join(SCRIPTS_DIR, "main_script.lua")
FAKE_SCRIPT_PATH = os.path.join(SCRIPTS_DIR, "fake_script.lua")
os.makedirs(SCRIPTS_DIR, exist_ok=True)

def encrypt_payload(plain_text, salt=""):
    key = (SCRIPT_SECRET + salt).encode('utf-8')
    if isinstance(plain_text, str):
        raw_bytes = plain_text.encode('utf-8')
    else:
        raw_bytes = plain_text
    if not raw_bytes:
        return ""
    key_len = len(key)
    repeated_key = (key * (len(raw_bytes) // key_len + 1))[:len(raw_bytes)]
    a = int.from_bytes(raw_bytes, 'big')
    b = int.from_bytes(repeated_key, 'big')
    encrypted = (a ^ b).to_bytes(len(raw_bytes), 'big')
    return base64.b64encode(encrypted).decode('ascii')

def get_main_script():
    if os.path.exists(MAIN_SCRIPT_PATH):
        try:
            with open(MAIN_SCRIPT_PATH, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading main script file: {e}")
    return get_setting("script_content", "-- Ovitar Main Script\nprint('Loaded!')\n")

def save_main_script(content_str, filename="main_script.lua"):
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    with open(MAIN_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(content_str)
    file_size = os.path.getsize(MAIN_SCRIPT_PATH)
    line_count = content_str.count('\n') + 1
    now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    set_setting("script_file_name", filename)
    set_setting("script_file_size", str(file_size))
    set_setting("script_line_count", str(line_count))
    set_setting("script_updated_at", now_str)
    if file_size < 65536:
        set_setting("script_content", content_str)
    else:
        set_setting("script_content", f"-- [DEPLOYED FILE: {filename} ({file_size:,} bytes) at {now_str}]")
    return file_size, line_count, now_str

def get_fake_script():
    if os.path.exists(FAKE_SCRIPT_PATH):
        try:
            with open(FAKE_SCRIPT_PATH, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            pass
    return get_setting("fake_script_content", "--[[\n    [OVITAR SCRIPT DECOY]\n    Checksum: 0x8892FA10-VERIFIED\n]]\n\nprint('✨ Ovitar Core System Loaded (Decoy Safe)')\n")

def save_fake_script(content_str):
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    with open(FAKE_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(content_str)
    set_setting("fake_script_content", content_str)

def hash_pw(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at INTEGER NOT NULL,
            last_login INTEGER DEFAULT 0,
            last_hwid_reset INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS license_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_string TEXT UNIQUE NOT NULL,
            key_type TEXT NOT NULL, /* 'free', 'user', 'dev', 'lifetime' */
            duration_days REAL NOT NULL, /* 0.125 for 3h, 7 for week, 30 for month, 0 for lifetime */
            created_at INTEGER NOT NULL,
            expires_at INTEGER,
            is_active INTEGER DEFAULT 1,
            is_used INTEGER DEFAULT 0,
            hwid TEXT DEFAULT NULL,
            claimed_by_ip TEXT DEFAULT NULL,
            registered_to TEXT DEFAULT NULL,
            registered_at INTEGER DEFAULT 0,
            note TEXT DEFAULT ''
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS free_key_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ip TEXT NOT NULL,
            claimed_at INTEGER NOT NULL,
            key_string TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS cultureland_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            plan_type TEXT NOT NULL, /* 'weekly', 'monthly', 'lifetime' */
            pin_code TEXT NOT NULL,
            amount_expected INTEGER NOT NULL,
            amount_charged INTEGER DEFAULT 0,
            status TEXT NOT NULL, /* 'success', 'failed', 'invalid_pin' */
            key_issued TEXT DEFAULT NULL,
            response_msg TEXT DEFAULT '',
            created_at INTEGER NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    # Ensure default admin
    c.execute("SELECT id FROM users WHERE username = 'lunatop3'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)",
            ('lunatop3', hash_pw('asd3411@11'), int(time.time()))
        )
        
    defaults = [
        ("api_status", "online"), # 'online', 'maintenance', 'offline'
        ("api_message", "정상 서비스 중"),
        ("script_version", "v0.6.0"),
        ("script_content", "--[[\n    OVITAR v0.6.0\n    Your space. Your way.\n]]\n\nlocal Library = loadstring(game:HttpGet('https://raw.githubusercontent.com/bloodball/-back-ups-for-libs/main/turtle'))()\nprint('✨ [OVITAR] Script executed successfully!')\n"),
        ("fake_script_content", "--[[\n    =====================================================\n    ✨ OVITAR SECURE INTERNAL DECOY KERNEL ✨\n    =====================================================\n    Checksum: 0x8892FA10-VERIFIED\n    Environment: Protected Luau Sandbox\n]]\n\nlocal Players = game:GetService('Players')\nlocal LocalPlayer = Players.LocalPlayer\nprint('🛡️ [OVITAR CORE] Decoy subsystem initialized for ' .. tostring(LocalPlayer.Name))\n"),
        ("discord_webhook_url", ""),
        ("cultureland_session_token", "95cd4dcf-e26e-4738-a62d-c566f9308c8c")
    ]
    for k, v in defaults:
        c.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

def generate_key_string(prefix="OVITAR"):
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(secrets.choice(chars) for _ in range(4)) for _ in range(3)]
    return f"{prefix}-" + "-".join(parts)

def get_setting(key, default=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def charge_cultureland_pin(pin_code, session_token):
    """
    Attempts to redeem a Cultureland gift card PIN using the mobile gateway.
    Handles 16-digit (4-4-4-4) and 18-digit (4-4-4-6) PIN codes.
    Returns (success: bool, amount: int, message: str)
    """
    clean_pin = re.sub(r'[^0-9A-Za-z]', '', pin_code)
    if len(clean_pin) not in (16, 18):
        return False, 0, "문화상품권 핀번호 자릿수(16자리 또는 18자리)가 올바르지 않습니다."

    # Split pin into components
    p1 = clean_pin[0:4]
    p2 = clean_pin[4:8]
    p3 = clean_pin[8:12]
    p4 = clean_pin[12:]

    # Prepare Cultureland Mobile charge request
    url = "https://m.cultureland.co.kr/csh/cshGiftCardRegProc.do"
    post_data = urllib.parse.urlencode({
        "scrId": "cshGiftCard",
        "txtScrName": "cshGiftCard",
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4,
        "pin": f"{p1}-{p2}-{p3}-{p4}",
        "deviceToken": session_token
    }).encode('utf-8')

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918N Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
        "Referer": "https://m.cultureland.co.kr/csh/cshGiftCard.do",
        "Origin": "https://m.cultureland.co.kr",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Cookie": f"KeepLoginConfig={session_token}; LoginConfig=SavedID%3Dtrue; JSESSIONID={session_token}; WMONID={session_token}"
    }

    try:
        req = urllib.request.Request(url, data=post_data, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode('utf-8', errors='ignore')

            # Parse Cultureland response
            # Check for success indicators or amount patterns
            if "성공" in res_body or "충전완료" in res_body or "정상적으로 충전" in res_body or "resultCode\":\"0000\"" in res_body:
                # Extract amount if present, e.g., 10,000원, 30000 etc.
                amt_match = re.search(r'([0-9,]{4,})\s*원', res_body)
                detected_amt = int(amt_match.group(1).replace(',', '')) if amt_match else 0
                return True, detected_amt, "컬쳐캐쉬 충전이 성공적으로 완료되었습니다."
            
            # Known failure cases
            if "이미 사용" in res_body or "기사용한" in res_body or "기사용" in res_body:
                return False, 0, "이미 사용되었거나 사용 완료된 핀번호입니다."
            if "유효하지 않" in res_body or "번호오류" in res_body or "확인 후" in res_body or "불일치" in res_body:
                return False, 0, "유효하지 않거나 잘못된 문화상품권 핀번호입니다."
            if "로그인" in res_body or "세션" in res_body or "인증" in res_body:
                # If session token expired on Cultureland side, record warning
                return False, 0, "관리자 컬쳐랜드 세션 인증이 만료되었습니다. 관리자에게 문의하세요."

            return False, 0, "컬쳐랜드 시스템 처리 중 오류가 발생했습니다. 잠시 후 다시 시도하세요."

    except urllib.error.HTTPError as e:
        return False, 0, f"컬쳐랜드 통신 실패 (HTTP {e.code})"
    except Exception as e:
        return False, 0, f"컬쳐랜드 충전 처리 중 예외 발생: {str(e)}"

init_db()

class KeyServerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, X-Device-Id, X-Admin-Token")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def _read_body(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            if length > 0:
                raw = self.rfile.read(length).decode('utf-8')
                return json.loads(raw)
        except Exception:
            pass
        return {}

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        # 1. API: Free Key Claim (하루 2개 제한 & 1시간 쿨타임)
        if parsed.path == "/api/claim-free-key":
            return self._send_json(410, {
                "success": False,
                "discontinued": True,
                "message": "무료 키 제공 서비스가 종료되었습니다. 공식 디스코드에서 라이선스(주간권 ₩15,000 / 월간권 ₩30,000 / 영구권 ₩80,000)를 구매해 주세요."
            })

        # 1-1. API: Cultureland Voucher Instant Auto-Pay (문상 핀번호 즉시 자동결제)
        elif parsed.path == "/api/pay/cultureland":
            data = self._read_body()
            plan = data.get("plan", "").strip().lower() # 'weekly', 'monthly', 'lifetime'
            pin = data.get("pin", "").strip()
            username = data.get("username", "").strip() # optional: bind directly to user account

            plan_prices = {
                "weekly": 15000,
                "monthly": 30000,
                "lifetime": 80000
            }
            plan_durations = {
                "weekly": 7,
                "monthly": 30,
                "lifetime": 0 # 0 = permanent
            }

            if plan not in plan_prices:
                return self._send_json(400, {"success": False, "message": "올바른 플랜(주간권 / 월간권 / 영구권)을 선택하세요."})

            expected_amount = plan_prices[plan]
            clean_pin = re.sub(r'[^0-9A-Za-z]', '', pin)

            if len(clean_pin) not in (16, 18):
                return self._send_json(400, {
                    "success": False, 
                    "message": "문화상품권 핀번호는 16자리 또는 18자리여야 합니다."
                })

            # Check if this PIN was already used in our database
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id FROM cultureland_payments WHERE pin_code = ? AND status = 'success'", (clean_pin,))
            if c.fetchone():
                conn.close()
                return self._send_json(400, {
                    "success": False,
                    "message": "이미 결제에 사용된 핀번호입니다. 다른 핀번호를 입력하세요."
                })

            session_token = get_setting("cultureland_session_token", "95cd4dcf-e26e-4738-a62d-c566f9308c8c")

            # Execute recharge against Cultureland
            charge_success, charged_amt, charge_msg = charge_cultureland_pin(clean_pin, session_token)
            now = int(time.time())

            if not charge_success:
                c.execute('''
                    INSERT INTO cultureland_payments (username, plan_type, pin_code, amount_expected, amount_charged, status, response_msg, created_at)
                    VALUES (?, ?, ?, ?, ?, 'failed', ?, ?)
                ''', (username or 'guest', plan, clean_pin, expected_amount, charged_amt, charge_msg, now))
                conn.commit()
                conn.close()
                return self._send_json(400, {
                    "success": False,
                    "message": charge_msg
                })

            # Success: Generate license key
            key_prefix = "OVT-LIFE" if plan == "lifetime" else ("OVT-MTH" if plan == "monthly" else "OVT-W7D")
            issued_key = generate_key_string(prefix=key_prefix)
            dur_days = plan_durations[plan]
            expires = (now + int(dur_days * 86400)) if dur_days > 0 else 0

            # Auto-bind if username was provided and exists
            bound_user = None
            bound_at = 0
            if username:
                c.execute("SELECT username FROM users WHERE username = ?", (username,))
                urow = c.fetchone()
                if urow:
                    bound_user = urow[0]
                    bound_at = now

            c.execute('''
                INSERT INTO license_keys (key_string, key_type, duration_days, created_at, expires_at, is_active, is_used, registered_to, registered_at, note)
                VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?, ?)
            ''', (issued_key, plan, dur_days, now, expires, bound_user, bound_at, f"Auto-paid via Cultureland ₩{expected_amount:,}"))

            c.execute('''
                INSERT INTO cultureland_payments (username, plan_type, pin_code, amount_expected, amount_charged, status, key_issued, response_msg, created_at)
                VALUES (?, ?, ?, ?, ?, 'success', ?, ?, ?)
            ''', (username or 'guest', plan, clean_pin, expected_amount, charged_amt or expected_amount, issued_key, charge_msg, now))

            conn.commit()
            conn.close()

            # Relay notification to Discord if configured
            webhook_url = get_setting("discord_webhook_url", "").strip()
            if webhook_url:
                try:
                    plan_names = {"weekly": "주간권 (7일)", "monthly": "월간권 (30일)", "lifetime": "영구권 (Lifetime)"}
                    discord_payload = {
                        "username": "Ovitar Sales Bot",
                        "embeds": [{
                            "title": "💰 [OVITAR] 문화상품권 자동 결제 성공!",
                            "description": f"새로운 플랜 구매가 전자동으로 완료되었습니다.",
                            "color": 0x22c55e,
                            "fields": [
                                {"name": "구매 플랜", "value": f"**{plan_names.get(plan, plan)}** (₩{expected_amount:,}원)", "inline": True},
                                {"name": "발급 라이선스 키", "value": f"`{issued_key}`", "inline": True},
                                {"name": "등록 계정", "value": f"`@{bound_user}`" if bound_user else "미지정 (키 직접 수령)", "inline": False},
                                {"name": "핀번호(앞자리)", "value": f"`{clean_pin[:8]}********`", "inline": True},
                                {"name": "결제 일시", "value": time.strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
                            ],
                            "footer": {"text": "Ovitar Cultureland Auto-Billing Gateway"}
                        }]
                    }
                    req = urllib.request.Request(
                        webhook_url,
                        data=json.dumps(discord_payload).encode('utf-8'),
                        headers={"Content-Type": "application/json", "User-Agent": "OvitarServer/1.0"}
                    )
                    urllib.request.urlopen(req, timeout=4)
                except Exception:
                    pass

            return self._send_json(200, {
                "success": True,
                "message": "문화상품권 결제가 정상 승인되었습니다! 라이선스 키가 즉시 발급되었습니다.",
                "plan": plan,
                "key": issued_key,
                "duration_days": dur_days,
                "expires_at": expires,
                "amount": expected_amount,
                "bound_user": bound_user
            })

        # 2. API: User Register (회원가입)
        elif parsed.path == "/api/auth/register":
            data = self._read_body()
            username = data.get("username", "").strip()
            password = data.get("password", "").strip()

            if not username or not password:
                return self._send_json(400, {"success": False, "message": "아이디와 비밀번호를 입력해주세요."})
            if len(username) < 3 or len(password) < 4:
                return self._send_json(400, {"success": False, "message": "아이디는 3자 이상, 비밀번호는 4자 이상이어야 합니다."})

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'user', ?)",
                          (username, hash_pw(password), int(time.time())))
                conn.commit()
                conn.close()
                return self._send_json(200, {"success": True, "message": "회원가입이 완료되었습니다. 로그인해주세요."})
            except sqlite3.IntegrityError:
                conn.close()
                return self._send_json(400, {"success": False, "message": "이미 존재하는 아이디입니다."})

        # 3. API: User / Admin Login (로그인)
        elif parsed.path == "/api/auth/login":
            data = self._read_body()
            username = data.get("username", "").strip()
            password = data.get("password", "").strip()

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, username, role, password_hash FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            if not user or user[3] != hash_pw(password):
                conn.close()
                return self._send_json(401, {"success": False, "message": "아이디 또는 비밀번호가 일치하지 않습니다."})

            c.execute("UPDATE users SET last_login = ? WHERE id = ?", (int(time.time()), user[0]))
            conn.commit()
            conn.close()

            res_data = {
                "success": True,
                "message": f"환영합니다, {user[1]}님!",
                "username": user[1],
                "role": user[2]
            }
            if user[2] == "admin":
                res_data["admin_token"] = ADMIN_TOKEN

            return self._send_json(200, res_data)

        # 4. API: User Key Registration (사용자가 본인 계정에 키 등록/바인딩)
        elif parsed.path == "/api/user/register-key":
            data = self._read_body()
            username = data.get("username", "").strip()
            key_string = data.get("key", "").strip().upper()

            if not username or not key_string:
                return self._send_json(400, {"success": False, "message": "로그인이 필요하거나 키 정보가 누락되었습니다."})

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            if not c.fetchone():
                conn.close()
                return self._send_json(401, {"success": False, "message": "인증되지 않은 사용자입니다. 다시 로그인하세요."})

            c.execute("SELECT id, key_string, key_type, is_active, registered_to, expires_at, duration_days FROM license_keys WHERE key_string = ?", (key_string,))
            k = c.fetchone()
            if not k:
                conn.close()
                return self._send_json(404, {"success": False, "message": "존재하지 않는 라이선스 키입니다."})

            k_id, k_str, k_type, is_active, registered_to, expires_at, duration_days = k

            if not is_active:
                conn.close()
                return self._send_json(400, {"success": False, "message": "비활성화 또는 정지된 키입니다."})

            if registered_to:
                conn.close()
                if registered_to == username:
                    return self._send_json(400, {"success": False, "message": "이미 회원님 계정에 등록되어 있는 키입니다."})
                else:
                    return self._send_json(400, {"success": False, "message": f"이미 다른 계정({registered_to})에 등록된 키입니다 (중복 등록 불가)."})

            # Check key limits:
            # - Free key: max 2 (1 active + 1 extension)
            # - Unlimited/Lifetime: max 1
            is_key_free = (k_type == 'free' or k_str.startswith('FREE-') or duration_days == 0.125 or duration_days == 1)
            is_key_lifetime = (k_type == 'lifetime' or duration_days == 0 or k_str.startswith('LIFETIME-') or k_str.startswith('DEV-'))

            if is_key_free:
                c.execute("SELECT COUNT(*) FROM license_keys WHERE registered_to = ? AND (key_type = 'free' OR key_string LIKE 'FREE-%' OR duration_days <= 1)", (username,))
                free_count = c.fetchone()[0]
                if free_count >= 2:
                    conn.close()
                    return self._send_json(400, {
                        "success": False, 
                        "message": "무료 키는 최대 2개(현재 키 1개 + 연장 키 1개)까지만 등록할 수 있습니다."
                    })

            if is_key_lifetime:
                c.execute("SELECT COUNT(*) FROM license_keys WHERE registered_to = ? AND (key_type = 'lifetime' OR duration_days = 0 OR key_string LIKE 'LIFETIME-%' OR key_string LIKE 'DEV-%')", (username,))
                life_count = c.fetchone()[0]
                if life_count >= 1:
                    conn.close()
                    return self._send_json(400, {
                        "success": False, 
                        "message": "무제한(영구) 키는 계정당 1개만 등록할 수 있습니다."
                    })

            now = int(time.time())
            c.execute("UPDATE license_keys SET registered_to = ?, registered_at = ? WHERE id = ?", (username, now, k_id))
            conn.commit()
            conn.close()

            return self._send_json(200, {
                "success": True,
                "message": f"키가 계정({username})에 성공적으로 등록되었습니다!",
                "key": k_str,
                "type": k_type,
                "registered_to": username
            })

        # API: User Remove Key
        elif parsed.path == "/api/user/remove-key":
            data = self._read_body()
            username = data.get("username", "").strip()
            key_id = data.get("key_id")
            if not username or not key_id:
                return self._send_json(400, {"success": False, "message": "필수 파라미터가 누락되었습니다."})

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id FROM license_keys WHERE id = ? AND registered_to = ?", (key_id, username))
            if not c.fetchone():
                conn.close()
                return self._send_json(404, {"success": False, "message": "해당 계정에 등록된 키를 찾을 수 없습니다."})

            c.execute("UPDATE license_keys SET registered_to = NULL, registered_at = 0 WHERE id = ?", (key_id,))
            conn.commit()
            conn.close()

            return self._send_json(200, {"success": True, "message": "키가 계정에서 성공적으로 해제되었습니다."})

        # API: Hardware Reset (일주일에 1회 제한)
        elif parsed.path == "/api/user/reset-hwid":
            data = self._read_body()
            username = data.get("username", "").strip()
            if not username:
                return self._send_json(400, {"success": False, "message": "사용자 이름이 필요합니다."})

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, last_hwid_reset FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            if not user:
                conn.close()
                return self._send_json(404, {"success": False, "message": "존재하지 않는 사용자입니다."})

            user_id, last_reset = user
            last_reset = last_reset or 0
            now = int(time.time())
            ONE_WEEK = 7 * 86400

            if now - last_reset < ONE_WEEK:
                remaining_sec = ONE_WEEK - (now - last_reset)
                rem_days = remaining_sec // 86400
                rem_hours = (remaining_sec % 86400) // 3600
                rem_mins = (remaining_sec % 3600) // 60
                conn.close()
                return self._send_json(400, {
                    "success": False,
                    "message": f"하드웨어 리셋은 일주일에 1회만 가능합니다. 남은 대기 시간: {rem_days}일 {rem_hours}시간 {rem_mins}분"
                })

            c.execute("UPDATE license_keys SET hwid = NULL WHERE registered_to = ?", (username,))
            affected = c.rowcount
            c.execute("UPDATE users SET last_hwid_reset = ? WHERE id = ?", (now, user_id))
            conn.commit()
            conn.close()

            return self._send_json(200, {
                "success": True,
                "message": f"하드웨어 정보가 성공적으로 초기화되었습니다! (초기화된 키: {affected}개)",
                "last_hwid_reset": now
            })

        # 5. API: Admin Key Generation
        elif parsed.path in ["/api/dev/generate-key", "/api/admin/generate-keys"]:
            data = self._read_body()
            key_type = data.get("type") or data.get("key_type") or "dev"
            days = float(data.get("days", 0))
            count = int(data.get("count", 1))
            note = data.get("note", "Admin Console")
            
            prefix = "DEV" if key_type == "dev" else ("LIFETIME" if days == 0 else ("FREE" if key_type == "free" else "OVT"))
            created_keys = []
            now = int(time.time())

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            for _ in range(count):
                new_key = generate_key_string(prefix=prefix)
                if key_type == "free":
                    expires = now + 10800 # 3h
                    duration = 0.125
                else:
                    expires = (now + int(days * 86400)) if days > 0 else 0
                    duration = days

                c.execute('''
                    INSERT INTO license_keys (key_string, key_type, duration_days, created_at, expires_at, is_active, is_used, note)
                    VALUES (?, ?, ?, ?, ?, 1, 0, ?)
                ''', (new_key, key_type, duration, now, expires, note))
                created_keys.append(new_key)

            conn.commit()
            conn.close()

            return self._send_json(200, {
                "success": True,
                "keys": created_keys,
                "type": key_type,
                "duration_days": days,
                "note": note
            })

        # 6. API: Admin Key Management
        elif parsed.path == "/api/admin/manage-key":
            data = self._read_body()
            key_id = data.get("key_id")
            action = data.get("action")

            if not key_id or not action:
                return self._send_json(400, {"success": False, "message": "key_id and action required"})

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            if action == 'reset_hwid':
                c.execute("UPDATE license_keys SET hwid = NULL WHERE id = ?", (key_id,))
                msg = "HWID 기기 바인딩이 초기화되었습니다."
            elif action == 'unbind_user':
                c.execute("UPDATE license_keys SET registered_to = NULL, registered_at = 0 WHERE id = ?", (key_id,))
                msg = "계정 연동이 성공적으로 해제되었습니다."
            elif action == 'toggle_active':
                c.execute("UPDATE license_keys SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (key_id,))
                msg = "키 활성/비활성 상태가 변경되었습니다."
            elif action == 'delete':
                c.execute("DELETE FROM license_keys WHERE id = ?", (key_id,))
                msg = "라이선스 키가 영구 삭제되었습니다."
            else:
                conn.close()
                return self._send_json(400, {"success": False, "message": "Unknown action"})

            conn.commit()
            conn.close()
            return self._send_json(200, {"success": True, "message": msg})

        # 7-UPLOAD. API: Admin Direct Large File Script Upload (Streaming)
        elif parsed.path == "/api/admin/script/upload":
            admin_token = self.headers.get("X-Admin-Token", "").strip()
            if admin_token != ADMIN_TOKEN:
                return self._send_json(403, {"success": False, "message": "관리자 인증 토큰이 유효하지 않습니다."})

            content_len = int(self.headers.get("Content-Length", 0))
            if content_len <= 0:
                return self._send_json(400, {"success": False, "message": "업로드할 데이터가 비어 있습니다."})

            raw_filename = self.headers.get("X-File-Name", "main_script.lua")
            filename = urllib.parse.unquote(raw_filename)
            if not filename:
                filename = "main_script.lua"

            os.makedirs(SCRIPTS_DIR, exist_ok=True)
            hasher = hashlib.sha256()
            line_count = 0
            bytes_received = 0

            with open(MAIN_SCRIPT_PATH, "wb") as f_out:
                remaining = content_len
                while remaining > 0:
                    chunk_size = min(remaining, 65536)
                    chunk = self.rfile.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    hasher.update(chunk)
                    line_count += chunk.count(b'\n')
                    remaining -= len(chunk)
                    bytes_received += len(chunk)

            file_size = os.path.getsize(MAIN_SCRIPT_PATH)
            checksum = hasher.hexdigest()
            now_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            set_setting("script_file_name", filename)
            set_setting("script_file_size", str(file_size))
            set_setting("script_line_count", str(line_count + 1))
            set_setting("script_checksum", checksum)
            set_setting("script_updated_at", now_str)
            set_setting("script_source_type", "file")
            set_setting("script_content", f"-- [DEPLOYED FILE: {filename} ({file_size:,} bytes) at {now_str}]")

            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"

            return self._send_json(200, {
                "success": True,
                "message": f"대용량 스크립트 파일이 성공적으로 배포되었습니다! ({size_str})",
                "filename": filename,
                "file_size": file_size,
                "file_size_formatted": size_str,
                "line_count": line_count + 1,
                "checksum": checksum[:12] + "...",
                "updated_at": now_str
            })

        # 7. API: Admin Script & API Status Control
        elif parsed.path == "/api/admin/script":
            data = self._read_body()
            if "api_status" in data:
                set_setting("api_status", data["api_status"]) # 'online', 'maintenance', 'offline'
            if "api_message" in data:
                set_setting("api_message", data["api_message"])
            if "script_version" in data:
                set_setting("script_version", data["script_version"])
            if "script_content" in data:
                c = data["script_content"]
                if not c.startswith("-- [[ 🚀 OVITAR HIGH-PERFORMANCE FILE DEPLOYMENT MODE ]]"):
                    save_main_script(c, "inline_script.lua")
            if "fake_script_content" in data:
                save_fake_script(data["fake_script_content"])
            if "discord_webhook_url" in data:
                set_setting("discord_webhook_url", data["discord_webhook_url"])

            return self._send_json(200, {
                "success": True,
                "message": "스크립트, 가짜 미끼 코드 및 웹훅 설정이 성공적으로 저장되었습니다!",
                "api_status": get_setting("api_status", "online"),
                "api_message": get_setting("api_message", "정상 서비스 중"),
                "script_version": get_setting("script_version", "v0.6.0")
            })

        # 7-0. API: Admin Cultureland Settings & Test Charge
        elif parsed.path == "/api/admin/cultureland":
            data = self._read_body()
            if "cultureland_session_token" in data:
                new_token = data["cultureland_session_token"].strip()
                set_setting("cultureland_session_token", new_token)

            action = data.get("action")
            if action == "test_charge":
                test_pin = data.get("pin", "").strip()
                token = get_setting("cultureland_session_token", "95cd4dcf-e26e-4738-a62d-c566f9308c8c")
                suc, amt, msg = charge_cultureland_pin(test_pin, token)
                return self._send_json(200, {
                    "success": suc,
                    "amount": amt,
                    "message": msg,
                    "token": token
                })

            return self._send_json(200, {
                "success": True,
                "message": "컬쳐랜드 연동 토큰이 성공적으로 저장되었습니다!",
                "cultureland_session_token": get_setting("cultureland_session_token", "")
            })

        # 7-1. API: Safe Webhook Relay (서버 프록시 경유로 Discord Webhook 주소 노출 방지 & 스팸 방어)
        elif parsed.path == "/api/webhook/relay":
            data = self._read_body()
            event_type = data.get("event", "Log")
            event_msg = data.get("message", "Activity logged")
            username = data.get("username", "Unknown")
            hwid = data.get("hwid", "Unknown")
            webhook_url = get_setting("discord_webhook_url", "").strip()

            if not webhook_url:
                return self._send_json(200, {"success": True, "relayed": False, "note": "Webhook URL not configured"})

            # Forward to Discord safely from server
            try:
                embed_color = 0x4ade80 if "Success" in event_type else (0xfacc15 if "Warning" in event_type else 0xf87171)
                discord_payload = {
                    "username": "Ovitar Shield Logger",
                    "embeds": [{
                        "title": f"🛡️ [Ovitar Security] {event_type}",
                        "description": event_msg,
                        "color": embed_color,
                        "fields": [
                            {"name": "User", "value": username, "inline": True},
                            {"name": "HWID / Machine", "value": hwid, "inline": True},
                            {"name": "Server Time", "value": time.strftime("%Y-%m-%d %H:%M:%S"), "inline": False}
                        ],
                        "footer": {"text": "Protected by Ovitar Server-Side Relay Shield"}
                    }]
                }
                req = urllib.request.Request(
                    webhook_url,
                    data=json.dumps(discord_payload).encode('utf-8'),
                    headers={"Content-Type": "application/json", "User-Agent": "OvitarRelay/2.0"}
                )
                urllib.request.urlopen(req, timeout=5)
                return self._send_json(200, {"success": True, "relayed": True})
            except Exception as e:
                return self._send_json(200, {"success": False, "error": str(e)})

        # 8. API: Roblox Loader Authentication & Script Delivery
        elif parsed.path == "/api/loader/auth":
            data = self._read_body()
            username = data.get("username", "").strip()
            password = data.get("password", "").strip()
            hwid = data.get("hwid", "").strip()

            api_status = get_setting("api_status", "online")
            api_message = get_setting("api_message", "정상 서비스 중")
            script_version = get_setting("script_version", "v0.6.0")

            if api_status == "maintenance":
                return self._send_json(503, {
                    "success": False,
                    "status": "maintenance",
                    "message": f"현재 스크립트 서버 점검 중입니다. ({api_message})"
                })
            elif api_status == "offline":
                return self._send_json(503, {
                    "success": False,
                    "status": "offline",
                    "message": "현재 스크립트 서비스가 비활성화(오프라인) 상태입니다."
                })

            if not username or not password:
                return self._send_json(400, {
                    "success": False,
                    "status": api_status,
                    "message": "아이디와 비밀번호를 모두 입력해주세요."
                })

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, username, role, password_hash FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            if not user or user[3] != hash_pw(password):
                conn.close()
                return self._send_json(401, {
                    "success": False,
                    "status": api_status,
                    "message": "아이디 또는 비밀번호가 올바르지 않습니다."
                })

            user_id, uname, role, _ = user

            # Find active license key for this user
            now = int(time.time())
            c.execute('''
                SELECT id, key_string, key_type, duration_days, expires_at, is_active, hwid 
                FROM license_keys 
                WHERE registered_to = ? AND is_active = 1
                ORDER BY duration_days ASC, id DESC
            ''', (uname,))
            keys = c.fetchall()

            valid_key = None
            for k in keys:
                k_id, k_str, k_type, dur_days, exp, active, db_hwid = k
                if exp != 0 and exp < now:
                    continue # Expired
                valid_key = k
                break

            if not valid_key:
                conn.close()
                return self._send_json(403, {
                    "success": False,
                    "status": api_status,
                    "message": "계정에 등록된 유효한 라이선스 키가 없습니다. 웹사이트에서 키를 발급/등록해주세요."
                })

            k_id, k_str, k_type, dur_days, exp, active, db_hwid = valid_key

            # HWID Check & Auto-bind (Admins and freshly reset keys auto-bind smoothly)
            hwid_clean = (hwid or "").strip()
            db_hwid_clean = (db_hwid or "").strip()

            if role == "admin":
                # Admin account can always log in and will update the active HWID to the current machine
                if hwid_clean and db_hwid_clean != hwid_clean:
                    c.execute("UPDATE license_keys SET hwid = ?, is_used = 1 WHERE id = ?", (hwid_clean, k_id))
                    conn.commit()
            elif not db_hwid_clean and hwid_clean:
                # First login or after Hardware Reset on website
                c.execute("UPDATE license_keys SET hwid = ?, is_used = 1 WHERE id = ?", (hwid_clean, k_id))
                conn.commit()
            elif db_hwid_clean and hwid_clean and db_hwid_clean != hwid_clean:
                conn.close()
                return self._send_json(403, {
                    "success": False,
                    "status": api_status,
                    "message": "하드웨어 정보가 등록된 기기와 일치하지 않습니다. 웹사이트에서 '하드웨어 리셋'을 진행하세요."
                })
            else:
                c.execute("UPDATE license_keys SET is_used = 1 WHERE id = ?", (k_id,))
                conn.commit()

            c.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
            conn.commit()
            conn.close()

            # Fetch script content & Encrypt payload so raw text is never exposed
            script_payload = get_main_script()
            fake_payload = get_fake_script()
            nonce = secrets.token_hex(8)
            encrypted_payload = encrypt_payload(script_payload, salt=nonce)
            encrypted_fake = encrypt_payload(fake_payload, salt=nonce)

            tier_name = "lifetime" if dur_days == 0 else ("free" if dur_days <= 1 else f"{int(dur_days)}d")

            return self._send_json(200, {
                "success": True,
                "status": api_status,
                "username": uname,
                "role": role,
                "license_tier": tier_name,
                "key": k_str,
                "version": script_version,
                "message": f"인증 성공! 환영합니다, {uname}님.",
                "encrypted": True,
                "nonce": nonce,
                "payload": encrypted_payload,
                "fake_payload": encrypted_fake,
                "script": "-- [PROTECTED BY OVITAR SECURITY SHIELD] RAW SOURCE MASKED"
            })

        super().do_POST()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # Block direct browser access to .lua files (show cool cyber shield instead of raw code)
        if parsed.path.endswith(".lua"):
            ua = self.headers.get("User-Agent", "").lower()
            accept = self.headers.get("Accept", "").lower()
            if "mozilla" in ua or "chrome" in ua or "safari" in ua or "edge" in ua or "text/html" in accept:
                self.send_response(403)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><title>403 Forbidden - OVITAR Security</title><style>body{background:#0a0a0d;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}.c{background:#141418;border:1px solid #282834;border-radius:20px;padding:40px;text-align:center;max-width:440px;box-shadow:0 20px 40px rgba(0,0,0,0.5);}.b{background:rgba(239,68,68,0.15);color:#f87171;padding:6px 14px;border-radius:99px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:16px;}</style></head><body><div class="c"><div class="b">🛡️ OVITAR API SHIELD ACTIVE</div><h2 style="margin:0 0 12px 0;">직접 링크 접근이 차단되었습니다</h2><p style="color:#889;font-size:13.5px;line-height:1.6;margin:0 0 20px 0;">보안 규정에 따라 브라우저를 통한 원본 스크립트 직접 열람이 엄격히 통제됩니다.<br>로블록스 익스큐터 로더를 통해 실행하세요.</p><a href="/" style="background:#fff;color:#000;text-decoration:none;padding:10px 22px;border-radius:99px;font-size:13px;font-weight:700;display:inline-block;">홈페이지로 이동</a></div></body></html>"""
                self.wfile.write(html.encode('utf-8'))
                return

        # Direct GET to loader auth is prohibited
        if parsed.path == "/api/loader/auth":
            return self._send_json(403, {
                "success": False,
                "message": "🛡️ [OVITAR SHIELD] 직접 링크 접근이 차단되었습니다. (POST Only)"
            })

        # Loader API Status (로블록스 로더 및 사이트에서 상태 조회: online, maintenance, offline)
        if parsed.path == "/api/loader/status":
            api_status = get_setting("api_status", "online")
            api_message = get_setting("api_message", "정상 서비스 중")
            script_version = get_setting("script_version", "v0.6.0")
            return self._send_json(200, {
                "status": api_status, # 'online' (🟢), 'maintenance' (🟡), 'offline' (🔴)
                "message": api_message,
                "version": script_version,
                "time": int(time.time())
            })

        # Heartbeat Keep-Alive Check (스크립트 실시간 생존 및 서버 상태 점검)
        elif parsed.path == "/api/loader/heartbeat":
            api_status = get_setting("api_status", "online")
            return self._send_json(200, {
                "alive": api_status == "online",
                "status": api_status,
                "timestamp": int(time.time())
            })

        # Admin API: Download Main Deployed Script File
        elif parsed.path == "/api/admin/script/download":
            admin_token = self.headers.get("X-Admin-Token", "").strip()
            query = urllib.parse.parse_qs(parsed.query)
            token_in_query = query.get("token", [""])[0]
            if admin_token != ADMIN_TOKEN and token_in_query != ADMIN_TOKEN:
                return self._send_json(403, {"success": False, "message": "다운로드 권한이 없습니다."})

            if not os.path.exists(MAIN_SCRIPT_PATH):
                return self._send_json(404, {"success": False, "message": "배포된 스크립트 파일이 없습니다."})

            file_size = os.path.getsize(MAIN_SCRIPT_PATH)
            filename = get_setting("script_file_name", "main_script.lua")

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(file_size))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with open(MAIN_SCRIPT_PATH, "rb") as f_in:
                while True:
                    chunk = f_in.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            return

        # Admin Script & Settings fetch (보호됨: 직접 링크 접속 시 원본 소스코드 절대 노출 차단)
        elif parsed.path == "/api/admin/script":
            admin_token = self.headers.get("X-Admin-Token", "").strip()
            if admin_token != ADMIN_TOKEN:
                return self._send_json(200, {
                    "api_status": get_setting("api_status", "online"),
                    "api_message": "🛡️ [OVITAR SHIELD] 직접 링크 접속이 차단되었습니다. 관리자 콘솔을 통해 인증 후 열람하세요.",
                    "script_version": get_setting("script_version", "v0.6.0"),
                    "script_content": "-- [OVITAR SECURITY SHIELD] 원본 스크립트 직접 열람이 차단되었습니다. 관리자 패널에 로그인하여 확인하세요.",
                    "fake_script_content": "-- [OVITAR SHIELD] Decoy protected."
                })

            main_script_content = get_main_script()
            raw_encoded = main_script_content.encode('utf-8')
            file_size = len(raw_encoded)
            filename = get_setting("script_file_name", "main_script.lua")
            updated_at = get_setting("script_updated_at", "")

            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"

            lines = main_script_content.splitlines()
            line_count = len(lines)
            is_large = file_size > 49152  # 48KB threshold for safe browser rendering

            if is_large:
                preview = "\n".join(lines[:80])
                display_content = (
                    f"-- [[ 🚀 OVITAR HIGH-PERFORMANCE FILE DEPLOYMENT MODE ]]\n"
                    f"-- 파일명: {filename} ({size_str} / {line_count:,} 줄)\n"
                    f"-- 최근 배포: {updated_at}\n"
                    f"-- [안내] 브라우저 프리징(DDoS 현상)을 방지하기 위해 상위 80줄 미리보기만 표시됩니다.\n"
                    f"-- 전체 코드는 서버 파일(scripts/{filename})에 안전하게 보관 중이며 게임 내 로더에서 정상 작동합니다.\n\n"
                    + preview
                    + f"\n\n-- ... [추가 {line_count - 80:,} 줄 생략됨] ...\n"
                    f"-- [팁] '현재 배포 파일 다운로드' 버튼으로 원본 전문을 확인하거나, 위 파일 업로더로 언제든 교체할 수 있습니다."
                )
            else:
                display_content = main_script_content

            return self._send_json(200, {
                "api_status": get_setting("api_status", "online"),
                "api_message": get_setting("api_message", "정상 서비스 중"),
                "script_version": get_setting("script_version", "v0.6.0"),
                "script_content": display_content,
                "is_large_file": is_large,
                "file_name": filename,
                "file_size": file_size,
                "file_size_formatted": size_str,
                "line_count": line_count,
                "updated_at": updated_at,
                "fake_script_content": get_fake_script(),
                "discord_webhook_url": get_setting("discord_webhook_url", "")
            })

        # Admin API: Fetch all keys & stats (보호됨)
        elif parsed.path == "/api/admin/keys":
            admin_token = self.headers.get("X-Admin-Token", "").strip()
            if admin_token != ADMIN_TOKEN:
                return self._send_json(403, {
                    "success": False,
                    "message": "🛡️ [OVITAR SHIELD] 직접 링크 접근이 차단되었습니다. 관리자 콘솔에서 로그인해주세요."
                })

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''
                SELECT id, key_string, key_type, duration_days, created_at, expires_at, is_active, is_used, hwid, claimed_by_ip, registered_to, registered_at, note
                FROM license_keys ORDER BY id DESC
            ''')
            keys = [dict(row) for row in c.fetchall()]

            c.execute("SELECT id, username, role, created_at, last_login, last_hwid_reset FROM users ORDER BY id DESC")
            users = [dict(row) for row in c.fetchall()]

            now = int(time.time())
            c.execute("SELECT COUNT(*) FROM free_key_claims WHERE claimed_at > ?", (now - 86400,))
            free_claims_24h = c.fetchone()[0]

            # Cultureland Payment Stats
            c.execute("SELECT id, username, plan_type, pin_code, amount_expected, amount_charged, status, key_issued, response_msg, created_at FROM cultureland_payments ORDER BY id DESC LIMIT 50")
            cultureland_logs = [dict(row) for row in c.fetchall()]

            c.execute("SELECT COALESCE(SUM(amount_charged), 0) FROM cultureland_payments WHERE status = 'success'")
            total_cultureland_revenue = c.fetchone()[0]

            conn.close()

            return self._send_json(200, {
                "success": True,
                "total_keys": len(keys),
                "total_users": len(users),
                "free_claims_24h": free_claims_24h,
                "api_status": get_setting("api_status", "online"),
                "script_version": get_setting("script_version", "v0.6.0"),
                "cultureland_session_token": get_setting("cultureland_session_token", "95cd4dcf-e26e-4738-a62d-c566f9308c8c"),
                "total_cultureland_revenue": total_cultureland_revenue,
                "cultureland_logs": cultureland_logs,
                "keys": keys,
                "users": users
            })

        # User API: Fetch keys registered to current user
        elif parsed.path == "/api/user/my-keys":
            query = urllib.parse.parse_qs(parsed.query)
            username = query.get("username", [""])[0].strip()
            if not username:
                return self._send_json(400, {"success": False, "message": "username parameter required"})

            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('''
                SELECT id, key_string, key_type, duration_days, created_at, expires_at, is_active, is_used, hwid, registered_at, note
                FROM license_keys WHERE registered_to = ? ORDER BY id DESC
            ''', (username,))
            keys = [dict(row) for row in c.fetchall()]
            conn.close()

            return self._send_json(200, {"success": True, "username": username, "keys": keys})

        super().do_GET()

if __name__ == "__main__":
    init_db()
    ThreadingHTTPServer.allow_reuse_address = True
    with ThreadingHTTPServer(("0.0.0.0", PORT), KeyServerHandler) as httpd:
        print(f"[OVITAR] Key Server running with ThreadingHTTPServer engine at http://127.0.0.1:{PORT}")
        httpd.serve_forever()
