from django.db import models

class ExcelFile(models.Model):
    STUDYING_YEAR_CHOICES = [
        ('FY', 'First Year'),
        ('SY', 'Second Year'),
        ('TY', 'Third Year'),
        ('BE', 'Bachelor of Engineering'),
    ]

    DIVISION_CHOICES = [
        ('A', 'Division A'),
        ('B', 'Division B'),
        ('C', 'Division C'),
    ]

    year_of_admission = models.IntegerField()  # Admission Year (e.g., 2022)
    studying_year = models.CharField(max_length=2, choices=STUDYING_YEAR_CHOICES)  
    division = models.CharField(max_length=1, choices=DIVISION_CHOICES)
    uploaded_file = models.FileField(upload_to='uploads/')
    file_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.year_of_admission}_{self.studying_year}_{self.division}_{self.file_name}"
