"""
Architecture diagram generator for CloudAttend.

Uses official AWS icons from the `diagrams` Python package if installed,
otherwise falls back to AWS-brand-coloured shapes drawn with Pillow only.

Install icons (no Graphviz needed):
    pip install diagrams

Run:
    python docs/generate_diagram.py

Output:
    docs/architecture.png
"""
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 1300, 820
img = Image.new("RGB", (W, H), "#f8fafc")
d   = ImageDraw.Draw(img)


# ── Fonts ─────────────────────────────────────────────────────────────────────
def font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf"  if not bold else "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arial.ttf"    if not bold else "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


F_HEAD  = font(13, bold=True)
F_SMALL = font(10)
F_HUGE  = font(28, bold=True)

# ── AWS brand colours ─────────────────────────────────────────────────────────
AWS_SQUID   = "#232F3E"
AWS_ORANGE  = "#FF9900"
AURORA_COL  = "#C7131F"
VPC_COL     = "#8C4FFF"
EB_COL      = "#FF9900"
GH_COL      = "#24292F"
CF_COL      = "#E7157B"
S3_COL      = "#3F8624"
SMTP_COL    = "#8b5cf6"
BROWSER_COL = "#22c55e"
BORDER_L    = "#E2E8F0"
TEXT_D      = "#0F172A"
TEXT_M      = "#475569"


# ── Official AWS icon loader ───────────────────────────────────────────────────
_ICON_CACHE: dict = {}


def _diagrams_icons_root() -> str | None:
    """
    Return the AWS icon resources root used by the `diagrams` package.

    The `diagrams` package stores icons in site-packages/resources/aws/
    (a sibling of the diagrams package, not inside it).  We discover the
    exact path by reading the class attribute set on each Node class.
    """
    try:
        import site
        import diagrams.aws.compute as _c
        icon_dir = getattr(_c.ElasticBeanstalk, '_icon_dir', '')  # 'resources/aws/compute'
        if not icon_dir:
            return None
        # Strip the sub-category ('compute') to get the AWS icons root
        aws_root_rel = '/'.join(icon_dir.rstrip('/').split('/')[:-1])  # 'resources/aws'
        for sp in site.getsitepackages():
            candidate = os.path.join(sp, aws_root_rel)
            if os.path.isdir(candidate):
                return candidate
        return None
    except (ImportError, AttributeError):
        return None


def _load_aws_icon(relative_path: str, size: int = 48) -> Image.Image | None:
    """
    Load an AWS icon from the `diagrams` package.

    `relative_path` is like 'compute/elastic-beanstalk.png'.  A case-insensitive
    and substring search is performed so minor version differences don't matter.
    Returns a Pillow RGBA Image or None.
    """
    key = f"{relative_path}@{size}"
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    root = _diagrams_icons_root()
    if not root:
        _ICON_CACHE[key] = None
        return None

    parts = relative_path.split("/", 1)
    if len(parts) != 2:
        _ICON_CACHE[key] = None
        return None

    cat_dir = os.path.join(root, parts[0])
    if not os.path.isdir(cat_dir):
        # Try case-insensitive category match
        low = parts[0].lower()
        for entry in os.listdir(root):
            if entry.lower() == low and os.path.isdir(os.path.join(root, entry)):
                cat_dir = os.path.join(root, entry)
                break
        else:
            _ICON_CACHE[key] = None
            return None

    target = parts[1].lower()
    keyword = target.replace(".png", "").replace("-", "").replace("_", "")
    found = None
    for fname in os.listdir(cat_dir):
        if fname.lower() == target:
            found = os.path.join(cat_dir, fname)
            break
        fkey = fname.lower().replace("-", "").replace("_", "").replace(".png", "")
        if keyword in fkey:
            found = os.path.join(cat_dir, fname)

    if not found:
        _ICON_CACHE[key] = None
        return None

    try:
        ico = Image.open(found).convert("RGBA").resize((size, size), Image.LANCZOS)
        _ICON_CACHE[key] = ico
        return ico
    except Exception as e:
        print(f"[warn] icon load failed {found}: {e}", file=sys.stderr)
        _ICON_CACHE[key] = None
        return None


# ── Drawing helpers ───────────────────────────────────────────────────────────
def rrect(box, radius=10, fill="#fff", outline="#ccc", width=2):
    d.rounded_rectangle(list(box), radius=radius, fill=fill, outline=outline, width=width)


