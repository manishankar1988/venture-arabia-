# Venture Arabia Trading Services – E-commerce Website

A secure, mobile-friendly online shop and content management system for
**Venture Arabia Trading Services**, Salwa Road, Doha, Qatar – Trodat
stamps dealer since 2009, supplier of computer toners and accessories, and
provider of printing, photocopying, laminating and binding services.

Built with **Django 5.2** (Python). The built-in administration panel is the
company's back office: staff add products and services, manage orders and
quotes, and edit every page of text on the site without touching code.

---

## 1. What is included

| Area | Features |
|------|----------|
| Storefront | Home page with hero banner, categories, featured products, services and testimonials; product catalogue with categories/sub-categories, search, sorting and pagination; product pages with specifications, gallery and stamp-text customisation; services pages with "Request a quote"; contact page with map |
| Shopping | Session cart (custom stamp text per line), guest checkout, delivery or collection, cash / card-on-delivery / bank transfer, delivery fee and free-delivery threshold, order confirmation emails, order tracking by order number + phone, customer accounts with order history and password reset |
| Back office (admin) | Products with images, prices, stock, specs; categories; services; orders with status workflow and CSV export; quote requests; contact messages; site settings (company details, CR number, phones, bank details, delivery fee, tax rate, payment methods); editable pages (About, Terms, Privacy, Returns, Delivery); home banners; testimonials |
| Qatar-specific | QAR currency, Asia/Qatar timezone, +974 phone validation, Qatar zone/street address fields, no VAT by default (configurable), starter legal pages referencing Qatari law, seller identification in footer and emails |
| Security | HTTPS redirect + HSTS in production, secure/HttpOnly/SameSite cookies, CSRF protection, Content-Security-Policy, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy, PBKDF2 password hashing, strong password rules, login brute-force lockout (django-axes), upload type/size validation, honeypot spam protection, obscured admin URL, environment-based secrets |
| SEO | Clean URLs, meta descriptions, Open Graph tags, product structured data (schema.org), XML sitemap, robots.txt |
| Quality | Automated end-to-end tests (`python manage.py test`), GitHub Actions CI (deploy checks, migrations, tests, Docker build) |
| Deployment | Docker Compose stack (PostgreSQL + Gunicorn + Nginx + certbot), systemd unit, Nginx config, deploy and backup scripts in `deploy/`; Windows production server via `serve.ps1` |

---

## 2. Run it locally (Windows)

The project uses **PostgreSQL 17** in development and production. Locally it runs
from the portable PostgreSQL binaries in `D:\pgsql17` (no installer or admin
rights needed) using the helper script `pg-local.ps1`.

```powershell
cd "D:\Venture Arabia"
python -m venv .venv                      # once
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt           # once
copy .env.example .env                    # once - DEBUG=1 and the local DATABASE_URL are already set
.\pg-local.ps1 init                       # once - creates the local database (role venture / password venture)
.\pg-local.ps1 start                      # every time after a reboot
python manage.py migrate
python manage.py seed_demo                # loads catalogue, services, settings and legal pages (safe to re-run)
python manage.py attach_catalogue_images  # links the product photos in media/products to the products
python manage.py createsuperuser          # your admin login
python manage.py runserver
```

Or simply run `.
un.ps1`, which does all of the above (including starting PostgreSQL) and launches the site.

Open <http://127.0.0.1:8000/> for the shop and <http://127.0.0.1:8000/manage/> for the admin panel.

A development `.env` and an admin user (`admin` / `ChangeMe!2026`) were created
during the initial build - **change that password** from *Authentication and
Authorization -> Users* in the admin panel.

`pg-local.ps1 stop` stops the database; `pg-local.ps1 psql` opens a SQL prompt.
If the PostgreSQL binaries are missing, download `postgresql-17.x-windows-x64-binaries.zip`
from <https://www.enterprisedb.com/download-postgresql-binaries> and extract it to `D:\pgsql17`.
Leaving `DATABASE_URL` empty in `.env` falls back to SQLite for quick experiments.

