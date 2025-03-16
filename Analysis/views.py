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
#####################################################storage and upload fetch code#####################################################


from django.contrib import messages

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ExcelFileUploadForm
from .models import ExcelFile
import os
from django.conf import settings
from django.http import HttpResponse

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


#File List View with Dropdown
def file_list(request):
    year_admission_filter = request.GET.get('year_of_admission', None)
    studying_year_filter = request.GET.get('studying_year', None)

    files = ExcelFile.objects.all()

    if year_admission_filter:
        files = files.filter(year_of_admission=year_admission_filter)
    
    if studying_year_filter:
        files = files.filter(studying_year=studying_year_filter)

    return render(request, 'file_list.html', {'files': files})

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

        # Load data
        df = pd.read_excel(uploaded_file)

        # Process Data
        subject_columns = df.columns[5:]
        for col in subject_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.fillna(0, inplace=True)

        total_possible_marks = len(subject_columns) * 100
        df['Total Marks'] = df[subject_columns].sum(axis=1)
        df['Percentage'] = (df['Total Marks'] / total_possible_marks) * 100
        df['Grade'] = df['Percentage'].apply(lambda x: 'A+' if x >= 90 else ('A' if x >= 80 else ('B' if x >= 70 else ('C' if x >= 50 else 'F'))))

        # Save session data
        request.session["df"] = df.to_dict(orient="records")

        # Generate Charts
        charts = generate_charts(df)

        return render(request, "result.html", {"df": df.to_dict(orient="records"), "charts": charts})

    return render(request, "upload.html")


def generate_charts(df):
    """Generates and saves charts as images, returning their paths."""
    chart_paths = {}

    # Pass/Fail Bar Chart
    pass_fail_counts = df['Grade'].apply(lambda x: 'Pass' if x != 'F' else 'Fail').value_counts()
    plt.figure(figsize=(5, 3))
    plt.bar(pass_fail_counts.index, pass_fail_counts.values, color=['green', 'red'])
    plt.title("Pass/Fail Distribution")
    pass_chart_path = "static/pass_fail_chart.png"
    plt.savefig(pass_chart_path)
    chart_paths["pass_fail"] = pass_chart_path
    plt.close()

    # Grade Distribution Pie Chart
    grade_counts = df['Grade'].value_counts()
    plt.figure(figsize=(5, 3))
    plt.pie(grade_counts, labels=grade_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title("Grade Distribution")
    pie_chart_path = "static/grade_distribution.png"
    plt.savefig(pie_chart_path)
    chart_paths["grade_pie"] = pie_chart_path
    plt.close()

    return chart_paths

###################################full analysis download###########################################
def generate_pdf(df):
    """Generates a PDF for full data analysis."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Student Result Analysis", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Students: {len(df)}", ln=True)

    # Grade Distribution
    pdf.image("static/grade_distribution.png", w=150)
    pdf.ln(10)

    pdf_output = BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_content)
    pdf_output.seek(0)
    return pdf_output


def download_full_pdf(request):
    """Returns a downloadable PDF file."""
    df = pd.DataFrame(request.session.get("df", []))
    pdf_file = generate_pdf(df)
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=full_analysis.pdf"
    return response

###################################for individual student download###########################################

def generate_student_pdf(student_name, df):
    """Generates a PDF for individual student performance."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Get student data
    student = df[df["Name"] == student_name].iloc[0]

    # Title
    pdf.cell(200, 10, txt=f"Student Performance Report: {student_name}", ln=True, align='C')
    pdf.ln(10)

    # Basic Info
    pdf.cell(200, 10, txt=f"Student ID: {student['Student ID']}", ln=True)
    pdf.cell(200, 10, txt=f"Total Marks: {student['Total Marks']}", ln=True)
    pdf.cell(200, 10, txt=f"Percentage: {student['Percentage']:.2f}%", ln=True)
    pdf.cell(200, 10, txt=f"Grade: {student['Grade']}", ln=True)

    # Subject-wise marks
    pdf.ln(10)
    pdf.cell(200, 10, txt="Subject-wise Performance:", ln=True)
    for subject in df.columns[5:-3]:  # Assuming subjects start from index 5
        marks = student[subject]
        grade = 'A+' if marks >= 90 else 'A' if marks >= 80 else 'B' if marks >= 70 else 'C' if marks >= 50 else 'F'
        pdf.cell(200, 10, txt=f"{subject}: {marks} (Grade: {grade})", ln=True)

    # Performance comment
    pdf.ln(10)
    comment = "Excellent performance! Keep it up!" if student["Grade"] in ["A+", "A"] else \
              "Good work, but room for improvement." if student["Grade"] == "B" else \
              "Needs more effort." if student["Grade"] == "C" else "Failing. Needs serious attention."
    pdf.cell(200, 10, txt=f"Performance Review: {comment}", ln=True)

    # Save PDF as bytes
    pdf_output = BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_content)
    pdf_output.seek(0)
    return pdf_output


def download_student_pdf(request, student_name):
    """Returns a downloadable PDF file for an individual student."""
    df = pd.DataFrame(request.session.get("df", []))

    # Validate student exists
    if student_name not in df["Name"].values:
        return HttpResponse("Student not found", status=404)

    pdf_file = generate_student_pdf(student_name, df)
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={student_name}_report.pdf"
    return response


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