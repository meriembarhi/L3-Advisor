# utils/export.py
import io

def generate_audit_log(messages):
    output = io.StringIO()
    output.write("=== L3-ADVISOR INCIDENT AUDIT LOG ===\n\n")
    for msg in messages:
        role = msg['role'].upper()
        output.write(f"[{role}]: {msg['content']}\n")
        output.write("-" * 30 + "\n")
    return output.getvalue()