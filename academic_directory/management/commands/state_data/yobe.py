# academic_directory/management/commands/state_data/yobe.py
"""Universities in Yobe State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Gashua',
        'abbreviation': 'FUGASHUA',
        'state': 'YOBE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Humanities and Social Sciences',
                'abbreviation': 'HSS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                ],
            },
        ],
    },
]
