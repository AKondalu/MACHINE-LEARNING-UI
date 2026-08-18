# SmartPlacement - Student Placement Prediction System

## Overview
This project provides a complete Flask web application for student placement prediction and analytics. It includes:
- a responsive dashboard,
- a prediction form with result display,
- a searchable students list,
- analytics pages with Chart.js visualizations,
- an ML training workflow using synthetic student data.

## Project Structure
- app.py: Flask application and routes
- run.py: application entry point
- train_model.py: generates synthetic data, trains the models, and saves artifacts
- templates/: HTML templates for the UI
- static/: CSS and JavaScript assets
- models/: generated model and data artifacts

## Setup on Windows
1. Open PowerShell in the project folder.
2. Install dependencies:
   `python -m pip install -r requirements.txt`
3. Train the model (optional if artifacts already exist):
   `python train_model.py`
4. Run the app:
   `python app.py`
5. Open http://127.0.0.1:5000

## Notes
The app will generate synthetic data and train models automatically if the trained artifacts do not exist.
