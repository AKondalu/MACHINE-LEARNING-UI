from pathlib import Path
import math
import joblib
import pandas as pd
from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_PATH = MODELS_DIR / "smartplacement_students.csv"
MODELS_PATH = MODELS_DIR / "smartplacement_models.joblib"

app = Flask(__name__)
app.config["SECRET_KEY"] = "smartplacement-secret"


_cached_artifacts = None
_cached_dataframe = None


def ensure_artifacts():
    global _cached_artifacts, _cached_dataframe
    if _cached_artifacts is None or _cached_dataframe is None:
        if not MODELS_PATH.exists() or not DATA_PATH.exists():
            from train_model import build_and_save_artifacts

            build_and_save_artifacts()
        _cached_artifacts = joblib.load(MODELS_PATH)
        _cached_dataframe = pd.read_csv(DATA_PATH)
    return _cached_artifacts, _cached_dataframe


def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "":
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    try:
        if val is None or str(val).strip() == "":
            return default
        return int(val)
    except (TypeError, ValueError):
        return default


def build_prediction_features(form_data, feature_columns):
    feature_values = {
        "cgpa": safe_float(form_data.get("cgpa"), 7.0),
        "internships": safe_int(form_data.get("internships"), 0),
        "projects": safe_int(form_data.get("projects"), 0),
        "aptitude_score": safe_float(form_data.get("aptitude_score"), 70.0),
        "soft_skills": safe_float(form_data.get("soft_skills"), 7.0),
        "backlogs": safe_int(form_data.get("backlogs"), 0),
        "extra_curricular": safe_float(form_data.get("extra_curricular"), 5.0),
        "communication_skills": safe_float(form_data.get("communication_skills"), 7.0),
    }
    branch_name = (form_data.get("branch", "CSE") or "CSE").strip()
    branch_column = f"branch_{branch_name}"
    features = {column: 0.0 for column in feature_columns}
    for key, value in feature_values.items():
        if key in features:
            features[key] = value
    if branch_column in features:
        features[branch_column] = 1.0
    else:
        fallback = "branch_Others"
        if fallback in features:
            features[fallback] = 1.0
    return pd.DataFrame([features])[feature_columns]


@app.route("/")
def dashboard():
    _, dataframe = ensure_artifacts()
    total_students = len(dataframe)
    placed_count = int(dataframe["placed"].sum())
    not_placed_count = total_students - placed_count
    placement_rate = round((placed_count / total_students) * 100, 2) if total_students else 0.0
    avg_salary = round(float(dataframe.loc[dataframe["placed"] == 1, "salary"].mean()), 2) if placed_count else 0.0

    salary_bins = ["0-2", "2-4", "4-6", "6-8", "8-10", "10-12", "12+"]
    placed_salary = dataframe.loc[dataframe["placed"] == 1, "salary"]
    bins = [0, 2, 4, 6, 8, 10, 12, 1000]
    salary_distribution = pd.cut(placed_salary, bins=bins, labels=salary_bins, include_lowest=True)
    salary_counts = salary_distribution.value_counts().reindex(salary_bins, fill_value=0).astype(int).tolist()

    metrics = {
        "total_students": total_students,
        "placed_count": placed_count,
        "not_placed_count": not_placed_count,
        "placement_rate": placement_rate,
        "avg_salary": avg_salary,
        "status_labels": ["Placed", "Not Placed"],
        "status_counts": [placed_count, not_placed_count],
        "salary_labels": salary_bins,
        "salary_counts": salary_counts,
    }
    return render_template("dashboard.html", metrics=metrics, endpoint="dashboard")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    artifacts, _ = ensure_artifacts()
    branches = ["CSE", "ECE", "EEE", "MECH", "Others"]
    result = None
    form_values = {
        "cgpa": "7.5",
        "internships": "2",
        "projects": "3",
        "aptitude_score": "78",
        "soft_skills": "8",
        "backlogs": "0",
        "extra_curricular": "7",
        "communication_skills": "8",
        "branch": "CSE",
    }

    if request.method == "POST":
        form_values = request.form.to_dict()
        feature_frame = build_prediction_features(form_values, artifacts["feature_columns"])
        placement_model = artifacts["placement_model"]
        salary_model = artifacts["salary_model"]
        placement_probability = float(placement_model.predict_proba(feature_frame)[0, 1])
        placement_prediction = int(placement_model.predict(feature_frame)[0])
        status = "PLACED" if placement_prediction == 1 else "NOT PLACED"
        estimated_salary = round(max(0.0, float(salary_model.predict(feature_frame)[0])), 2) if placement_prediction == 1 else 0.0

        result = {
            "status": status,
            "estimated_salary": estimated_salary,
            "probability": round(placement_probability * 100, 1),
            "confidence": round((1 - abs(placement_probability - 0.5)) * 100, 1),
            "input_summary": {
                "CGPA": form_values.get("cgpa", "N/A"),
                "Internships": form_values.get("internships", "N/A"),
                "Projects": form_values.get("projects", "N/A"),
                "Aptitude": form_values.get("aptitude_score", "N/A"),
                "Soft Skills": form_values.get("soft_skills", "N/A"),
                "Backlogs": form_values.get("backlogs", "N/A"),
                "Extra Curricular": form_values.get("extra_curricular", "N/A"),
                "Communication": form_values.get("communication_skills", "N/A"),
                "Branch": form_values.get("branch", "N/A"),
            },
        }

    return render_template(
        "predict.html",
        result=result,
        form_values=form_values,
        branches=branches,
        endpoint="predict",
    )


