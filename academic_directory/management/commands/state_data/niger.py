# academic_directory/management/commands/state_data/niger.py
"""Universities in Niger State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University of Technology, Minna',
        'abbreviation': 'FUTMINNA',
        'state': 'NIGER',
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
                    {'name': 'Agricultural and Bioresources Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                ],
            },
        ],
    },
]
