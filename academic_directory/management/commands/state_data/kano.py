# academic_directory/management/commands/state_data/kano.py
"""
Universities in Kano State.
Add more universities to this list as needed.
"""

UNIVERSITIES = [
    {
        'name': 'Bayero University, Kano',
        'abbreviation': 'BUK',
        'state': 'KANO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
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
