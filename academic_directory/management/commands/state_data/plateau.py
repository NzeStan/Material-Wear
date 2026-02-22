# academic_directory/management/commands/state_data/plateau.py
"""Universities in Plateau State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'University of Jos',
        'abbreviation': 'UNIJOS',
        'state': 'PLATEAU',
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
                ],
            },
            {
                'name': 'Faculty of Natural Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
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
                'name': 'Faculty of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                ],
            },
        ],
    },
]
