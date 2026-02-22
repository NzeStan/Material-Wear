# academic_directory/management/commands/state_data/borno.py
"""Universities in Borno State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'University of Maiduguri',
        'abbreviation': 'UNIMAID',
        'state': 'BORNO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
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
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics', 'abbreviation': 'LIN'},
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
