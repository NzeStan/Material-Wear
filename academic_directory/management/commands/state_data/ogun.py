# academic_directory/management/commands/state_data/ogun.py
"""
Universities in Ogun State.
Add more universities to this list as needed.
"""

UNIVERSITIES = [
    {
        'name': 'Covenant University',
        'abbreviation': 'COVENANT',
        'state': 'OGUN',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'College of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Information Engineering', 'abbreviation': 'EIE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer and Information Sciences', 'abbreviation': 'CIS'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PTE'},
                ],
            },
            {
                'name': 'College of Science and Technology',
                'abbreviation': 'CST',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                ],
            },
            {
                'name': 'College of Business and Social Sciences',
                'abbreviation': 'CBS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Economics and Development Studies', 'abbreviation': 'EDS'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                ],
            },
        ],
    },
]
