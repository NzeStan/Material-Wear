# academic_directory/management/commands/state_data/zamfara.py
"""Universities in Zamfara State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Gusau',
        'abbreviation': 'FUGUSAU',
        'state': 'ZAMFARA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
]
