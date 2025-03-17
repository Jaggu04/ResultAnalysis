from django.http import HttpResponse
# Create your views here.
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth  import login,logout,authenticate
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Prevents Tkinter error
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from django.shortcuts import render
from django.http import HttpResponse
from fpdf import FPDF
import os
from django.conf import settings
from .forms import ExcelFileUploadForm
from .models import ExcelFile
from django.contrib import messages
import datetime
import json

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import FileResponse
import io
#####################################################storage and upload fetch code#####################################################

def upload_file(request):
    if request.method == "POST":
        form = ExcelFileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)

            # Generate structured filename: 2022_FY_A_filename.xlsx
            original_filename = request.FILES['uploaded_file'].name
            instance.file_name = f"{instance.year_of_admission}_{instance.studying_year}_{instance.division}_{original_filename}"
            
            # Save to database
            instance.save()

            # Show success message
            messages.success(request, "File uploaded successfully!")

            return redirect('file_list')  # Redirect to file list
    else:
        form = ExcelFileUploadForm()

    return render(request, 'upload1.html', {'form': form})


####################################33File List View with Dropdown
def file_list(request):
    year_filter = request.GET.get('year_of_admission', None)
    studying_year_filter = request.GET.get('studying_year', None)

    files = ExcelFile.objects.all()

    if year_filter:
        files = files.filter(year_of_admission=year_filter)
    
    if studying_year_filter:
        files = files.filter(studying_year=studying_year_filter)

    # Generate year choices dynamically
    current_year = datetime.datetime.now().year
    year_choices = [(year, str(year)) for year in range(2000, current_year + 1)]

    return render(request, 'file_list.html', {
        'files': files,
        'year_choices': year_choices
    })

#  File Download View
def download_file(request, file_id):
    file_instance = ExcelFile.objects.get(id=file_id)
    file_path = os.path.join(settings.MEDIA_ROOT, str(file_instance.uploaded_file))
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = f'attachment; filename="{file_instance.file_name}"'
            return response
    else:
        return HttpResponse("File not found!", status=404)


#####################################################upload and analysis code#####################################################



def upload_and_analyze(request):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_file = request.FILES["file"]

        # Load Excel Data
        df = pd.read_excel(uploaded_file)

        # Ensure Correct Column Names
        df.columns = df.columns.str.strip()
        df.rename(columns={"Student ID": "Student_ID"}, inplace=True)  # Adjust if needed
        # Process Data
        subject_columns = df.columns[5:]  # Adjust according to your Excel structure
        for col in subject_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.fillna(0, inplace=True)

        # Calculate Scores
        total_possible_marks = len(subject_columns) * 100
        df["Total_Marks"] = df[subject_columns].sum(axis=1)
        df["Percentage"] = (df["Total_Marks"] / total_possible_marks) * 100
        df["Grade"] = df["Percentage"].apply(lambda x: "A+" if x >= 90 else 
                                             ("A" if x >= 80 else 
                                             ("B" if x >= 70 else 
                                             ("C" if x >= 50 else "F"))))

        # Store Data in Session
        request.session["df"] = json.dumps(df.to_dict(orient="records"))

        # Generate Analysis Charts
        charts = generate_charts(df, subject_columns)

        return render(request, "result.html", {
            "df": df.to_dict(orient="records"),
            "charts": charts,
            "students": df["Name"].tolist(),  # Pass student names for dropdown
        })

    return render(request, "upload.html")


def generate_charts(df, subject_columns):
    """Generates multiple charts for better analysis."""
    chart_paths = {}
    os.makedirs("static", exist_ok=True)

    # 1️⃣ Pass/Fail Bar Chart
    pass_fail_counts = df["Grade"].apply(lambda x: "Pass" if x != "F" else "Fail").value_counts()
    plt.figure(figsize=(5, 3))
    plt.bar(pass_fail_counts.index, pass_fail_counts.values, color=["green", "red"])
    plt.title("Pass/Fail Distribution")
    plt.ylabel("Number of Students")
    chart_paths["pass_fail"] = "static/pass_fail_chart.png"
    plt.savefig(chart_paths["pass_fail"], bbox_inches="tight")
    plt.close()

    # 2️⃣ Grade Distribution Pie Chart
    grade_counts = df["Grade"].value_counts()
    plt.figure(figsize=(5, 3))
    plt.pie(grade_counts, labels=grade_counts.index, autopct="%1.1f%%", startangle=90)
    plt.title("Grade Distribution")
    chart_paths["grade_pie"] = "static/grade_distribution.png"
    plt.savefig(chart_paths["grade_pie"], bbox_inches="tight")
    plt.close()

    # 3️⃣ Top Performers (Top 10%)
    top_performers = df.nlargest(max(1, int(len(df) * 0.1)), "Percentage")
    plt.figure(figsize=(6, 4))
    plt.bar(top_performers["Name"], top_performers["Percentage"], color="blue")
    plt.xticks(rotation=45, ha="right")
    plt.title("Top 10% Performers")
    chart_paths["top_performers"] = "static/top_performers.png"
    plt.savefig(chart_paths["top_performers"], bbox_inches="tight")
    plt.close()

    # 4️⃣ Subject-wise Average Marks
    subject_means = df[subject_columns].mean()
    plt.figure(figsize=(6, 4))
    plt.bar(subject_means.index, subject_means.values, color="purple")
    plt.xticks(rotation=45, ha="right")
    plt.title("Average Marks Per Subject")
    chart_paths["subject_average"] = "static/subject_average.png"
    plt.savefig(chart_paths["subject_average"], bbox_inches="tight")
    plt.close()

    # 5️⃣ Class Performance Distribution (Histogram)
    plt.figure(figsize=(6, 4))
    plt.hist(df["Percentage"], bins=10, color="cyan", edgecolor="black")
    plt.title("Class Performance Distribution")
    plt.xlabel("Percentage Range")
    plt.ylabel("Number of Students")
    chart_paths["performance_distribution"] = "static/performance_distribution.png"
    plt.savefig(chart_paths["performance_distribution"], bbox_inches="tight")
    plt.close()

    return chart_paths

