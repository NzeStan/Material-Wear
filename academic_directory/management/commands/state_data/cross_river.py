# academic_directory/management/commands/state_data/cross_river.py
"""Universities in Cross River State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'University of Calabar',
        'abbreviation': 'UNICAL',
        'state': 'CROSS_RIVER',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical and Petroleum Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'COE'},
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
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
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
