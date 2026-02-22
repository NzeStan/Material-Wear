# academic_directory/management/commands/state_data/ondo.py
"""
Universities in Ondo State.
Add more universities to this list as needed.
"""

UNIVERSITIES = [
    {
        'name': 'Federal University of Technology, Akure',
        'abbreviation': 'FUTA',
        'state': 'ONDO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering and Engineering Technology',
                'abbreviation': 'SEET',
                'departments': [
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CEE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                    {'name': 'Mining Engineering', 'abbreviation': 'MNE'},
                    {'name': 'Industrial and Production Engineering', 'abbreviation': 'IPE'},
                    {'name': 'Marine Technology', 'abbreviation': 'MRT'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCOS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematical Sciences', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Biophysics', 'abbreviation': 'BIP'},
                ],
            },
            {
                'name': 'School of Earth and Mineral Sciences',
                'abbreviation': 'SEMS',
                'departments': [
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Geophysics', 'abbreviation': 'GPH'},
                    {'name': 'Remote Sensing and Geoscience', 'abbreviation': 'RSG'},
                    {'name': 'Mining Engineering', 'abbreviation': 'MNE'},
                    {'name': 'Meteorology', 'abbreviation': 'MET'},
                ],
            },
            {
                'name': 'School of Management Technology',
                'abbreviation': 'SMAT',
                'departments': [
                    {'name': 'Project Management Technology', 'abbreviation': 'PMT'},
                    {'name': 'Information Management Technology', 'abbreviation': 'IMT'},
                    {'name': 'Transport Management Technology', 'abbreviation': 'TMT'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                ],
            },
        ],
    },
]