### Version control

The project is a git repository (branch `main`). Secrets and generated files are
excluded by `.gitignore`: `.env`, the virtualenv, `staticfiles/`, `db.sqlite3`
and customer uploads in `media/quotes/`. To publish it to GitHub or another host:

```powershell
git remote add origin https://github.com/<your-account>/venture-arabia.git
git push -u origin main
```

Commit your changes regularly with `git add -A` and `git commit -m "describe the change"`.
Never commit `.env` or `.env.production`.

Every push to `main` runs the GitHub Actions workflow in `.github/workflows/ci.yml`:
production settings check, migration check, the test suite against PostgreSQL 17 and a
Docker image build. Run the same tests locally with `python manage.py test`.

---

## 3. Admin panel guide (for the company)

Log in at `/manage/` (the path is set by `ADMIN_URL` in `.env`).

| Menu | Use it to… |
|------|-----------|
| **Website content → Site settings** | Company name, tagline, logo, **CR number**, address, phones, WhatsApp, email, opening hours, social links, delivery fee, free-delivery threshold, tax rate, which payment methods are enabled, bank transfer details, announcement bar, About text |
| **Website content → Pages** | Edit About, Terms & Conditions, Privacy Policy, Returns & Refunds, Delivery pages or add new ones. HTML is allowed. Tick *show in footer* / *show in main navigation* |
| **Website content → Home banners** | Hero slide on the home page (title, subtitle, image, button) |
| **Website content → Testimonials / Contact messages** | Customer quotes for the home page; messages sent through the contact form |
| **Products & services → Categories** | Product groups (a category can have a parent, e.g. *Round Stamps* under *Trodat Self-Inking Stamps*) |
| **Products & services → Products** | Add/edit products: name, SKU/model, price, compare-at price, stock, plate size, ink cartridge, colours, photos (main image + gallery), *Requires custom text* for stamps, featured/active flags. Bulk actions: publish, hide, export CSV |
| **Products & services → Services** | Printing, photocopying, laminating, binding, etc. with starting price, unit and turnaround |
| **Products & services → Quote requests** | Enquiries from the "Request a quote" form, with status and internal notes |
| **Orders → Orders** | Every web order: customer details, delivery address, items with stamp text, totals. Change *Status* (Pending → Confirmed → In production → Ready/Out for delivery → Delivered) and *Payment status*; bulk actions and CSV export |

Tips
* Product photos and sample impressions were cropped from the Trodat dealer catalogue (`docs/trodat-catalogue.pdf`) and live in `media/products/`. Replace them with your own photos any time from the product page in the admin (square images, at least 800 × 800 px). Toner and paper items have no catalogue photo yet.
* Untick *Track stock* for made-to-order items (stamps). Tick it for cartridges, pads and paper so stock counts down automatically.
* **Stamps and services show no price** ("Price on request") as requested by the company; the price is confirmed with the customer before production. Consumables (cartridges, pads, ink, paper, toner) carry placeholder prices – update them, or clear a price to show "Price on request".

---

## 4. Going live in Qatar – deployment checklist

### 4.1 Hosting
Any Linux VPS or cloud server works. For data-residency comfort under Qatar's
privacy law, prefer a region in Qatar or the GCC (for example Microsoft Azure
*Qatar Central* in Doha, AWS *me-south-1* Bahrain / *me-central-1* UAE, Oracle
Cloud Doha, or a Qatari provider such as Ooredoo Cloud / Meeza). Register a
`.qa` domain through a registrar accredited by the Communications Regulatory
Authority (CRA).

### 4.2 Three ways to run the production version

All of them use the same code from git and the same `.env` values (section 4.3).
`python manage.py check --deploy` must report no warnings before you go live.

