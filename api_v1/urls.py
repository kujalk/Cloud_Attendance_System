from django.urls import path
from api_v1 import views

urlpatterns = [
    # ---- REST API ----
    path('api/v1/students/', views.StudentListCreate.as_view(), name='api_students'),
    path('api/v1/students/<slug:student_id>/', views.StudentDetail.as_view(), name='api_student_detail'),
    path('api/v1/attendance/', views.AttendanceListCreate.as_view(), name='api_attendance'),
    path('api/v1/attendance/<int:pk>/', views.AttendanceDetail.as_view(), name='api_attendance_detail'),
    path('api/v1/subjects/', views.SubjectListCreate.as_view(), name='api_subjects'),
    path('api/v1/subjects/<int:subject_code>/', views.SubjectDetail.as_view(), name='api_subject_detail'),
    path('api/v1/departments/', views.DepartmentListCreate.as_view(), name='api_departments'),
    path('api/v1/enrollments/', views.StudentSubjectListCreate.as_view(), name='api_enrollments'),

    # ---- Legacy API (backwards compatibility) ----
    path('v1/student/<slug:student_id>', views.StudentDetail.as_view()),
    path('v1/student', views.StudentListCreate.as_view()),
    path('v1/attendance/<int:pk>', views.AttendanceDetail.as_view()),
    path('v1/attendance', views.AttendanceListCreate.as_view()),

    # ---- Dashboard ----
    path('', views.dashboard, name='home'),
    path('home', views.homePage),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),

    # ---- Students ----
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_create, name='student_create'),
    path('students/<slug:student_id>/', views.student_detail, name='student_detail'),
    path('students/<slug:student_id>/edit/', views.student_edit, name='student_edit'),
    path('students/<slug:student_id>/delete/', views.student_delete, name='student_delete'),
    path('students/<slug:student_id>/resend-email/', views.resend_welcome_email, name='resend_welcome_email'),

    # Legacy student URLs
    path('student_insert', views.student_insert),
    path('student_update', views.student_update),
    path('student_viewsingle', views.student_viewsingle),
    path('student_viewall', views.student_viewall),
    path('student_delete', views.student_list),

    # ---- Attendance ----
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/add/', views.attendance_create, name='attendance_create'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('attendance/<int:pk>/delete/', views.attendance_delete_view, name='attendance_delete'),

    # Legacy attendance URLs
    path('attendance_insert', views.attendance_insert),
    path('attendance_update', views.attendance_update),
    path('attendance_viewall', views.attendance_viewall),
    path('attendance_viewsingle', views.attendance_viewsingle),
    path('attendance_delete', views.attendance_delete),

    # ---- Subjects ----
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_create, name='subject_create'),
    path('subjects/<int:subject_code>/edit/', views.subject_edit, name='subject_edit'),

    # Legacy subject URL
    path('subjects_viewall', views.subjects_viewall),

    # ---- Departments ----
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),

    # ---- Reports ----
    path('reports/', views.reports, name='reports'),

    # ---- Personal / Student ----
    path('my-attendance/', views.student_dashboard, name='my_attendance'),
    path('viewPersonal', views.viewPersonal),
]
