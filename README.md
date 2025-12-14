# Raman Spectrum Fitting App for SnX₆ Octahedra

A Streamlit web application for fitting experimental Raman spectra against theoretical spectra for tin-halide octahedra (SnCl₆₋ₙBrₙ).

## Features

- **Upload experimental spectra** in XY format (wavenumber vs intensity)
- **10 theory spectra** for mixed Sn-halide octahedra:
  - SnCl₆ and SnBr₆ (end members)
  - SnCl₅Br and SnClBr₅ (singly substituted)
  - SnCl₄Br₂ (cis and trans isomers)
  - SnCl₃Br₃ (fac and mer isomers)
  - SnCl₂Br₄ (cis and trans isomers)
- **Interactive sliders** for real-time fitting:
  - Individual coefficients for each theory spectrum
  - Rigid wavenumber shift for all spectra
  - Adjustable peak width (FWHM)
- **Fit quality metrics**: R², RMS residual, scale factor
- **Residual plot** for visual assessment

## Project Structure

```
raman-fitting-app/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── deploy.sh           # Cloud Run deployment script
├── sample_spectrum.xy  # Sample data for testing
└── README.md           # This file
```

## Local Development

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Google Cloud Run Deployment

### Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
2. [Docker](https://docs.docker.com/get-docker/) installed
3. A GCP project with billing enabled

### Quick Deploy

1. Edit `deploy.sh` and set your `PROJECT_ID`:
   ```bash
   PROJECT_ID="your-project-id"
   ```

2. Make the script executable and run:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

### Manual Deployment Steps

1. **Authenticate with GCP:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable required APIs:**
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com
   ```

3. **Build and push container:**
   ```bash
   # Build locally
   docker build -t gcr.io/YOUR_PROJECT_ID/raman-fitting .
   
   # Push to Container Registry
   docker push gcr.io/YOUR_PROJECT_ID/raman-fitting
   ```

4. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy raman-fitting \
       --image gcr.io/YOUR_PROJECT_ID/raman-fitting \
       --platform managed \
       --region us-central1 \
       --allow-unauthenticated \
       --port 8080 \
       --memory 1Gi
   ```

### Alternative: Deploy with Cloud Build

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/raman-fitting
gcloud run deploy raman-fitting --image gcr.io/YOUR_PROJECT_ID/raman-fitting --platform managed --region us-central1 --allow-unauthenticated
```

## Input File Format

The app accepts XY files with the following format:
- Two columns: wavenumber (cm⁻¹) and intensity
- Separated by spaces, tabs, or commas
- Lines starting with `#` are treated as comments
- File extensions: .txt, .xy, .dat, .csv

Example:
```
# Raman spectrum
100.0   45.2
105.0   52.1
110.0   78.4
...
```

## Theory Spectra

The theoretical Raman peak positions and intensities are derived from DFT calculations for isolated SnX₆ octahedra. Each spectrum consists of discrete Raman-active modes that are broadened using Lorentzian line shapes for visualization and fitting.

## License

MIT License
