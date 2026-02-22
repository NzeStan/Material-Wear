# academic_directory/management/commands/state_data/nasarawa.py
"""Universities in Nasarawa State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Lafia',
        'abbreviation': 'FULAFIA',
        'state': 'NASARAWA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                ],
            },
            {
                'name': 'Faculty of Humanities and Social Sciences',
                'abbreviation': 'HSS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
]
