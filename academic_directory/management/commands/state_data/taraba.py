# academic_directory/management/commands/state_data/taraba.py
"""Universities and Polytechnics in Taraba State."""

UNIVERSITIES = [
    # FEDERAL UNIVERSITY, WUKARI
    {
        'name': 'Federal University, Wukari',
        'abbreviation': 'FUWUKARI',
        'state': 'TARABA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Physical Sciences',
                'abbreviation': 'PHS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                ],
            },
            {
                'name': 'Faculty of Agriculture and Life Science',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Biotechnology', 'abbreviation': 'BTC'},
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Crop Science', 'abbreviation': 'CPS'},
                    {'name': 'Soil Science', 'abbreviation': 'SLS'},
                ],
            },
            {
                'name': 'Faculty of Bio-Sciences',
                'abbreviation': 'BSC',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Plant Science and Biotechnology', 'abbreviation': 'PSB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Computing and Information System',
                'abbreviation': 'CIS',
                'departments': [
                    {'name': 'Information Technology', 'abbreviation': 'IT'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYS'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Health Education', 'abbreviation': 'HED'},
                    {'name': 'Physical Education', 'abbreviation': 'PED'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CIV'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEC'},
                ],
            },
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics', 'abbreviation': 'LIN'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Islamic Law', 'abbreviation': 'ISL'},
                    {'name': 'Public Law', 'abbreviation': 'PBL'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUS'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
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
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                ],
            },
        ],
    },
    
    # TARABA STATE UNIVERSITY, JALINGO
    {
        'name': 'Taraba State University',
        'abbreviation': 'TSU',
        'state': 'TARABA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEE'},
                    {'name': 'Agronomy', 'abbreviation': 'AGR'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Language and Linguistics', 'abbreviation': 'LL'},
                    {'name': 'History and Archeology', 'abbreviation': 'HIS'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts and Social Sciences Education', 'abbreviation': 'ASS'},
                    {'name': 'Science Education', 'abbreviation': 'SCI'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural and Bio-Resources Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CIV'},
                    {'name': 'Electrical and Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEC'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTS'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUS'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Political Science and International Relations', 'abbreviation': 'POL'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
    
    # FEDERAL POLYTECHNIC, BALI
    {
        'name': 'Federal Polytechnic, Bali',
        'abbreviation': 'FEDPOLYBALI',
        'state': 'TARABA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CIV'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Agric and Bio-environmental Engineering Technology', 'abbreviation': 'ABE'},
                ],
            },
            {
                'name': 'School of Applied Sciences',
                'abbreviation': 'APS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTS'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Animal Health and Production', 'abbreviation': 'AHP'},
                ],
            },
            {
                'name': 'School of Management Studies',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Management and Technology', 'abbreviation': 'BMT'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                ],
            },
            {
                'name': 'School of Agricultural Technology',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGT'},
                ],
            },
            {
                'name': 'School of Preliminary Studies',
                'abbreviation': 'PST',
                'departments': [
                    {'name': 'PRE-ND Science', 'abbreviation': 'PSC'},
                ],
            },
        ],
    },
    
    # TARABA STATE POLYTECHNIC, SUNTAI
    {
        'name': 'Taraba State Polytechnic, Suntai',
        'abbreviation': 'TARAPOLY',
        'state': 'TARABA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CIV'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEC'},
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
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SST',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                ],
            },
            {
                'name': 'School of Management Studies',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
            {
                'name': 'School of Agricultural Technology',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGT'},
                    {'name': 'Fisheries Technology', 'abbreviation': 'FIS'},
                    {'name': 'Forestry Technology', 'abbreviation': 'FOR'},
                ],
            },
        ],
    },
    
    # COLLEGE OF EDUCATION, ZING (treated as university per your instruction)
    {
        'name': 'College of Education, Zing',
        'abbreviation': 'COEZING',
        'state': 'TARABA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'Hausa Education', 'abbreviation': 'HAS'},
                    {'name': 'Arabic Education', 'abbreviation': 'ARB'},
                    {'name': 'French Education', 'abbreviation': 'FRN'},
                    {'name': 'Mumuye Education', 'abbreviation': 'MUM'},
                    {'name': 'Christian Religious Studies Education', 'abbreviation': 'CRS'},
                    {'name': 'Islamic Studies Education', 'abbreviation': 'ISL'},
                    {'name': 'History Education', 'abbreviation': 'HIS'},
                    {'name': 'Geography Education', 'abbreviation': 'GEO'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SST'},
                    {'name': 'Economics Education', 'abbreviation': 'ECO'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                    {'name': 'Physical and Health Education', 'abbreviation': 'PHE'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                    {'name': 'Fine and Applied Art Education', 'abbreviation': 'FAA'},
                    {'name': 'Technical Education', 'abbreviation': 'TED'},
                ],
            },
            {
                'name': 'School of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Early Childhood Care Education', 'abbreviation': 'ECE'},
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                ],
            },
        ],
    },
]