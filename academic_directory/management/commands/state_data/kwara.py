# academic_directory/management/commands/state_data/kwara.py
"""Universities in Kwara State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'University of Ilorin',
        'abbreviation': 'UNILORIN',
        'state': 'KWARA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Agricultural and Biosystems Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Biomedical Engineering', 'abbreviation': 'BME'},
                ],
            },
            {
                'name': 'Faculty of Physical Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Geology and Mineral Sciences', 'abbreviation': 'GMS'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Business and Entrepreneurship', 'abbreviation': 'BEP'},
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
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                ],
            },
        ],
    },
]