@app.route("/students")
def students():
    _, dataframe = ensure_artifacts()
    page = max(1, safe_int(request.args.get("page"), 1))
    search_term = (request.args.get("search", "") or "").strip()
    branch_filter = request.args.get("branch", "")
    placement_filter = request.args.get("placement", "")

    filtered = dataframe.copy()
    if search_term:
        search_mask = filtered["name"].str.contains(search_term, case=False, na=False) | filtered["branch"].str.contains(search_term, case=False, na=False)
        filtered = filtered[search_mask]
    if branch_filter:
        filtered = filtered[filtered["branch"] == branch_filter]
    if placement_filter == "placed":
        filtered = filtered[filtered["placed"] == 1]
    elif placement_filter == "not_placed":
        filtered = filtered[filtered["placed"] == 0]

    page_size = 10
    total_pages = max(1, math.ceil(len(filtered) / page_size))
    page = min(page, total_pages)
    start = (page - 1) * page_size
    end = start + page_size
    page_records = filtered.iloc[start:end]

    selected_student = None
    selected_id = request.args.get("view_id")
    if selected_id:
        val = safe_int(selected_id, -1)
        if val != -1:
            selected_student = dataframe[dataframe["student_id"] == val]
            if not selected_student.empty:
                selected_student = selected_student.iloc[0].to_dict()

    start_page = max(1, page - 3)
    end_page = min(total_pages, page + 3)
    if end_page - start_page < 6:
        if start_page == 1:
            end_page = min(total_pages, start_page + 6)
        elif end_page == total_pages:
            start_page = max(1, end_page - 6)
    page_range = list(range(start_page, end_page + 1))

    branches = sorted(dataframe["branch"].unique().tolist())
    return render_template(
        "students.html",
        students=page_records.to_dict(orient="records"),
        selected_student=selected_student,
        branches=branches,
        page=page,
        total_pages=total_pages,
        page_range=page_range,
        has_prev=(page > 1),
        has_next=(page < total_pages),
        prev_page=page - 1,
        next_page=page + 1,
        total_records=len(filtered),
        search_term=search_term,
        branch_filter=branch_filter,
        placement_filter=placement_filter,
        endpoint="students",
    )


@app.route("/analytics")
def analytics():
    _, dataframe = ensure_artifacts()
    placed_students = dataframe[dataframe["placed"] == 1]
    avg_cgpa_placed = round(float(placed_students["cgpa"].mean()), 2) if not placed_students.empty else 0.0
    placement_rate = round(float(dataframe["placed"].mean() * 100), 2) if not dataframe.empty else 0.0
    avg_aptitude = round(float(dataframe["aptitude_score"].mean()), 2) if not dataframe.empty else 0.0

    cgpa_bins = ["< 6.0", "6.0-7.0", "7.0-8.0", "8.0-9.0", "9.0+"]
    cgpa_ranges = pd.cut(dataframe["cgpa"], bins=[0, 6, 7, 8, 9, 10], labels=cgpa_bins, include_lowest=True)
    cgpa_rate = dataframe.groupby(cgpa_ranges)["placed"].mean().fillna(0) * 100

    branch_rate = dataframe.groupby("branch")["placed"].mean().fillna(0) * 100

    metrics = {
        "avg_cgpa_placed": avg_cgpa_placed,
        "placement_rate": placement_rate,
        "avg_aptitude": avg_aptitude,
        "cgpa_labels": cgpa_bins,
        "cgpa_rates": [round(float(value), 1) for value in cgpa_rate.tolist()],
        "branch_labels": [label for label in branch_rate.index.tolist()],
        "branch_rates": [round(float(value), 1) for value in branch_rate.tolist()],
    }
    return render_template("analytics.html", metrics=metrics, endpoint="analytics")


@app.route("/about")
def about():
    return render_template("about.html", endpoint="about")


@app.route("/help")
def help():
    return render_template("help.html", endpoint="help")


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

