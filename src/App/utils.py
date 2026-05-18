import os
import re
import unicodedata
from urllib.parse import urlparse

from flask import request

_EXTENSION_RE = re.compile(r'^[A-Za-z0-9]{1,16}$')
_FILENAME_BAD_CHARS = re.compile(r'[\\/\x00-\x1f<>:"|?*]')


def sanitize_extension(raw):
    if not raw:
        return ''
    raw = raw.strip().lower()
    if _EXTENSION_RE.match(raw):
        return raw
    return ''


def sanitize_display_name(raw, fallback='file'):
    if not raw:
        return fallback
    name = unicodedata.normalize('NFC', raw)
    name = _FILENAME_BAD_CHARS.sub('_', name)
    name = name.strip().lstrip('.').rstrip('.')
    if not name or name in {'.', '..'}:
        return fallback
    return name[:255]


def split_extension(filename):
    name = sanitize_display_name(filename)
    parts = name.rsplit('.', 1)
    if len(parts) == 2 and _EXTENSION_RE.match(parts[1]):
        return name, parts[1].lower()
    return name, ''


def safe_int(value, default=None, minimum=None, maximum=None):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None and n < minimum:
        return default
    if maximum is not None and n > maximum:
        return default
    return n


def safe_next_url(target):
    if not target or not isinstance(target, str):
        return None
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return None
    if not target.startswith('/'):
        return None
    if target.startswith('//'):
        return None
    return target


def is_safe_uploads_path(uploads_dir, disk_name):
    uploads_dir = os.path.realpath(uploads_dir)
    full = os.path.realpath(os.path.join(uploads_dir, disk_name))
    return os.path.commonpath([uploads_dir, full]) == uploads_dir
