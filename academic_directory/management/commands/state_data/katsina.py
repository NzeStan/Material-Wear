# academic_directory/management/commands/state_data/katsina.py
"""Universities in Katsina State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Dutsin-Ma',
        'abbreviation': 'FUDMA',
        'state': 'KATSINA',
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
                'name': 'Faculty of Humanities and Education',
                'abbreviation': 'HED',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Education', 'abbreviation': 'EDU'},
                ],
            },
        ],
    },
]
