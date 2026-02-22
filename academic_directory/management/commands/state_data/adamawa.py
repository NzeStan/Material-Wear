# academic_directory/management/commands/state_data/adamawa.py
"""Universities in Adamawa State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Modibbo Adama University',
        'abbreviation': 'MAUTECH',
        'state': 'ADAMAWA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Technology',
                'abbreviation': 'TECH',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Science and Information Technology', 'abbreviation': 'CSI'},
                ],
            },
            {
                'name': 'School of Pure and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                ],
            },
        ],
    },
]
