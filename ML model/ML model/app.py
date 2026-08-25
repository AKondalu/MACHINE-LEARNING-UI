from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/predict")
def predict():
    return render_template("predict.html")


@app.route("/students")
def students():
    return render_template("students.html")


@app.route("/analytics")
def analytics():
    return render_template("analytics.html")


@app.route("/result")
def result():

    prediction = "PLACED"
    salary = "₹ 8.50 LPA"
    probability = 94

    return render_template(
        "result.html",
        prediction=prediction,
        salary=salary,
        probability=probability
    )


if __name__ == "__main__":
    app.run(debug=True)