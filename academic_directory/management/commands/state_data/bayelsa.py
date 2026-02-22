# academic_directory/management/commands/state_data/bayelsa.py
"""Universities in Bayelsa State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Otuoke',
        'abbreviation': 'FUOTUOKE',
        'state': 'BAYELSA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
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
                ],
            },
            {
                'name': 'Faculty of Humanities and Social Sciences',
                'abbreviation': 'HSS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
]
