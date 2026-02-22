# academic_directory/management/commands/state_data/bauchi.py
"""Universities in Bauchi State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Abubakar Tafawa Balewa University',
        'abbreviation': 'ATBU',
        'state': 'BAUCHI',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering and Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
        ],
    },
]