**0. Quick public URL for testing (Render.com, free tier)**
Push the repo to GitHub, then on <https://dashboard.render.com> choose *New -> Blueprint*, pick the
repository and apply `render.yaml`. You get `https://venture-arabia.onrender.com` with PostgreSQL
attached. The first start seeds the catalogue and creates the admin user `admin` by itself
(`bootstrap_site`); read the generated password from the service's *Environment* tab
(`DJANGO_SUPERUSER_PASSWORD`) and change it after logging in.
The free tier sleeps when idle and loses admin-uploaded photos on redeploy, so use it for
review, not for the real shop.

**A. Docker Compose (recommended – one command on any Linux server)**
```bash
git clone <your-repo> venture && cd venture
cp .env.production.example .env && nano .env      # SECRET_KEY, domain, DB password, email
echo "POSTGRES_PASSWORD=<same password as in DATABASE_URL>" >> .env
cd deploy
docker compose up -d --build
docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d venturearabia.qa -d www.venturearabia.qa
docker compose restart nginx
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py attach_catalogue_images
docker compose exec web python manage.py createsuperuser
```
In `.env` use `DATABASE_URL=postgres://venture:<password>@db:5432/venture`, `BEHIND_PROXY=1`,
`FORCE_HTTPS=0` (Nginx redirects) and `SERVE_MEDIA=0` (Nginx serves media).
Update later with `git pull && docker compose up -d --build`.

