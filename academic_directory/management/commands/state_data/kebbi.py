# academic_directory/management/commands/state_data/kebbi.py
"""Universities in Kebbi State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Birnin Kebbi',
        'abbreviation': 'FUBK',
        'state': 'KEBBI',
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
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                ],
            },
        ],
    },
]
