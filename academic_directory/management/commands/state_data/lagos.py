# academic_directory/management/commands/state_data/lagos.py
"""
Universities in Lagos State.
Add more universities to this list as needed.
"""

UNIVERSITIES = [
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
]
