# Deepfake Detector — Free Cloud Deployment Guide (Render.com)

Yeh guide tumhare project ko **Render.com** ke free tier par deploy karne ke liye hai —
poori tarah free, koi credit card nahi chahiye, aur ek public link milega jo koi bhi
open kar sakta hai.

## Maine code mein kya safety/privacy fixes kiye (before deploy)

1. **Secrets environment variables mein** — `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` ab
   hardcoded nahi hain; Render dashboard mein set karoge (neeche steps mein hai).
2. **Purane test photos aur DB records hata diye** — tumhare `media/` folder mein
   real test photos (WhatsApp images, etc.) aur `db.sqlite3` mein 8 purane scan
   records the — yeh public GitHub repo mein jaate toh koi bhi dekh sakta tha.
   Maine dono clean kar diye hain.
3. **Scan History ab private hai** — pehle koi bhi `/history/` page par jaake
   **sabke** uploaded photos dekh sakta tha. Ab har visitor ko sirf apni khud ki
   scan history dikhti hai (browser session ke through, koi login nahi chahiye).
4. **Auto-delete after 7 days** — uploaded photos + heatmaps 7 din baad
   automatically delete ho jaate hain, taaki personal photos hamesha ke liye
   server par na rahein.
5. **Upload validation** — file size max 5MB, sirf real JPG/PNG/WEBP images
   accept hoti hain (corrupted ya disguised files reject ho jaati hain).
6. **Rate limiting** — ek session se 1 ghante mein max 15 scans, taaki koi
   free server ko spam/overload na kar sake.
7. **Production security headers** — HTTPS redirect, secure cookies, clickjacking
   protection — sab `DEBUG=False` hone par automatically on ho jaate hain.
8. **Random filenames** — uploaded file ka original naam (jisme kabhi-kabhi
   phone/app ka naam ya date-time leak hota hai) ab store nahi hota; ek random
   naam use hota hai.

## Deploy Steps (Render.com free tier)

### 1. GitHub par push karo
- GitHub par ek naya **private ya public repo** banao (e.g. `deepfake-detector`).
- Is poore folder (`Deep Fake Detection/`) ko us repo mein push karo:
  ```bash
  cd "Deep Fake Detection"
  git init
  git add .
  git commit -m "Deepfake detector - production ready"
  git branch -M main
  git remote add origin https://github.com/<your-username>/deepfake-detector.git
  git push -u origin main
  ```
- `.gitignore` already bana hua hai — `media/`, `db.sqlite3`, `__pycache__` push
  nahi honge (yeh sahi hai, cloud par yeh apne aap ban jaayenge).

### 2. Render par account banao
- https://render.com par jaake GitHub se sign up karo (free).

### 3. Naya Web Service banao
- Dashboard → **New +** → **Web Service** → apna GitHub repo select karo.
- Settings:
  - **Runtime**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `bash build.sh && gunicorn deepfake_site.wsgi --chdir deepfake_site --bind 0.0.0.0:$PORT`
  - **Instance Type**: Free

### 4. Environment Variables set karo (Render dashboard → Environment)
| Key | Value |
|---|---|
| `SECRET_KEY` | Ek random long string (neeche generate karne ka tarika hai) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` (Render tumhe URL dega, deploy hone ke baad add kar dena, phir redeploy) |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app-name.onrender.com` |
| `PYTHON_VERSION` | `3.12.7` |

**SECRET_KEY generate karne ke liye** (apne local terminal par):
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 5. Deploy
- **Create Web Service** click karo. Render automatically build karega
  (PyTorch install hone mein 5-10 min lag sakte hain, normal hai).
- Deploy hone ke baad tumhe ek link milega: `https://your-app-name.onrender.com`
- Pehli baar deploy hone ke baad, uss actual URL ko `ALLOWED_HOSTS` aur
  `CSRF_TRUSTED_ORIGINS` env vars mein daal ke ek baar **Manual Deploy** kar dena.

### 6. (Optional) Admin access
Agar Django admin (`/admin/`) use karna hai to Render ke **Shell** tab se:
```bash
cd deepfake_site && python manage.py createsuperuser
```

## Important limitations (free tier — jaan lena zaroori hai)

- **Free instance "sleeps"** agar 15 min tak koi traffic na aaye — pehli request
  thodi slow (30-60 sec) hogi jab tak spin-up na ho jaaye. Yeh sirf free tier ki
  baat hai, koi bug nahi.
- **Disk ephemeral hai** — matlab agar Render service restart/redeploy ho, to
  `media/` folder aur SQLite database reset ho jaayenge. Chhote academic demo
  ke liye yeh theek hai (aur privacy ke liye actually accha hai — data apne aap
  clean ho jaata hai), lekin agar tumhe data hamesha persist chahiye to Render
  ka paid "Persistent Disk" ya external storage (Cloudinary/S3) chahiye hoga —
  yeh is project ke scope se bahar hai (jaisa synopsis mein bhi likha hai:
  "Public cloud deployment and production-grade scaling" out of scope hai).
- **Sirf ek instance** — bahut zyada users ek saath use karenge to slow ho
  sakta hai. Demo/college submission ke liye bilkul sahi hai.

## Local par test karna (deploy karne se pehle recommended)

```bash
cd "Deep Fake Detection/deepfake_site"
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r ../requirements.txt
export DEBUG=True SECRET_KEY=local-dev-key ALLOWED_HOSTS=127.0.0.1,localhost
python manage.py migrate
python manage.py runserver
```
Phir browser mein `http://127.0.0.1:8000` kholo.
