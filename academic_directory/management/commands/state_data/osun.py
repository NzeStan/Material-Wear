# academic_directory/management/commands/state_data/osun.py
"""Universities in Osun State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Obafemi Awolowo University',
        'abbreviation': 'OAU',
        'state': 'OSUN',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Technology',
                'abbreviation': 'TECH',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronic Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Science and Engineering', 'abbreviation': 'CSE'},
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Materials Science and Engineering', 'abbreviation': 'MSE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics and Engineering Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology and Anthropology', 'abbreviation': 'SOA'},
                    {'name': 'Demography and Social Statistics', 'abbreviation': 'DSS'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'College of Health Sciences',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                    {'name': 'Dentistry', 'abbreviation': 'DEN'},
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                ],
            },
        ],
    },
]
