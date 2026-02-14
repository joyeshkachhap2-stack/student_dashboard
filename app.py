from flask import Flask, render_template, request, send_from_directory
import os
import urllib.parse
import uuid
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

app = Flask(__name__)

# ================= FOLDERS =================
UPLOAD_FOLDER = "uploads"
REPORT_FOLDER = "reports"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REPORT_FOLDER'] = REPORT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

# ================= RULE BASED AI =================
def evaluate_student(attendance, marks):

    if attendance < 60:
        risk = "High Risk"
    elif attendance < 75:
        risk = "Medium Risk"
    else:
        risk = "Low Risk"

    if marks < 40:
        result = "Fail"
    else:
        result = "Pass"

    if risk == "High Risk":
        suggestion = "Increase attendance immediately and focus on weak subjects."
    elif risk == "Medium Risk":
        suggestion = "Maintain consistency and improve performance."
    else:
        suggestion = "Keep up the good work!"

    return risk, result, suggestion


# ================= HOME =================
@app.route('/')
def home():
    return render_template('index.html')


# ================= SERVE UPLOADED PHOTOS =================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ================= RESULT =================
@app.route('/result', methods=['POST'])
def result():

    name = request.form['name']
    email = request.form['email']
    phone = request.form.get('phone')
    roll = request.form['roll']
    reg = request.form['reg']
    semester = request.form['semester']
    branch = request.form.get('branch', 'Not Provided')


    subjects_list = request.form.getlist('subjects')
    subjects = ", ".join(subjects_list)

    attendance = float(request.form['attendance'])
    marks = float(request.form['marks'])

    # ===== Save Photo with Unique Name =====
    photo = request.files['photo']
    unique_filename = str(uuid.uuid4()) + "_" + photo.filename
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    photo.save(photo_path)

    photo_url = f"/uploads/{unique_filename}"

    # ===== AI Evaluation =====
    risk, result_status, suggestion = evaluate_student(attendance, marks)

    # ===== Generate PDF =====
    pdf_filename = f"{name.replace(' ', '_')}_report.pdf"
    pdf_path = os.path.join(app.config['REPORT_FOLDER'], pdf_filename)

    generate_pdf(pdf_path, name, email, roll, reg, semester, branch,
                 subjects, attendance, marks,
                 risk, result_status, suggestion, photo_path)

    # ===== WhatsApp Link =====
    message = f"""Hello {name},

Your Student Performance Report is ready.

Branch: {branch}
Result: {result_status}
Risk Level: {risk}

Please download your full report from the system.

Regards,
AI Student Dashboard
"""

    encoded_message = urllib.parse.quote(message)
    whatsapp_link = f"https://wa.me/91{phone}?text={encoded_message}"

    return render_template('report.html',
                           name=name,
                           email=email,
                           roll=roll,
                           reg=reg,
                           semester=semester,
                           branch=branch,
                           attendance=attendance,
                           marks=marks,
                           subjects=subjects,
                           risk=risk,
                           result=result_status,
                           suggestion=suggestion,
                           pdf_file=pdf_filename,
                           whatsapp_link=whatsapp_link,
                           photo_url=photo_url)


# ================= PDF GENERATION =================
def generate_pdf(file_path, name, email, roll, reg, semester, branch,
                 subjects, attendance, marks,
                 risk, result_status, suggestion, photo_path):

    doc = SimpleDocTemplate(file_path)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Student Performance Report</b>", styles['Title']))
    elements.append(Spacer(1, 20))

    img = Image(photo_path, 2 * inch, 2 * inch)
    elements.append(img)
    elements.append(Spacer(1, 20))

    data = [
        ["Name", name],
        ["Email", email],
        ["Roll Number", roll],
        ["Registration Number", reg],
        ["Semester", semester],
        ["Branch / Stream", branch],
        ["Subjects", subjects],
        ["Attendance", f"{attendance}%"],
        ["Marks", marks],
        ["Risk Level", risk],
        ["Final Result", result_status],
        ["Suggestion", suggestion]
    ]

    table = Table(data, colWidths=[150, 300])
    elements.append(table)

    doc.build(elements)


# ================= DOWNLOAD REPORT =================
@app.route('/reports/<filename>')
def download_report(filename):
    return send_from_directory(app.config['REPORT_FOLDER'], filename)


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