**B. Plain Ubuntu server (systemd + Nginx)**
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip nginx postgresql certbot python3-certbot-nginx
sudo -u postgres createuser venture -P && sudo -u postgres createdb -O venture venture
sudo useradd -m -d /srv/venture venture && sudo -u venture git clone <your-repo> /srv/venture
cd /srv/venture && sudo -u venture python3 -m venv .venv && sudo -u venture .venv/bin/pip install -r requirements.txt
sudo -u venture cp .env.production.example .env && sudo -u venture nano .env
sudo -u venture mkdir -p logs backups
sudo -u venture .venv/bin/python manage.py migrate
sudo -u venture .venv/bin/python manage.py seed_demo
sudo -u venture .venv/bin/python manage.py attach_catalogue_images
sudo -u venture .venv/bin/python manage.py createsuperuser
sudo -u venture .venv/bin/python manage.py collectstatic --noinput
sudo cp deploy/gunicorn.service /etc/systemd/system/venture.service && sudo systemctl enable --now venture
sudo cp deploy/nginx.conf /etc/nginx/sites-available/venture   # edit: upstream 127.0.0.1:8000, /srv/venture/staticfiles, /srv/venture/media
sudo ln -s /etc/nginx/sites-available/venture /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d venturearabia.qa -d www.venturearabia.qa
```
Later updates: `bash deploy/deploy.sh` (pulls from git, migrates, collects static, restarts).
Nightly backups: add `deploy/backup.sh` to cron as shown inside the script.

**C. Windows server or a local production-mode test (Waitress)**
```powershell
copy .env.production.example .env.production      # then edit
.\serve.ps1                                       # check --deploy, migrate, collectstatic, serve on :8000
```
For a local test on plain HTTP set `ALLOWED_HOSTS=localhost,127.0.0.1`, `FORCE_HTTPS=0`
and `SERVE_MEDIA=1` in `.env.production`. On a real Windows server put IIS or another
reverse proxy with HTTPS in front and keep `FORCE_HTTPS=1`, `BEHIND_PROXY=1`.

### 4.3 Production `.env`
```
SECRET_KEY=<64+ random characters – python -c "import secrets;print(secrets.token_urlsafe(64))">
DEBUG=0
ALLOWED_HOSTS=venturearabia.qa,www.venturearabia.qa
CSRF_TRUSTED_ORIGINS=https://venturearabia.qa,https://www.venturearabia.qa
ADMIN_URL=<something-unguessable>/
DATABASE_URL=postgres://venture:<password>@localhost:5432/venture
EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_HOST_USER=venture@venture.com.qa
EMAIL_HOST_PASSWORD=<app password>
EMAIL_USE_TLS=1
DEFAULT_FROM_EMAIL=Venture Arabia <venture@venture.com.qa>
ORDER_NOTIFICATION_EMAIL=venture@venture.com.qa
BEHIND_PROXY=1
FORCE_HTTPS=1
SERVE_MEDIA=0
```
With `DEBUG=0` the site forces HTTPS, enables HSTS, marks cookies *Secure* and
refuses to start without a `SECRET_KEY`.

### 4.4 Online card payments (optional)
The site currently takes **cash or card on delivery and bank transfer**, so no
card data ever touches the server (no PCI-DSS scope). To accept cards online
you need a merchant agreement with a payment provider licensed for Qatar –
for example QPay / Sadad (Qatar Central Bank), Dibsy, SkipCash, Tap Payments or
Checkout.com – and then add a payment step in `shop/views.py` after the order
is created, marking `payment_status = paid` on the provider's webhook. Keep
card entry on the provider's hosted page.

---

## 5. Legal & regulatory checklist (State of Qatar)

The site was built to support compliance with the main laws that apply to an
online shop in Qatar. **The seeded legal pages are templates – have them
reviewed by a lawyer licensed in Qatar before launch**, and keep them updated.

| Requirement | Law / regulator | Where it is handled |
|-------------|-----------------|---------------------|
| Seller identification (legal name, address, CR number, contact details) shown clearly | Law No. 16 of 2010 (E-Commerce & Transactions); Law No. 8 of 2008 (Consumer Protection); MOCI e-commerce guidance | Footer, contact page, order emails ← **enter your CR number in Site settings** |
| Clear prices in QAR, delivery charges and total shown before the order is confirmed | Consumer Protection Law | Cart, checkout, confirmation page |
| Terms & Conditions accepted before ordering; order acknowledgement sent | E-Commerce Law | Mandatory checkbox at checkout (recorded on the order); confirmation email |
| Returns, refunds and warranty rights; complaint route to MOCI Consumer Protection Dept. | Consumer Protection Law | *Returns & Refunds* page |
| Privacy notice, consent, data minimisation, security, breach notification, data subject rights | Law No. 13 of 2016 (Personal Data Privacy Protection – PDPPL), supervised by the National Cyber Security Agency | *Privacy Policy* page, consent checkboxes on registration/checkout, essential-only cookies with notice, security controls above |
| Website security and lawful use | Law No. 14 of 2014 (Cybercrime) | Security hardening, Terms section 9 |
| VAT | Qatar has not yet implemented VAT on these goods | `Tax rate %` in Site settings (default 0) – update if the law changes |
| Commercial Registration, trade licence and MOCI e-commerce registration for the online store | MOCI | Obtain / update before launch; record CR number in Site settings |
| Advertising & promotions | MOCI approval is required for public promotions/discount campaigns in Qatar | Get approval before running "sale" pricing (compare-at prices) |
| Language | Arabic is the official language; English is accepted for commercial websites but Arabic versions of Terms may be requested | Django i18n is enabled (`LANGUAGES` en/ar) – add Arabic translations in `locale/ar/` when ready |

---

## 6. Project layout

```
venture/        settings, URLs, WSGI
cms/            site settings, pages, banners, testimonials, contact, security-headers middleware, sitemaps
catalog/        categories, products, product images, services, quote requests, seed command
shop/           cart, orders, checkout, tracking, customer orders
accounts/       registration, login, profile, password reset
templates/      HTML templates (base.html = layout)
static/         css/site.css, js/site.js, favicon
media/          product/category/banner images from the catalogue; customer uploads go to media/quotes (ignored by git)
docs/           the Trodat dealer catalogue PDF the images were taken from
deploy/         Dockerfile, docker-compose.yml, nginx.conf, gunicorn.service, deploy.sh, backup.sh
serve.ps1       production-mode server for Windows (Waitress)
shop/tests.py   end-to-end test suite
```

Useful commands: `python manage.py check --deploy`, `python manage.py collectstatic`,
`python manage.py seed_demo`, `python manage.py createsuperuser`.
