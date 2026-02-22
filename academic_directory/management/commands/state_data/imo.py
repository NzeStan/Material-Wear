# academic_directory/management/commands/state_data/imo.py
"""Universities in Imo State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University of Technology, Owerri',
        'abbreviation': 'FUTO',
        'state': 'IMO',
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
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Polymer and Textile Engineering', 'abbreviation': 'PTE'},
                ],
            },
            {
                'name': 'School of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Geosciences', 'abbreviation': 'GEO'},
                ],
            },
        ],
    },
]