def paste_icon(icon: Image.Image, cx: int, cy: int):
    x, y = cx - icon.width // 2, cy - icon.height // 2
    img.paste(icon, (x, y), icon)


def badge(cx, cy, r, color, text):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.text((cx, cy), text, font=font(11, bold=True), fill="#fff", anchor="mm")


def service_box(cx, cy, w, h, icon_path, icon_color, label,
                sublabel="", extra_lines=(), icon_size=48):
    bx0, by0, bx1, by1 = cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2
    rrect([bx0, by0, bx1, by1], radius=10, fill="#ffffff", outline=icon_color, width=2)

    icon_top = by0 + 8
    icon_cy = icon_top + icon_size // 2

    ico = _load_aws_icon(icon_path, size=icon_size) if icon_path else None
    if ico:
        paste_icon(ico, cx, icon_cy)
    else:
        badge(cx, icon_cy, icon_size // 2, icon_color, label[:2].upper())

    ty = icon_top + icon_size + 10
    d.text((cx, ty), label, font=F_HEAD, fill=TEXT_D, anchor="mm")
    if sublabel:
        ty += 15; d.text((cx, ty), sublabel, font=F_SMALL, fill=TEXT_M, anchor="mm")
    for line in extra_lines:
        ty += 13; d.text((cx, ty), line, font=F_SMALL, fill=TEXT_M, anchor="mm")
    return bx0, by0, bx1, by1


def arrow(x0, y0, x1, y1, color="#64748b", label="", dashed=False):
    import math
    if dashed:
        steps = max(abs(x1 - x0), abs(y1 - y0))
        n = max(steps // 12, 1)
        for i in range(n):
            t0, t1 = i / n, (i + 0.5) / n
            d.line([(x0 + (x1-x0)*t0, y0+(y1-y0)*t0),
                    (x0 + (x1-x0)*t1, y0+(y1-y0)*t1)], fill=color, width=2)
    else:
        d.line([(x0, y0), (x1, y1)], fill=color, width=2)
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    if ln:
        ux, uy = dx / ln, dy / ln
        sz = 8
        d.polygon([(x1, y1),
                   (x1 - sz*ux + sz*.4*uy, y1 - sz*uy - sz*.4*ux),
                   (x1 - sz*ux - sz*.4*uy, y1 - sz*uy + sz*.4*ux)], fill=color)
    if label:
        d.text(((x0+x1)//2 + 4, (y0+y1)//2 - 10), label, font=F_SMALL, fill=color)


# ══════════════════════════════════════════════════════════════════════════════
# Startup info
# ══════════════════════════════════════════════════════════════════════════════
_icons_root = _diagrams_icons_root()
if _icons_root:
    print(f"[info] Official AWS icons found at: {_icons_root}")
else:
    print("[info] `diagrams` package not installed — using brand-colour fallback.")
    print("       Run: pip install diagrams   to get official AWS icons.")

# ══════════════════════════════════════════════════════════════════════════════
# Title bar
# ══════════════════════════════════════════════════════════════════════════════
d.rectangle([0, 0, W, 52], fill=AWS_SQUID)
d.text((W // 2, 26), "CloudAttend — AWS Architecture",
       font=F_HUGE, fill="#ffffff", anchor="mm")

# ══════════════════════════════════════════════════════════════════════════════
# GitHub Actions (top-left)
# ══════════════════════════════════════════════════════════════════════════════
rrect([28, 68, 220, 202], radius=10, fill="#f0f6ff", outline=GH_COL, width=2)
gh_ico = _load_aws_icon("management/management-console.png", 36)
if gh_ico:
    paste_icon(gh_ico, 124, 96)
else:
    badge(124, 96, 18, GH_COL, "GH")
d.text((124, 122), "GitHub Actions",    font=F_HEAD,  fill=TEXT_D, anchor="mm")
d.text((124, 136), "CI/CD Pipeline",    font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((124, 150), "• Build & test",    font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((124, 162), "• CF stack deploy", font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((124, 174), "• EB app deploy",   font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((124, 186), "• Manage S3",       font=F_SMALL, fill=TEXT_M, anchor="mm")

# ══════════════════════════════════════════════════════════════════════════════
# CloudFormation (below GH)
# ══════════════════════════════════════════════════════════════════════════════
rrect([28, 218, 220, 318], radius=10, fill="#fff0f8", outline=CF_COL, width=2)
cf_ico = _load_aws_icon("management/cloudformation.png", 36)
if cf_ico:
    paste_icon(cf_ico, 124, 243)
else:
    badge(124, 243, 18, CF_COL, "CF")
d.text((124, 268), "CloudFormation",      font=F_HEAD,  fill=TEXT_D, anchor="mm")
d.text((124, 282), "IaC Stack",           font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((124, 295), "VPC·EB·Aurora·IAM",   font=F_SMALL, fill=TEXT_M, anchor="mm")
arrow(124, 202, 124, 218, color=CF_COL, label="deploys")

# ══════════════════════════════════════════════════════════════════════════════
# S3 bucket (right of GH)
# ══════════════════════════════════════════════════════════════════════════════
rrect([244, 68, 396, 148], radius=10, fill="#f0fff4", outline=S3_COL, width=2)
s3_ico = _load_aws_icon("storage/simple-storage-service.png", 36)
if s3_ico:
    paste_icon(s3_ico, 320, 91)
else:
    badge(320, 91, 18, S3_COL, "S3")
d.text((320, 116), "S3 Bucket",   font=F_HEAD,  fill=TEXT_D, anchor="mm")
d.text((320, 130), "App bundles", font=F_SMALL, fill=TEXT_M, anchor="mm")
arrow(220, 114, 244, 107, color=S3_COL, label="zip")

# ══════════════════════════════════════════════════════════════════════════════
# Browser (far right)
# ══════════════════════════════════════════════════════════════════════════════
rrect([1032, 322, 1168, 422], radius=10, fill="#f0fdf4", outline=BROWSER_COL, width=2)
d.text((1100, 362), "Browser",          font=F_HEAD,  fill=TEXT_D, anchor="mm")
d.text((1100, 378), "Admin / Student",  font=F_SMALL, fill=TEXT_M, anchor="mm")

# ══════════════════════════════════════════════════════════════════════════════
# Internet Gateway
# ══════════════════════════════════════════════════════════════════════════════
rrect([856, 322, 992, 412], radius=10, fill="#f5f3ff", outline=VPC_COL, width=2)
igw_ico = _load_aws_icon("network/internet-gateway.png", 36)
if igw_ico:
    paste_icon(igw_ico, 924, 348)
else:
    badge(924, 348, 18, VPC_COL, "IGW")
d.text((924, 374), "Internet",  font=F_HEAD,  fill=TEXT_D, anchor="mm")
d.text((924, 388), "Gateway",   font=F_SMALL, fill=TEXT_M, anchor="mm")
arrow(1032, 366, 992, 359, color=BROWSER_COL, label="HTTPS")
arrow(992, 376, 1032, 383, color=VPC_COL)

# ══════════════════════════════════════════════════════════════════════════════
# VPC boundary
# ══════════════════════════════════════════════════════════════════════════════
rrect([418, 60, 1020, 762], radius=16, fill="#fafaf9", outline=VPC_COL, width=3)
vpc_ico = _load_aws_icon("network/vpc.png", 18)
if vpc_ico:
    paste_icon(vpc_ico, 436, 83)
d.text((726, 83), "Amazon VPC  —  10.0.0.0/16",
       font=F_HEAD, fill=VPC_COL, anchor="mm")
arrow(856, 364, 1020, 364, color=VPC_COL)

# ── Public subnets ────────────────────────────────────────────────────────────
rrect([436, 98, 1008, 462], radius=10, fill="#f0fdf4", outline="#4ade80", width=1)
d.text((722, 116), "Public Subnets (AZ-1 · AZ-2) — Elastic Beanstalk",
       font=F_SMALL, fill="#166534", anchor="mm")

# Elastic Beanstalk (primary)
eb_cx, eb_cy = 570, 295
service_box(eb_cx, eb_cy, 210, 210,
            "compute/elastic-beanstalk.png", EB_COL,
            "Elastic Beanstalk", "EC2  t3.micro",
            extra_lines=("Django 5 · Python 3.12", "WhiteNoise · DRF", "Gunicorn / WSGI"),
            icon_size=52)

# EB AZ-2
rrect([806, 198, 970, 382], radius=10, fill="#fff", outline="#4ade80", width=1)
d.text((888, 258), "EB (AZ-2)",    font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((888, 274), "Auto-scaled",  font=F_SMALL, fill="#94a3b8", anchor="mm")
d.text((888, 290), "EC2 instance", font=F_SMALL, fill="#94a3b8", anchor="mm")

arrow(856, 348, 694, 298, color=VPC_COL)
arrow(320, 148, 530, 212, color=S3_COL, label="app bundle", dashed=True)

# ── Private subnets ───────────────────────────────────────────────────────────
rrect([436, 480, 1008, 750], radius=10, fill="#fff5f5", outline="#f87171", width=1)
d.text((722, 498), "Private Subnets (AZ-1 · AZ-2) — Aurora Serverless v2",
       font=F_SMALL, fill="#991b1b", anchor="mm")

# Aurora cluster
aurora_cx, aurora_cy = 590, 635
service_box(aurora_cx, aurora_cy, 230, 210,
            "database/aurora.png", AURORA_COL,
            "Aurora Serverless v2", "MySQL-compatible 8.0",
            extra_lines=("Auto-scales 0.5–4 ACUs", "AES-256 encrypted", "7-day backup"),
            icon_size=52)

# Aurora reader
rrect([826, 530, 970, 706], radius=10, fill="#fff", outline=AURORA_COL, width=1)
d.text((898, 598), "Reader",   font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((898, 614), "Endpoint", font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((898, 630), "(AZ-2)",   font=F_SMALL, fill="#94a3b8", anchor="mm")

arrow(eb_cx, eb_cy + 105, aurora_cx, aurora_cy - 105,
      color=AURORA_COL, label="MySQL 3306")

# ══════════════════════════════════════════════════════════════════════════════
# SMTP email (bottom-left)
# ══════════════════════════════════════════════════════════════════════════════
rrect([28, 348, 220, 450], radius=10, fill="#f5f3ff", outline=SMTP_COL, width=2)
d.text((124, 382), "SMTP Email",      font=F_HEAD,  fill=TEXT_D, anchor="mm")
d.text((124, 398), "Gmail / Mailgun", font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((124, 412), "Maildrop (test)", font=F_SMALL, fill=TEXT_M, anchor="mm")
d.text((124, 426), "Welcome emails",  font=F_SMALL, fill=SMTP_COL, anchor="mm")
arrow(460, 287, 220, 388, color=SMTP_COL, label="send_mail()", dashed=True)

# CF → VPC
arrow(220, 268, 418, 268, color=CF_COL, label="provisions")

# ══════════════════════════════════════════════════════════════════════════════
# Legend
# ══════════════════════════════════════════════════════════════════════════════
leg_x, leg_y = 28, 470
rrect([leg_x, leg_y, leg_x + 220, leg_y + 272], radius=8,
      fill="#fff", outline=BORDER_L, width=1)
d.text((leg_x + 110, leg_y + 18), "Legend", font=F_HEAD, fill=TEXT_D, anchor="mm")
for i, (col, lbl) in enumerate([
    (EB_COL,      "Elastic Beanstalk"),
    (S3_COL,      "S3 Storage"),
    (AURORA_COL,  "Aurora Serverless v2"),
    (VPC_COL,     "VPC / Internet GW"),
    (CF_COL,      "CloudFormation IaC"),
    (GH_COL,      "GitHub Actions CI/CD"),
    (SMTP_COL,    "SMTP Email"),
    (BROWSER_COL, "User / Browser"),
]):
    y = leg_y + 44 + i * 26
    d.rectangle([leg_x + 14, y + 2, leg_x + 28, y + 14], fill=col)
    d.text((leg_x + 36, y + 8), lbl, font=F_SMALL, fill=TEXT_D, anchor="lm")

# ══════════════════════════════════════════════════════════════════════════════
# Footer
# ══════════════════════════════════════════════════════════════════════════════
d.rectangle([0, H - 30, W, H], fill=AWS_SQUID)
d.text((W // 2, H - 15),
       "CloudAttend · Django 5 · Elastic Beanstalk · Aurora Serverless v2 · GitHub Actions",
       font=F_SMALL, fill="#94a3b8", anchor="mm")

# ══════════════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════════════
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architecture.png")
img.save(out, "PNG", dpi=(150, 150))
print(f"Saved: {out}  ({img.width}x{img.height})")
