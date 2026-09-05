import re
import html

# Patterns commonly used in prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)",
    r"system\s+prompt\s*:",
    r"system\s+instruction\s*:",
    r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|unrestricted|jailbreak)",
    r"\[\s*INST\s*\]",
    r"\[\s*/\s*INST\s*\]",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\|endoftext\|>",
    r"###\s*instruction\s*:",
    r"###\s*system\s*:"
]

COMPILED_INJECTIONS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def sanitise_text(raw_text: str) -> str:
    """
    Sanitises untrusted text from enquiry message bodies or attachments.
    - Strips dangerous HTML tags and scripts
    - Neutralizes known prompt injection phrases
    - Cleans control characters and zero-width spaces
    - Normalizes unicode whitespace
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Strip null bytes and zero-width characters
    zero_width_chars = ["\x00", "\u200B", "\u200C", "\u200D", "\uFEFF"]
    for ch in zero_width_chars:
        text = text.replace(ch, "")

    # 2. Strip HTML tags like <script>...</script>, <style>...</style>
    text = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<\s*style[^>]*>.*?<\s*/\s*style\s*>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Strip remaining HTML tags (leaving tag content)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)

    # 3. Defuse prompt injection sequences
    for pattern in COMPILED_INJECTIONS:
        text = pattern.sub("[INJECTION_DEFUSED]", text)

    # 4. Clean excessive horizontal whitespace while preserving newlines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines).strip()

    return text
