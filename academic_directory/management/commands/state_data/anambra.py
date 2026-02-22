# academic_directory/management/commands/state_data/anambra.py
"""Universities in Anambra State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Nnamdi Azikiwe University',
        'abbreviation': 'UNIZIK',
        'state': 'ANAMBRA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electronic and Computer Engineering', 'abbreviation': 'ECE'},
                    {'name': 'Polymer and Textile Engineering', 'abbreviation': 'PTE'},
                ],
            },
            {
                'name': 'Faculty of Physical Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics and Industrial Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                ],
            },
            {
                'name': 'Faculty of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
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
