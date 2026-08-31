# AQI Predictor

Hourly US EPA AQI forecasts for the next 72 hours across major Pakistani cities, served from an end to end serverless MLOps pipeline.

Live app: https://pakaqipredictor.netlify.app
API: [https://aqi-predictor-uid9.onrender.com](https://aqi-predictor-uid9.onrender.com)

## What it does

Go ahead and pick a city and the app shows the current air quality and the forecast for the next three days at 24, 48, and 72 hour horizons. Each forecast comes with a plain language summary, the recent Pakistan AQI news, and a per horizon breakdown of the features that pushed the prediction up or down, computed with real SHAP values from the model.

The data stays current on its own. A feature pipeline runs every hour to pull fresh weather and pollutant data, compute features, and write them to the feature store. The forecast you see is always built from the latest available inputs.

## How it fits together

The system is five pieces wired in a line, plus two schedulers that keep it running.

1. **Data.** Pulls the weather and pollutant history from OpenMeteo. No API key, and the free tier gives the historical depth that is needed for training.
2. **Features.** Raw data gets turned into model ready features: lags and rolling stats for AQI and PM values, cyclical time encodings (hour and month as sin and cos), and weather dispersion features like wind vectors, surface pressure, and a stagnation index. The forecast targets are the only thing that looks forward. Everything else is known at prediction time, so there is no leakage.
3. **Feature store.** Features land in Hopsworks Serverless. Training reads the full history from here, and a lightweight serving feature group (one overwritten row per city, keyed by city id) feeds live predictions without loading the heavy engine.
4. **Model.** Then train a pooled XGBoost model, one per horizon, across the tier 1 cities. Metrics (RMSE, MAE, R2) are computed per city and per horizon on a chronological hold out split. SHAP values are computed once and baked into the model bundle so the frontend can show real feature importance per horizon.
5. **Serving.** A FastAPI backend loads the model bundle, reads the serving vector, builds the forecast, and returns it along with an AI written summary (Groq) and recent AQI news (GNews). A React frontend renders the forecast chart, the horizon cards, the SHAP drivers panel, and the alerts.

### Automation

Two GitHub Actions workflows keep the system fresh.

- **Feature pipeline** runs hourly. It fetches new data, computes features, and updates the feature store and serving vectors.
- **Training pipeline** runs weekly. It retrains, evaluates against the currently deployed model, and only promotes the new model if the 24h and 48h R2 do not regress. A retrain that comes out worse is rejected and the existing model is kept. Promotion to the live serving model is a deliberate manual step, so an unreviewed model never reaches users on its own.

## Tech stack

**Data and features**
- OpenMeteo (weather and pollutant data)
- Hopsworks Serverless (feature store, online enabled, HUDI write path)

**Modelling**
- scikit-learn, XGBoost (pooled, one model per horizon)
- SHAP (TreeExplainer) for per horizon feature importance
- Model bundle saved as joblib, metrics as JSON

**Backend**
- FastAPI
- Groq (`openai/gpt-oss-20b`) for the plain language summary
- GNews for Pakistan wide AQI news

**Frontend**
- React with TypeScript, built on Vite
- Tailwind v4 and shadcn/ui
- Recharts for the forecast chart
- Motion for animation
- Brutalist visual style

**Infrastructure**
- Netlify (frontend)
- Render (backend)
- GitHub Actions (feature and training pipelines)

## Cities

6 tier 1 cities run the full pipeline with two years of backfilled hourly history and their own trained models: Karachi, Lahore, Islamabad, Peshawar, Faisalabad and Quetta. The forecast is strongest at 24 hours and, as expected for air quality, gets harder at 48 and 72 hours. I reported the real per city metrics rather than hiding the harder horizons.

Other cities sit in the registry as tier 2 and are not part of the trained pipeline. Promoting or demoting a city is a one line change to its tier in `src/cities.py`.

## Running it locally

You need Python 3.12 and Node. The project is set up to run each Python module with `python -m`.

### 1. Clone and set up Python

```bash
git clone https://github.com/SyedSameerRizvi/AQI-Predictor.git
cd AQI-Predictor
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` in the project root with your keys:

```
HOPSWORKS_API_KEY=your_key
HOPSWORKS_PROJECT=your_project
GROQ_API_KEY=your_key
GNEWS_API_KEY=your_key
```

### 3. Run the backend

From the project root:

```bash
python -m uvicorn src.api:app --port 8000
```

### 4. Run the frontend

From a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on port 5173 and reads the city list live from the backend.

### Pipelines

Run the pipelines by hand when you need to:

```bash
python -m src.pipelines.feature_pipeline
python -m src.pipelines.training_pipeline
```

In production these run on GitHub Actions on the schedules above. Both also have a manual trigger.

## API

The backend exposes:

- `GET /cities` returns the served cities
- `GET /forecast/{city_id}` returns the current AQI, the 24, 48, and 72 hour forecast, per horizon accuracy, the SHAP explanations, and the AI summary
- `GET /metrics` returns the model metrics
- `GET /news` returns recent Pakistan AQI news

City ids are prefixed, for example `pk-karachi`.

## Notes

The Hopsworks free tier shapes a few choices. Bulk reads go through the online store, serving uses a dedicated lightweight feature group to stay under the memory limit on the free backend host, and the write path uses HUDI with streaming. These are worked around in the pipeline code rather than papered over.
