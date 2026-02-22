# academic_directory/management/commands/state_data/jigawa.py
"""Universities in Jigawa State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Dutse',
        'abbreviation': 'FUD',
        'state': 'JIGAWA',
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
                'name': 'Faculty of Humanities and Management Sciences',
                'abbreviation': 'HMS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                ],
            },
        ],
    },
]
