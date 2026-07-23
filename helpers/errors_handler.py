from typing import Dict, Any, Tuple

# Penanganan Kode Penutupan Koneksi WebSocket SOT 4xxx
WS_CLOSE_CODES: Dict[int, Dict[str, Any]] = {
 1000: {"error": "CLEAN_EXIT", "retry": False, "desc": "Game ended normally."},
 1011: {"error": "INTERNAL_SERVER_ERROR", "retry": True, "backoff": 5.0, "desc": "Server encountered an error. Reconnect with backoff."},
 1013: {"error": "TRY_AGAIN_LATER", "retry": True, "backoff": 2.0, "desc": "Transient condition. Reconnect with backoff."},
 4001: {"error": "READINESS_BLOCKED", "retry": False, "desc": "Failed eligibility check. Inspect welcome.readiness.missing[]."},
 4002: {"error": "ENTRYTYPE_NOT_PERMITTED", "retry": False, "desc": "Entry type not allowed. Check welcome.decision."},
 4003: {"error": "HELLO_TIMEOUT_OR_IP_LIMIT", "retry": False, "desc": "Handshake timed out or exceeded IP limit (Max 5 agents per IP)."},
 4004: {"error": "INVALID_HELLO", "retry": False, "desc": "Handshake hello frame format was invalid."},
 4005: {"error": "SIGN_TIMEOUT", "retry": True, "backoff": 1.0, "desc": "EIP-712 signature collection timed out."},
 4006: {"error": "INVALID_SIGNATURE", "retry": False, "desc": "Failed to recover Agent EOA signer address from signature."},
 4030: {"error": "WEB_SESSION_ACTIVE", "retry": True, "backoff": 60.0, "desc": "Web session active; owner holds control. Back off >=60s."},
 4503: {"error": "SERVICE_UNAVAILABLE", "retry": True, "backoff": 10.0, "desc": "Gateway under maintenance, Redis flap, or outage."}
}

MAX_AGENTS_PER_IP: int = 5

def parse_rest_error(response_json: Dict[str, Any]) -> Tuple[str, str]:
 """
 Mengurai bentuk respon error standard REST API.
 Mengembalikan tuple (error_code, error_message).
 """
 error_obj = response_json.get("error", {})
 code = error_obj.get("code", "UNKNOWN_ERROR")
 message = error_obj.get("message", "An unspecified error occurred.")
 return code, message

def get_reconnection_strategy(close_code: int) -> Tuple[bool, float]:
 """
 Menentukan apakah koneksi harus diulang beserta durasi jeda backoff-nya.
 """
 code_info = WS_CLOSE_CODES.get(close_code)
 if not code_info:
  return True, 1.0 # Ulangi secara default untuk kode yang tidak dikenal
 return code_info["retry"], code_info.get("backoff", 0.0)