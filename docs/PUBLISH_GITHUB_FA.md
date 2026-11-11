# انتشار مستقل در GitHub (حساب sanatat)

در این تحویل، مخزن از طریق GitHub ساخته نشده است. به جای ادعای انتشار، این فایل‌ها به‌صورت ZIP آماده شده‌اند.

## راه ۱ — با GitHub CLI

داخل پوشه پروژه در Linux Mint:

```bash
sudo apt update && sudo apt install gh git
# با روش امن خودت وارد GitHub شو:
gh auth login

git init -b main
git add .
git commit -m "Initial reproducible EcoCausal-Reasoner research prototype"
gh repo create sanatat/EcoCausal-Reasoner --public --source=. --remote=origin --push
```

اگر نام مخزن قبلاً وجود داشته باشد، به‌جای ایجاد مجدد باید آن را بررسی کنی. قبل از انتشار بررسی کن هیچ PDF خصوصی، Token، فایل مدل محدود، یا داده حساس به ZIP اضافه نشده باشد.

## راه ۲ — ایجاد یک مخزن خالی در GitHub وب

یک repository جدید با نام `EcoCausal-Reasoner` ایجاد کن و `README`, `license`, `.gitignore` اولیه از سایت را انتخاب نکن؛ سپس از پوشه پروژه:

```bash
git init -b main
git add .
git commit -m "Initial prototype"
git remote add origin https://github.com/sanatat/EcoCausal-Reasoner.git
git push -u origin main
```

**مهم:** پروژه شامل کد واقعی و تست شده است، اما اجرای زنده مدل‌های بزرگ، گردآوری داده‌های واقعی و داوری مستقل هنوز کامل نشده‌اند. CV باید دقیقاً همین مرز را رعایت کند.

## چک امنیتی قبل از Push

```bash
# فایل‌های انتخاب‌شده برای Commit را بررسی کن:
git status --short
git ls-files
python scripts/prepublish_check.py
# هر فایل PDF، کلید، وزن مدل، اطلاعات شخصی یا داده دارای حق نشر را پیش از push حذف کن.
python -m pytest -q
```

**معرفی کوتاه (GitHub Description):**

`Provenance-aware scientific evidence prototype: lexical RAG, RDF/SPARQL, deterministic agents, and synthetic causal/world-model tests.`

**Topics:** `scientific-nlp`, `causal-inference`, `knowledge-graphs`, `rdf`, `sparql`, `research-software`, `python`, `reproducible-research`

پس از انتشار، وارد تب **Actions** شو و موفق‌بودن اجرای تست‌های Python 3.10 و 3.12 را بررسی کن. مدل‌های اختیاری در CI تست نمی‌شوند؛ این مورد را صادقانه در README نگه دار.
