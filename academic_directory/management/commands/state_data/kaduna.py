# academic_directory/management/commands/state_data/kaduna.py
"""Universities in Kaduna State. Add more universities to this list as needed."""

UNIVERSITIES = [
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
                    {'name': 'Electrical Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
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
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
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
                    {'name': 'Nursing Sciences', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Sciences', 'abbreviation': 'MLS'},
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                ],
            },
        ],
    },
]
