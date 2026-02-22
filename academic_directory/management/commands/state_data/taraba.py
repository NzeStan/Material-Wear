# academic_directory/management/commands/state_data/taraba.py
"""Universities in Taraba State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Wukari',
        'abbreviation': 'FUWUKARI',
        'state': 'TARABA',
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
                'name': 'Faculty of Humanities and Social Sciences',
                'abbreviation': 'HSS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                ],
            },
        ],
    },
]
