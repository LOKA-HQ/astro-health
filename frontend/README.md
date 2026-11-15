# Astro Health — Frontend

واجهة React/Vite لداشبورد متابعة صحة طاقم رحلة المريخ، متصلة بالـ FastAPI backend الموجود في مجلد `backend`.

## التشغيل

### 1) Backend
من مجلد المشروع الرئيسي:
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
الـ API يعمل على `http://localhost:8000` والوثائق على `http://localhost:8000/docs`.

### 2) Frontend
في Terminal آخر:
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
افتح الرابط الذي يعرضه Vite غالباً `http://localhost:5173`.

للبناء النهائي:
```bash
npm run build
```

## الصفحات
- **Overview:** حالة الطاقم، مؤشرات مختارة، آخر التنبيهات، إشعاع GOES، والاستعداد الفردي.
- **Body:** نموذج ثلاثي الأبعاد دوّار بـ Three.js، نبض بصري متزامن مع HR، و8 مؤشرات مع مخطط 30 يوم.
- **Labs:** نتائج التحاليل المعلّمة مع المدى المرجعي، فلاتر High/Low/Baseline، وتصدير ملخص أسبوعي TXT.
- **Environment:** تدفق البروتونات، عتبات NOAA S-scale، أحداث DONKI، ومعدلات الجرعة المرجعية.

## ملاحظات الداتا
- التحاليل من بيانات NASA OSDR كما يوفرها الـ backend.
- المؤشرات الحيوية اليومية **Synthetic demo data** وليست قياسات حقيقية مباشرة من رواد فضاء.
- بيانات GOES/DONKI هي snapshots يجهزها الـ backend؛ استخدم `POST /api/v1/environment/refresh` لتحديثها.
- معدلات الجرعة المنشورة في صفحة Environment مرجعية وليست قياسات جرعة حية للطاقم.
- النموذج الثلاثي الأبعاد تجسيد بصري للمراقبة وليس تصويراً طبياً تشريحياً. في حال تعذر WebGL تظهر رسالة بديلة.

## الربط
القيمة الافتراضية:
`VITE_API_BASE=http://localhost:8000/api/v1`

غيّرها في `frontend/.env` عند تشغيل الـ API على عنوان آخر.

## Data integrity and refresh behavior

- Crew vital-sign time series are synthetic demonstration data. They are labelled as demo data in the UI and must not be represented as live astronaut wearable telemetry.
- NASA DONKI and NOAA SWPC values are source snapshots. Use **Refresh sources** to call `POST /api/v1/environment/refresh`; a successful request attempts to refresh both external sources independently.
- Laboratory results use API pagination and the dashboard loads all pages before displaying them. The table itself is paginated in 50-row pages.
- Frontend dependencies are pinned to exact versions for repeatable installs.

## Docker

لتشغيل الباك إند والفرونت إند معاً في حاويات، من مجلد المشروع الرئيسي:
```bash
docker compose up --build
```
وبعدين افتح http://localhost:8080 (الداشبورد) — الـ API على http://localhost:8000.

- الـ `VITE_API_BASE` بيتثبّت في الباندل وقت البناء (build arg في `docker-compose.yml`) — غيّره لو الـ API على عنوان تاني.
- الـ `ASTRO_CORS_ORIGINS` في خدمة الباك إند لازم يتضمن عنوان الفرونت إند اللي بيفتحه المتصفح، وإلا المتصفح هيمنع طلبات الـ API.
