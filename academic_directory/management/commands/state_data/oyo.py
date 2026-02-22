# academic_directory/management/commands/state_data/oyo.py
"""
Universities in Oyo State.
Add more universities to this list as needed.
"""

UNIVERSITIES = [
    {
        'name': 'University of Ibadan',
        'abbreviation': 'UI',
        'state': 'OYO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Technology',
                'abbreviation': 'TECH',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Industrial and Production Engineering', 'abbreviation': 'IPE'},
                    {'name': 'Agricultural and Environmental Engineering', 'abbreviation': 'AEE'},
                    {'name': 'Wood Products Engineering', 'abbreviation': 'WPE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Botany and Microbiology', 'abbreviation': 'BMB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
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
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Communication and Language Arts', 'abbreviation': 'CLA'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                    {'name': 'Linguistics and African Languages', 'abbreviation': 'LAL'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
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
                'name': 'College of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                    {'name': 'Dentistry', 'abbreviation': 'DEN'},
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Teacher Education', 'abbreviation': 'TED'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GCS'},
                    {'name': 'Special Education', 'abbreviation': 'SPE'},
                    {'name': 'Library, Archival and Information Studies', 'abbreviation': 'LAI'},
                ],
            },
            {
                'name': 'Faculty of Agriculture and Forestry',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agronomy', 'abbreviation': 'AGN'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Soil Science and Land Resources Management', 'abbreviation': 'SSL'},
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEX'},
                    {'name': 'Crop Protection and Environmental Biology', 'abbreviation': 'CPB'},
                    {'name': 'Forestry and Environmental Management', 'abbreviation': 'FEM'},
                    {'name': 'Home Science, Nutrition and Dietetics', 'abbreviation': 'HND'},
                ],
            },
        ],
    },
]
