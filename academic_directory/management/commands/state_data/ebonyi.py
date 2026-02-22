# academic_directory/management/commands/state_data/ebonyi.py
"""Universities in Ebonyi State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Ndufu-Alike',
        'abbreviation': 'FUNAI',
        'state': 'EBONYI',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Information Engineering', 'abbreviation': 'EIE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Computer Science and Informatics', 'abbreviation': 'CSI'},
                ],
            },
            {
                'name': 'Faculty of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
]
