# academic_directory/management/commands/state_data/ondo.py
"""Universities and Polytechnics in Ondo State."""

UNIVERSITIES = [
    # FEDERAL UNIVERSITY OF TECHNOLOGY, AKURE
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
                    {'name': 'Mathematical Sciences', 'abbreviation': 'MTS'},
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
            {
                'name': 'School of Agriculture and Agricultural Technology',
                'abbreviation': 'SAAT',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Production and Health', 'abbreviation': 'APH'},
                    {'name': 'Crop, Soil and Pest Management', 'abbreviation': 'CSP'},
                    {'name': 'Food Science and Technology', 'abbreviation': 'FST'},
                ],
            },
            {
                'name': 'School of Environmental Technology',
                'abbreviation': 'SET',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Health and Health Technology',
                'abbreviation': 'SHHT',
                'departments': [
                    {'name': 'Biomedical Technology', 'abbreviation': 'BMT'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                ],
            },
        ],
    },
    
    # ADEKUNLE AJASIN UNIVERSITY
    {
        'name': 'Adekunle Ajasin University',
        'abbreviation': 'AAUA',
        'state': 'ONDO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Studies', 'abbreviation': 'ENG'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics and Languages', 'abbreviation': 'LNL'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematical Sciences', 'abbreviation': 'MTS'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Plant Science', 'abbreviation': 'PLS'},
                    {'name': 'Animal and Environmental Biology', 'abbreviation': 'AEB'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Social Science Education', 'abbreviation': 'SSE'},
                    {'name': 'Vocational and Technical Education', 'abbreviation': 'VTE'},
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
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Crop Science', 'abbreviation': 'CPS'},
                ],
            },
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
    
    # ONDO STATE UNIVERSITY OF SCIENCE AND TECHNOLOGY
    {
        'name': 'Ondo State University of Science and Technology',
        'abbreviation': 'OSUSTECH',
        'state': 'ONDO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematical Sciences', 'abbreviation': 'MTS'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                ],
            },
            {
                'name': 'Faculty of Engineering and Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                ],
            },
        ],
    },
    
    # ELIZADE UNIVERSITY
    {
        'name': 'Elizade University',
        'abbreviation': 'ELIZADE',
        'state': 'ONDO',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                ],
            },
            {
                'name': 'Faculty of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Information Technology', 'abbreviation': 'IT'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                ],
            },
            {
                'name': 'Faculty of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
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
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                ],
            },
        ],
    },
    
    # ACHIEVERS UNIVERSITY
    {
        'name': 'Achievers University',
        'abbreviation': 'ACHIEVERS',
        'state': 'ONDO',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                ],
            },
        ],
    },
    
    # RUFUS GIWA POLYTECHNIC
    {
        'name': 'Rufus Giwa Polytechnic',
        'abbreviation': 'RUGIPO',
        'state': 'ONDO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural and Bio-Environmental Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering Technology', 'abbreviation': 'CPE'},
                    {'name': 'Electrical Engineering Technology', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering Technology', 'abbreviation': 'MEE'},
                    {'name': 'Mechatronics Engineering Technology', 'abbreviation': 'MTR'},
                    {'name': 'Welding and Fabrication Engineering', 'abbreviation': 'WFE'},
                    {'name': 'Marine Engineering', 'abbreviation': 'MRE'},
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
                    {'name': 'Art and Industrial Design', 'abbreviation': 'AID'},
                ],
            },
            {
                'name': 'School of Management Studies',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Insurance', 'abbreviation': 'INS'},
                    {'name': 'Taxation', 'abbreviation': 'TAX'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SST',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTS'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Food Science and Technology', 'abbreviation': 'FST'},
                    {'name': 'Pharmaceutical Technology', 'abbreviation': 'PHT'},
                ],
            },
            {
                'name': 'School of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGT'},
                    {'name': 'Animal Health and Production', 'abbreviation': 'AHP'},
                    {'name': 'Fisheries and Aquaculture', 'abbreviation': 'FIS'},
                    {'name': 'Forestry Technology', 'abbreviation': 'FRT'},
                    {'name': 'Horticultural Technology', 'abbreviation': 'HRT'},
                ],
            },
            {
                'name': 'School of Communication and Information Technology',
                'abbreviation': 'CIT',
                'departments': [
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Library Information Science', 'abbreviation': 'LIS'},
                ],
            },
        ],
    },
    
    # FEDERAL COLLEGE OF AGRICULTURE, AKURE
    {
        'name': 'Federal College of Agriculture, Akure',
        'abbreviation': 'FCAAKURE',
        'state': 'ONDO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Agricultural Technology',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Production', 'abbreviation': 'ANP'},
                    {'name': 'Crop Production', 'abbreviation': 'CRP'},
                    {'name': 'Soil Science', 'abbreviation': 'SLS'},
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                ],
            },
            {
                'name': 'School of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                ],
            },
        ],
    },
    
    # ONDO STATE COLLEGE OF EDUCATION, ILAJE
    {
        'name': 'Ondo State College of Education, Ilaje',
        'abbreviation': 'OSCEI',
        'state': 'ONDO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'Yoruba Education', 'abbreviation': 'YOR'},
                    {'name': 'History Education', 'abbreviation': 'HIS'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SST'},
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
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                ],
            },
        ],
    },
]