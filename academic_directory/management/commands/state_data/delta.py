# academic_directory/management/commands/state_data/delta.py
"""Universities in Delta State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University of Petroleum Resources, Effurun',
        'abbreviation': 'FUPRE',
        'state': 'DELTA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Chemical and Petroleum Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PTE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                ],
            },
        ],
    },
]