def download_full_pdf(request):
    df = json.loads(request.session.get("df", "[]"))
    if not df:
        return HttpResponse("No data available for analysis", status=400)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica", 12)

    # Title
    p.drawString(100, 750, "Class Performance Report")

    # Pass/Fail Stats
    pass_count = sum(1 for s in df if s["Grade"] != "F")
    fail_count = sum(1 for s in df if s["Grade"] == "F")
    total_students = len(df)

    p.drawString(100, 720, f"Total Students: {total_students}")
    p.drawString(100, 700, f"Pass Count: {pass_count}")
    p.drawString(100, 680, f"Fail Count: {fail_count}")

    # Grade Distribution
    grade_counts = {g: sum(1 for s in df if s["Grade"] == g) for g in ["A+", "A", "B", "C", "F"]}
    y_pos = 660
    for grade, count in grade_counts.items():
        p.drawString(100, y_pos, f"{grade}: {count} students")
        y_pos -= 20

    # Add Analysis Charts
    charts = ["pass_fail_chart.png", "grade_distribution.png", "top_performers.png", "subject_average.png", "performance_distribution.png"]
    y_pos = 580
    for chart in charts:
        img_path = f"static/{chart}"
        if os.path.exists(img_path):
            p.drawImage(img_path, 100, y_pos, width=400, height=200)
            y_pos -= 220  # Move down for next chart

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename="Class_Analysis_Report.pdf")


def download_student_pdf(request):
    student_name = request.GET.get("student_name")  
    if not student_name:
        return HttpResponse("No student selected", status=400)
    
    df = json.loads(request.session.get("df", "[]"))
    student = next((s for s in df if s["Name"] == student_name), None)
    
    if not student:
        return HttpResponse("Student data not found", status=404)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)

    # Title
    p.drawString(100, 750, f"Performance Report for {student_name}")
    p.setFont("Helvetica", 12)

    # Table Header
    y_pos = 700
    p.drawString(100, y_pos, "Subject")
    p.drawString(300, y_pos, "Marks")
    p.line(100, y_pos - 5, 400, y_pos - 5)  # Underline header

    # Subject-wise Marks
    y_pos -= 30
    for subject, marks in student.items():
        if subject not in ["Name", "Total_Marks", "Percentage", "Grade"]:  # Include only subjects
            p.drawString(100, y_pos, subject)
            p.drawString(300, y_pos, str(marks))
            y_pos -= 20

    # Total Score, Percentage & Grade
    y_pos -= 10
    p.line(100, y_pos, 400, y_pos)  # Underline before summary
    y_pos -= 20
    p.drawString(100, y_pos, f"Total Marks: {student['Total_Marks']}")
    p.drawString(100, y_pos - 20, f"Percentage: {student['Percentage']}%")
    p.drawString(100, y_pos - 40, f"Grade: {student['Grade']}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{student_name}_report.pdf")


################################################Authentication code########################################
def home(request):
    if request.user.is_authenticated:
        return render(request,"index.html")
    else:
        return redirect('/stafflogin')

def stafflogin(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect if already logged in

    if request.method == "POST":
        username = request.POST.get('username', '')  # Avoid KeyError
        password = request.POST.get('password', '')

        if username and password:  # Ensure fields are not empty
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
        
        # If authentication fails, return the login page again
        return render(request, "stafflogin.html", {"error": "Invalid credentials"})

    # Always return a response (login page)
    return render(request, "stafflogin.html")

def stafflogout(request):
    logout(request)
    return redirect('stafflogin')
####################################################################################