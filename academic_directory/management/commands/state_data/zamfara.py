# academic_directory/management/commands/state_data/zamfara.py
"""Universities and Polytechnics in Zamfara State."""

UNIVERSITIES = [
    # FEDERAL UNIVERSITY, GUSAU
    {
        'name': 'Federal University, Gusau',
        'abbreviation': 'FUGUSAU',
        'state': 'ZAMFARA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Plant Science and Biotechnology', 'abbreviation': 'PSB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English Language', 'abbreviation': 'ENG'},
                    {'name': 'Arabic Language', 'abbreviation': 'ARB'},
                    {'name': 'Arabic Literature', 'abbreviation': 'ARL'},
                    {'name': 'Hausa Studies', 'abbreviation': 'HAS'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                ],
            },
            {
                'name': 'Faculty of Management and Social Sciences',
                'abbreviation': 'MSS',
                'departments': [
                    {'name': 'Accounting and Finance', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUS'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Educational Psychology', 'abbreviation': 'EDP'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Research Measurement and Evaluation', 'abbreviation': 'RME'},
                    {'name': 'Sociology of Education', 'abbreviation': 'SED'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
    
    # ZAMFARA STATE UNIVERSITY, TALATA MAFARA
    {
        'name': 'Zamfara State University',
        'abbreviation': 'ZAMSU',
        'state': 'ZAMFARA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Nursing Sciences', 'abbreviation': 'NSC'},
                    {'name': 'Public Health', 'abbreviation': 'PBH'},
                    {'name': 'Physiotherapy', 'abbreviation': 'PHT'},
                    {'name': 'Human Nutrition and Dietetics', 'abbreviation': 'HND'},
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
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Biochemistry and Molecular Biology', 'abbreviation': 'BMB'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Electronics', 'abbreviation': 'ELE'},
                ],
            },
            {
                'name': 'Faculty of Management and Social Sciences',
                'abbreviation': 'MSS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                ],
            },
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Early Child Education', 'abbreviation': 'ECE'},
                    {'name': 'Primary Education', 'abbreviation': 'PED'},
                ],
            },
        ],
    },
    
    # FEDERAL POLYTECHNIC, KAURA NAMODA
    {
        'name': 'Federal Polytechnic, Kaura Namoda',
        'abbreviation': 'FEDPONAM',
        'state': 'ZAMFARA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Business and Management Studies',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CIV'},
                    {'name': 'Electrical/Electronic Engineering Technology', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering Technology', 'abbreviation': 'MEC'},
                    {'name': 'Agricultural Engineering Technology', 'abbreviation': 'AGE'},
                ],
            },
            {
                'name': 'School of Environmental Studies',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management and Valuation', 'abbreviation': 'EST'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Information and Communication Technology',
                'abbreviation': 'ICT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SST',
                'departments': [
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                ],
            },
            {
                'name': 'School of General Studies',
                'abbreviation': 'GST',
                'departments': [
                    {'name': 'Languages', 'abbreviation': 'LAN'},
                    {'name': 'Social Sciences', 'abbreviation': 'SOC'},
                ],
            },
            {
                'name': 'School of Remedial and Basic Studies',
                'abbreviation': 'RBS',
                'departments': [
                    {'name': 'Remedial Science', 'abbreviation': 'RSC'},
                    {'name': 'Remedial Arts', 'abbreviation': 'RAR'},
                ],
            },
        ],
    },
    
    # ZAMFARA STATE COLLEGE OF EDUCATION, MARU (treated as university per your instruction)
    {
        'name': 'Zamfara State College of Education, Maru',
        'abbreviation': 'ZACOEM',
        'state': 'ZAMFARA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Science Education',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Geography Education', 'abbreviation': 'GEO'},
                    {'name': 'Computer Education', 'abbreviation': 'CSC'},
                ],
            },
            {
                'name': 'School of Arts and Social Sciences Education',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Language Education', 'abbreviation': 'ENG'},
                    {'name': 'Hausa Language Education', 'abbreviation': 'HAS'},
                    {'name': 'Arabic Language Education', 'abbreviation': 'ARB'},
                    {'name': 'Islamic Studies Education', 'abbreviation': 'ISL'},
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                ],
            },
        ],
    },
]