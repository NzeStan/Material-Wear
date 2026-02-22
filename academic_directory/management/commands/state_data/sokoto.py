# academic_directory/management/commands/state_data/sokoto.py
"""Universities in Sokoto State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Usmanu Danfodiyo University',
        'abbreviation': 'UDUSOK',
        'state': 'SOKOTO',
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
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Arts and Islamic Studies',
                'abbreviation': 'AIS',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                    {'name': 'English', 'abbreviation': 'ENG'},
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
