# academic_directory/management/commands/populate_academic_data.py
"""
Management command: populate_academic_data

Seeds the database with Nigerian universities, their faculties, and departments.
Safe to run multiple times — uses get_or_create so existing records are untouched.

Usage:
    python manage.py populate_academic_data             # seed everything
    python manage.py populate_academic_data --dry-run   # preview only
    python manage.py populate_academic_data --university UNN  # seed one university
"""
from django.core.management.base import BaseCommand
from django.db import transaction

# ---------------------------------------------------------------------------
# Data: universities → faculties → departments
# Structure: { 'name': ..., 'abbreviation': ..., 'state': ..., 'type': ...,
#              'faculties': [ { 'name': ..., 'abbreviation': ...,
#                               'departments': [ { 'name': ..., 'abbreviation': ... } ] } ] }
# ---------------------------------------------------------------------------
UNIVERSITIES = [
    # =========================================================
    # FEDERAL UNIVERSITIES
    # =========================================================
    {
        'name': 'University of Nigeria, Nsukka',
        'abbreviation': 'UNN',
        'state': 'ENUGU',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Agricultural and Bioresources Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electronic Engineering', 'abbreviation': 'ELN'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics and Astronomy', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology and Environmental Biology', 'abbreviation': 'ZEB'},
                    {'name': 'Plant Science and Biotechnology', 'abbreviation': 'PSB'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology and Anthropology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Social Work', 'abbreviation': 'SWK'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English and Literary Studies', 'abbreviation': 'ELS'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Linguistics, Igbo and Other Nigerian Languages', 'abbreviation': 'LNG'},
                    {'name': 'Music', 'abbreviation': 'MUS'},
                    {'name': 'Theatre and Film Studies', 'abbreviation': 'TFS'},
                    {'name': 'Fine and Applied Arts', 'abbreviation': 'FAA'},
                    {'name': 'Foreign Languages', 'abbreviation': 'FLA'},
                    {'name': 'Religion and Cultural Studies', 'abbreviation': 'RCS'},
                ],
            },
            {
                'name': 'Faculty of Business Administration',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Management', 'abbreviation': 'MGT'},
                    {'name': 'Public Administration and Local Government', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'Faculty of Medical Sciences',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                    {'name': 'Pharmacology and Therapeutics', 'abbreviation': 'PHT'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                ],
            },
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agronomy', 'abbreviation': 'AGN'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Soil Science and Land Resources Management', 'abbreviation': 'SSL'},
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEE'},
                    {'name': 'Crop Science', 'abbreviation': 'CRP'},
                    {'name': 'Forestry and Environmental Management', 'abbreviation': 'FEM'},
                    {'name': 'Home Science, Nutrition and Dietetics', 'abbreviation': 'HND'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Science Education', 'abbreviation': 'SCE'},
                    {'name': 'Social Science Education', 'abbreviation': 'SSE'},
                    {'name': 'Arts Education', 'abbreviation': 'ARE'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Vocational Teacher Education', 'abbreviation': 'VTE'},
                    {'name': 'Health and Physical Education', 'abbreviation': 'HPE'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                ],
            },
        ],
    },

    {
        'name': 'University of Benin',
        'abbreviation': 'UNIBEN',
        'state': 'EDO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PTE'},
                    {'name': 'Production Engineering', 'abbreviation': 'PRE'},
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Biomedical Engineering', 'abbreviation': 'BME'},
                    {'name': 'Materials and Metallurgical Engineering', 'abbreviation': 'MME'},
                    {'name': 'Structural Engineering', 'abbreviation': 'STE'},
                    {'name': 'Systems Engineering', 'abbreviation': 'SYE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Plant Biology and Biotechnology', 'abbreviation': 'PBB'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science and Public Administration', 'abbreviation': 'PPA'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology and Anthropology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Geography and Regional Planning', 'abbreviation': 'GRP'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English and Literature', 'abbreviation': 'ELT'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Languages and Linguistics', 'abbreviation': 'LNG'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                    {'name': 'Fine Arts', 'abbreviation': 'FAA'},
                    {'name': 'Religious Studies', 'abbreviation': 'RES'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Office and Information Management', 'abbreviation': 'OIM'},
                    {'name': 'Tourism and Hospitality Management', 'abbreviation': 'THM'},
                ],
            },
            {
                'name': 'Faculty of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Pharmacology', 'abbreviation': 'PHT'},
                    {'name': 'Medical Biochemistry', 'abbreviation': 'MBX'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Psychology and Curriculum Studies', 'abbreviation': 'EPC'},
                    {'name': 'Adult and Non-Formal Education', 'abbreviation': 'ANF'},
                    {'name': 'Vocational and Technical Education', 'abbreviation': 'VTE'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GCS'},
                ],
            },
        ],
    },

    {
        'name': 'University of Lagos',
        'abbreviation': 'UNILAG',
        'state': 'LAGOS',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical and Polymer Engineering', 'abbreviation': 'CPO'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Marine Engineering', 'abbreviation': 'MRE'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                    {'name': 'Systems Engineering', 'abbreviation': 'SYE'},
                    {'name': 'Surveying and Geoinformatics', 'abbreviation': 'SRV'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Cell Biology and Genetics', 'abbreviation': 'CBG'},
                    {'name': 'Marine Sciences', 'abbreviation': 'MRS'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History and Strategic Studies', 'abbreviation': 'HSS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Linguistics, African and Asian Studies', 'abbreviation': 'LAA'},
                    {'name': 'Creative Arts', 'abbreviation': 'CRA'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                ],
            },
            {
                'name': 'Faculty of Business Administration',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Management and Organisational Behaviour', 'abbreviation': 'MOB'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Actuarial Science and Insurance', 'abbreviation': 'ASI'},
                    {'name': 'Industrial Relations and Personnel Management', 'abbreviation': 'IRP'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'College of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                    {'name': 'Dental and Maxillofacial Surgery', 'abbreviation': 'DMS'},
                    {'name': 'Physiotherapy', 'abbreviation': 'PHT'},
                    {'name': 'Radiology', 'abbreviation': 'RAD'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts and Social Sciences Education', 'abbreviation': 'ASE'},
                    {'name': 'Educational Administration and Planning', 'abbreviation': 'EAP'},
                    {'name': 'Science and Technology Education', 'abbreviation': 'STE'},
                    {'name': 'Human Kinetics and Health Education', 'abbreviation': 'HKH'},
                    {'name': 'Physical and Health Education', 'abbreviation': 'PHE'},
                ],
            },
        ],
    },

    {
        'name': 'University of Ibadan',
        'abbreviation': 'UI',
        'state': 'OYO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Technology',
                'abbreviation': 'TECH',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Industrial and Production Engineering', 'abbreviation': 'IPE'},
                    {'name': 'Agricultural and Environmental Engineering', 'abbreviation': 'AEE'},
                    {'name': 'Wood Products Engineering', 'abbreviation': 'WPE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Botany and Microbiology', 'abbreviation': 'BMB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Communication and Language Arts', 'abbreviation': 'CLA'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Linguistics and African Languages', 'abbreviation': 'LAL'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'College of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                    {'name': 'Dentistry', 'abbreviation': 'DEN'},
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Teacher Education', 'abbreviation': 'TED'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GCS'},
                    {'name': 'Special Education', 'abbreviation': 'SPE'},
                    {'name': 'Library, Archival and Information Studies', 'abbreviation': 'LAI'},
                ],
            },
        ],
    },

    {
        'name': 'University of Port Harcourt',
        'abbreviation': 'UNIPORT',
        'state': 'RIVERS',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical and Petrochemical Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'COE'},
                    {'name': 'Marine Engineering', 'abbreviation': 'MRE'},
                    {'name': 'Gas Engineering', 'abbreviation': 'GSE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political and Administrative Studies', 'abbreviation': 'PAS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                ],
            },
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English and Communication Studies', 'abbreviation': 'ECS'},
                    {'name': 'History and Diplomatic Studies', 'abbreviation': 'HDS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Linguistics and Communication Studies', 'abbreviation': 'LCS'},
                    {'name': 'Theatre and Film Studies', 'abbreviation': 'TFS'},
                    {'name': 'Fine and Performing Arts', 'abbreviation': 'FPA'},
                    {'name': 'Religious and Cultural Studies', 'abbreviation': 'RCS'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Finance and Banking', 'abbreviation': 'FBK'},
                    {'name': 'Management', 'abbreviation': 'MGT'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
        ],
    },

    {
        'name': 'Ahmadu Bello University',
        'abbreviation': 'ABU',
        'state': 'KADUNA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Computer Engineering', 'abbreviation': 'ECE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                    {'name': 'Water Resources and Environmental Engineering', 'abbreviation': 'WRE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                ],
            },
            {
                'name': 'Faculty of Arts and Islamic Studies',
                'abbreviation': 'AIS',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                    {'name': 'English and French', 'abbreviation': 'ENF'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Nigerian Languages', 'abbreviation': 'NGL'},
                ],
            },
            {
                'name': 'Faculty of Administration',
                'abbreviation': 'ADM',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                ],
            },
        ],
    },

    {
        'name': 'Obafemi Awolowo University',
        'abbreviation': 'OAU',
        'state': 'OSUN',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Technology',
                'abbreviation': 'TECH',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronic Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Science and Engineering', 'abbreviation': 'CSE'},
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Food Science and Technology', 'abbreviation': 'FST'},
                    {'name': 'Materials Science and Engineering', 'abbreviation': 'MSE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics and Engineering Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry and Molecular Biology', 'abbreviation': 'BCH'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology and Anthropology', 'abbreviation': 'SOC'},
                    {'name': 'Demography and Social Statistics', 'abbreviation': 'DSS'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Linguistics and African Languages', 'abbreviation': 'LAL'},
                    {'name': 'Dramatic Arts', 'abbreviation': 'DRA'},
                    {'name': 'Music', 'abbreviation': 'MUS'},
                    {'name': 'Fine Arts', 'abbreviation': 'FAA'},
                ],
            },
            {
                'name': 'Faculty of Administration',
                'abbreviation': 'ADM',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Management and Accounting', 'abbreviation': 'MAA'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'College of Health Sciences',
                'abbreviation': 'CHS',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Dental and Maxillofacial Surgery', 'abbreviation': 'DMS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                ],
            },
        ],
    },

    {
        'name': 'Nnamdi Azikiwe University',
        'abbreviation': 'UNIZIK',
        'state': 'ANAMBRA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Agricultural and Bioenvironmental Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Geology and Mining Engineering', 'abbreviation': 'GME'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                ],
            },
            {
                'name': 'Faculty of Natural Sciences',
                'abbreviation': 'NSC',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics and Industrial Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology and Anthropology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English and Literary Studies', 'abbreviation': 'ELS'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Linguistics', 'abbreviation': 'LNG'},
                    {'name': 'Music', 'abbreviation': 'MUS'},
                    {'name': 'Fine and Applied Arts', 'abbreviation': 'FAA'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
        ],
    },

    {
        'name': 'University of Ilorin',
        'abbreviation': 'UNILORIN',
        'state': 'KWARA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENGTECH',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Biomedical Engineering', 'abbreviation': 'BME'},
                    {'name': 'Food Engineering', 'abbreviation': 'FDE'},
                    {'name': 'Materials and Metallurgical Engineering', 'abbreviation': 'MME'},
                    {'name': 'Water Resources and Environmental Engineering', 'abbreviation': 'WRE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology and Biotechnology', 'abbreviation': 'MCB'},
                    {'name': 'Geology and Mineral Sciences', 'abbreviation': 'GMS'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Plant Biology', 'abbreviation': 'PLB'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Geography and Environmental Management', 'abbreviation': 'GEM'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics and Nigerian Languages', 'abbreviation': 'LNL'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'Performing Arts', 'abbreviation': 'PEA'},
                    {'name': 'Fine Arts', 'abbreviation': 'FAA'},
                ],
            },
            {
                'name': 'Faculty of Business and Social Sciences',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
        ],
    },

    # =========================================================
    # STATE UNIVERSITIES
    # =========================================================
    {
        'name': 'Lagos State University',
        'abbreviation': 'LASU',
        'state': 'LAGOS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical and Polymer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'COE'},
                    {'name': 'Mechatronics Engineering', 'abbreviation': 'MEC'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Geography and Planning', 'abbreviation': 'GAP'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Industrial Relations and Personnel Management', 'abbreviation': 'IRP'},
                    {'name': 'Transport Management', 'abbreviation': 'TRM'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
        ],
    },

    # =========================================================
    # PRIVATE UNIVERSITIES
    # =========================================================
    {
        'name': 'Covenant University',
        'abbreviation': 'COVENANT',
        'state': 'OGUN',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'College of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Information Engineering', 'abbreviation': 'EIE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer and Information Sciences', 'abbreviation': 'CIS'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PTE'},
                ],
            },
            {
                'name': 'College of Science and Technology',
                'abbreviation': 'CST',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                ],
            },
            {
                'name': 'College of Business and Social Sciences',
                'abbreviation': 'CBS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Economics and Development Studies', 'abbreviation': 'EDS'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                ],
            },
        ],
    },

    {
        'name': 'Federal University of Technology, Akure',
        'abbreviation': 'FUTA',
        'state': 'ONDO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering and Engineering Technology',
                'abbreviation': 'SEET',
                'departments': [
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CEE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                    {'name': 'Industrial and Production Engineering', 'abbreviation': 'IPE'},
                    {'name': 'Marine Technology', 'abbreviation': 'MRT'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCOS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematical Sciences', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Biophysics', 'abbreviation': 'BIP'},
                ],
            },
            {
                'name': 'School of Earth and Mineral Sciences',
                'abbreviation': 'SEMS',
                'departments': [
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Geophysics', 'abbreviation': 'GPH'},
                    {'name': 'Remote Sensing and Geoscience', 'abbreviation': 'RSG'},
                    {'name': 'Mining Engineering', 'abbreviation': 'MNE'},
                    {'name': 'Meteorology', 'abbreviation': 'MET'},
                ],
            },
            {
                'name': 'School of Management Technology',
                'abbreviation': 'SMAT',
                'departments': [
                    {'name': 'Project Management Technology', 'abbreviation': 'PMT'},
                    {'name': 'Information Management Technology', 'abbreviation': 'IMT'},
                    {'name': 'Transport Management Technology', 'abbreviation': 'TMT'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = (
        "Seed the database with Nigerian universities, faculties, and departments.\n"
        "Safe to run multiple times — uses get_or_create so existing records are preserved.\n\n"
        "Examples:\n"
        "  python manage.py populate_academic_data\n"
        "  python manage.py populate_academic_data --dry-run\n"
        "  python manage.py populate_academic_data --university UNN\n"
        "  python manage.py populate_academic_data --university UNILAG --university UNIBEN"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be created without writing to the database.',
        )
        parser.add_argument(
            '--university',
            action='append',
            metavar='ABBREVIATION',
            dest='universities',
            help='Only seed the specified university (by abbreviation). Repeatable.',
        )

    def handle(self, *args, **options):
        from academic_directory.models import University, Faculty, Department

        dry_run = options['dry_run']
        filter_universities = [u.upper() for u in (options.get('universities') or [])]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be saved.\n"))

        data = UNIVERSITIES
        if filter_universities:
            data = [u for u in data if u['abbreviation'] in filter_universities]
            if not data:
                self.stderr.write(
                    self.style.ERROR(
                        f"No matching universities found for: {filter_universities}\n"
                        f"Available: {[u['abbreviation'] for u in UNIVERSITIES]}"
                    )
                )
                return

        total_universities = 0
        total_faculties = 0
        total_departments = 0

        try:
            with transaction.atomic():
                for uni_data in data:
                    uni_label = f"{uni_data['abbreviation']} ({uni_data['name']})"

                    if dry_run:
                        self.stdout.write(f"  [University] {uni_label}")
                    else:
                        uni, uni_created = University.objects.get_or_create(
                            abbreviation=uni_data['abbreviation'],
                            defaults={
                                'name': uni_data['name'],
                                'state': uni_data['state'],
                                'type': uni_data['type'],
                                'is_active': True,
                            },
                        )
                        if uni_created:
                            total_universities += 1
                            self.stdout.write(
                                self.style.SUCCESS(f"  ✅ Created University: {uni_label}")
                            )
                        else:
                            self.stdout.write(f"  ⏩ Skipped (exists): University {uni_label}")

                    for fac_data in uni_data.get('faculties', []):
                        fac_label = f"{fac_data['abbreviation']} — {fac_data['name']}"

                        if dry_run:
                            self.stdout.write(f"    [Faculty] {fac_label}")
                        else:
                            fac, fac_created = Faculty.objects.get_or_create(
                                university=uni,
                                name=fac_data['name'],
                                defaults={
                                    'abbreviation': fac_data['abbreviation'],
                                    'is_active': True,
                                },
                            )
                            if fac_created:
                                total_faculties += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f"    ✅ Created Faculty: {fac_label}")
                                )
                            else:
                                self.stdout.write(f"    ⏩ Skipped (exists): Faculty {fac_label}")

                        for dept_data in fac_data.get('departments', []):
                            dept_label = f"{dept_data['abbreviation']} — {dept_data['name']}"

                            if dry_run:
                                self.stdout.write(f"      [Dept] {dept_label}")
                            else:
                                dept, dept_created = Department.objects.get_or_create(
                                    faculty=fac,
                                    name=dept_data['name'],
                                    defaults={
                                        'abbreviation': dept_data['abbreviation'],
                                        'is_active': True,
                                    },
                                )
                                if dept_created:
                                    total_departments += 1
                                    self.stdout.write(
                                        self.style.SUCCESS(f"      ✅ Created Dept: {dept_label}")
                                    )
                                else:
                                    self.stdout.write(
                                        f"      ⏩ Skipped (exists): Dept {dept_label}"
                                    )

                if dry_run:
                    raise Exception("dry-run-rollback")

        except Exception as exc:
            if dry_run:
                self.stdout.write(self.style.WARNING("\nDry run complete — no data written."))
                return
            self.stderr.write(self.style.ERROR(f"Error during seeding: {exc}"))
            raise

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done! Created: {total_universities} universities, "
            f"{total_faculties} faculties, {total_departments} departments."
        ))
        if total_universities == 0 and total_faculties == 0 and total_departments == 0:
            self.stdout.write("All records already exist — nothing new to create.")
