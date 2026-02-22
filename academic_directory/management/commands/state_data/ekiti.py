# academic_directory/management/commands/state_data/ekiti.py
"""Universities in Ekiti State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Oye-Ekiti',
        'abbreviation': 'FUOYE',
        'state': 'EKITI',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
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
                ],
            },
            {
                'name': 'Faculty of Arts and Humanities',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English and Literary Studies', 'abbreviation': 'ELS'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Religious and Cultural Studies', 'abbreviation': 'RCS'},
                ],
            },
        ],
    },
]
