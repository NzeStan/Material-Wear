# academic_directory/management/commands/state_data/abia.py
"""Universities in Abia State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Michael Okpara University of Agriculture, Umudike',
        'abbreviation': 'MOUAU',
        'state': 'ABIA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'College of Engineering and Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural and Bioresources Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronic Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Food Science and Technology', 'abbreviation': 'FST'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'College of Natural Sciences',
                'abbreviation': 'NAT',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
]
