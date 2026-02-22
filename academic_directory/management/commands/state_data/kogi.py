# academic_directory/management/commands/state_data/kogi.py
"""Universities in Kogi State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Federal University, Lokoja',
        'abbreviation': 'FULOKOJA',
        'state': 'KOGI',
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
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                ],
            },
            {
                'name': 'Faculty of Humanities and Social Sciences',
                'abbreviation': 'HSS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
]
