# academic_directory/management/commands/state_data/benue.py
"""Universities in Benue State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'University of Agriculture, Makurdi',
        'abbreviation': 'UAM',
        'state': 'BENUE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'College of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural and Environmental Engineering', 'abbreviation': 'AEE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Food and Bioprocess Engineering', 'abbreviation': 'FBE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'College of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
]
