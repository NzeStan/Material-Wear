# academic_directory/management/commands/state_data/kebbi.py
"""Universities and Polytechnics in Kebbi State."""

UNIVERSITIES = [
    # FEDERAL UNIVERSITY, BIRNIN KEBBI
    {
        'name': 'Federal University, Birnin Kebbi',
        'abbreviation': 'FUBK',
        'state': 'KEBBI',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'History and International Relations', 'abbreviation': 'HIS'},
                    {'name': 'European Languages', 'abbreviation': 'EUL'},
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUS'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Demography and Social Statistics', 'abbreviation': 'DSS'},
                ],
            },
            {
                'name': 'Faculty of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Applied Geophysics', 'abbreviation': 'APH'},
                    {'name': 'Biochemistry and Molecular Biology', 'abbreviation': 'BCH'},
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Pure and Industrial Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Physics with Electronics', 'abbreviation': 'PHY'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                ],
            },
            {
                'name': 'College of Health Sciences',
                'abbreviation': 'CHS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MED'},
                    {'name': 'Nursing Sciences', 'abbreviation': 'NRS'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
    
    # KEBBI STATE UNIVERSITY OF SCIENCE AND TECHNOLOGY, ALIERO
    {
        'name': 'Kebbi State University of Science and Technology',
        'abbreviation': 'KSUSTA',
        'state': 'KEBBI',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Agronomy', 'abbreviation': 'AGR'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Fisheries and Aquaculture', 'abbreviation': 'FIS'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Biotechnology', 'abbreviation': 'BTC'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Environmental Science', 'abbreviation': 'ENV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Faculty of Arts and Humanities',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
        ],
    },
    
    # WAZIRI UMARU FEDERAL POLYTECHNIC, BIRNIN KEBBI
    {
        'name': 'Waziri Umaru Federal Polytechnic',
        'abbreviation': 'WUFPBK',
        'state': 'KEBBI',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Management and Administration',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CVE'},
                    {'name': 'Electrical/Electronics Engineering Technology', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering Technology', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'School of Environmental Studies',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Surveying and Geo-Informatics', 'abbreviation': 'SGV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
        ],
    },
    
    # COLLEGE OF EDUCATION, ARGUNGU
    {
        'name': 'College of Education, Argungu',
        'abbreviation': 'COEAR',
        'state': 'KEBBI',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arabic Education', 'abbreviation': 'ARB'},
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'Hausa Education', 'abbreviation': 'HAU'},
                    {'name': 'History Education', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies Education', 'abbreviation': 'ISL'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SST'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                ],
            },
        ],
    },
]