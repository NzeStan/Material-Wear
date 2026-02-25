# academic_directory/management/commands/state_data/oyo.py
"""Universities and Polytechnics in Oyo State."""

UNIVERSITIES = [
    # UNIVERSITY OF IBADAN
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
                    {'name': 'Archaeology and Anthropology', 'abbreviation': 'ARA'},
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
                    {'name': 'Geography', 'abbreviation': 'GEO'},
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
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'Classics', 'abbreviation': 'CLA'},
                    {'name': 'French', 'abbreviation': 'FRN'},
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
                'name': 'Faculty of Veterinary Medicine',
                'abbreviation': 'VET',
                'departments': [
                    {'name': 'Veterinary Anatomy', 'abbreviation': 'VAN'},
                    {'name': 'Veterinary Physiology', 'abbreviation': 'VPH'},
                    {'name': 'Veterinary Pathology', 'abbreviation': 'VPT'},
                    {'name': 'Veterinary Microbiology', 'abbreviation': 'VMB'},
                    {'name': 'Veterinary Pharmacology', 'abbreviation': 'VPM'},
                    {'name': 'Veterinary Medicine', 'abbreviation': 'VMD'},
                    {'name': 'Veterinary Surgery', 'abbreviation': 'VSU'},
                    {'name': 'Veterinary Public Health', 'abbreviation': 'VPH'},
                ],
            },
            {
                'name': 'Faculty of Pharmacy',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmaceutics', 'abbreviation': 'PHA'},
                    {'name': 'Pharmaceutical Chemistry', 'abbreviation': 'PCH'},
                    {'name': 'Pharmacology', 'abbreviation': 'PHM'},
                    {'name': 'Pharmacognosy', 'abbreviation': 'PHG'},
                    {'name': 'Clinical Pharmacy', 'abbreviation': 'CPH'},
                ],
            },
            {
                'name': 'College of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                    {'name': 'Dentistry', 'abbreviation': 'DEN'},
                    {'name': 'Physiotherapy', 'abbreviation': 'PHT'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Radiography', 'abbreviation': 'RAD'},
                    {'name': 'Human Nutrition and Dietetics', 'abbreviation': 'HND'},
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
                    {'name': 'Adult Education', 'abbreviation': 'ADE'},
                    {'name': 'Human Kinetics and Health Education', 'abbreviation': 'HKE'},
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
            {
                'name': 'Faculty of Public Health',
                'abbreviation': 'PUB',
                'departments': [
                    {'name': 'Epidemiology', 'abbreviation': 'EPI'},
                    {'name': 'Health Promotion', 'abbreviation': 'HPR'},
                    {'name': 'Health Policy', 'abbreviation': 'HPO'},
                    {'name': 'Environmental Health', 'abbreviation': 'ENH'},
                ],
            },
            {
                'name': 'Faculty of Renewable Natural Resources',
                'abbreviation': 'RNR',
                'departments': [
                    {'name': 'Wildlife Management', 'abbreviation': 'WLM'},
                    {'name': 'Fisheries', 'abbreviation': 'FIS'},
                    {'name': 'Forest Resources Management', 'abbreviation': 'FRM'},
                ],
            },
        ],
    },
    
    # UNIVERSITY OF IBADAN (Distance Learning Centre)
    # Note: This is part of UI but listed separately for completeness
    {
        'name': 'University of Ibadan Distance Learning Centre',
        'abbreviation': 'UIDLC',
        'state': 'OYO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                ],
            },
        ],
    },
    
    # LADOKE AKINTOLA UNIVERSITY OF TECHNOLOGY
    {
        'name': 'Ladoke Akintola University of Technology',
        'abbreviation': 'LAUTECH',
        'state': 'OYO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Food Engineering', 'abbreviation': 'FEN'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'Faculty of Computing and Informatics',
                'abbreviation': 'COM',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Information Systems', 'abbreviation': 'INS'},
                ],
            },
            {
                'name': 'Faculty of Pure and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'Faculty of Agricultural Sciences',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Production', 'abbreviation': 'APR'},
                    {'name': 'Crop Production', 'abbreviation': 'CPR'},
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
                'name': 'Faculty of Food and Consumer Sciences',
                'abbreviation': 'FCS',
                'departments': [
                    {'name': 'Food Science', 'abbreviation': 'FSC'},
                    {'name': 'Nutrition and Dietetics', 'abbreviation': 'NDT'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Management', 'abbreviation': 'BMT'},
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
            {
                'name': 'Faculty of Clinical Sciences',
                'abbreviation': 'CLS',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                ],
            },
            {
                'name': 'Faculty of Pharmacy',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmacy', 'abbreviation': 'PHA'},
                ],
            },
            {
                'name': 'Faculty of Nursing',
                'abbreviation': 'NUR',
                'departments': [
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                ],
            },
        ],
    },
    
    # AJAYI CROWTHER UNIVERSITY
    {
        'name': 'Ajayi Crowther University',
        'abbreviation': 'ACU',
        'state': 'OYO',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                ],
            },
            {
                'name': 'Faculty of Natural Sciences',
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
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
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
    
    # BOWEN UNIVERSITY
    {
        'name': 'Bowen University',
        'abbreviation': 'BU',
        'state': 'OYO',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                ],
            },
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Crop Science', 'abbreviation': 'CPS'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
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
                ],
            },
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
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
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Clinical Sciences',
                'abbreviation': 'CLS',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                ],
            },
        ],
    },
    
    # DOMINICAN UNIVERSITY
    {
        'name': 'Dominican University',
        'abbreviation': 'DU',
        'state': 'OYO',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                ],
            },
        ],
    },
    
    # POLYTECHNIC IBADAN
    {
        'name': 'Polytechnic Ibadan',
        'abbreviation': 'POLYIBADAN',
        'state': 'OYO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
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
                'name': 'School of Business and Management Studies',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                ],
            },
            {
                'name': 'School of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'School of Art, Design and Printing',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Fine Art', 'abbreviation': 'FNA'},
                    {'name': 'Graphic Design', 'abbreviation': 'GRD'},
                    {'name': 'Printing Technology', 'abbreviation': 'PRT'},
                ],
            },
        ],
    },
    
    # THE FEDERER POLYTECHNIC
    {
        'name': 'The Federal Polytechnic',
        'abbreviation': 'FEDPOLY',
        'state': 'OYO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'School of Environmental Studies',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                ],
            },
            {
                'name': 'School of Business Studies',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                ],
            },
        ],
    },
    
    # FEDERAL COLLEGE OF ANIMAL HEALTH AND PRODUCTION TECHNOLOGY, IBADAN
    {
        'name': 'Federal College of Animal Health and Production Technology',
        'abbreviation': 'FCAHPT',
        'state': 'OYO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Animal Health',
                'abbreviation': 'ANH',
                'departments': [
                    {'name': 'Animal Health Technology', 'abbreviation': 'AHT'},
                ],
            },
            {
                'name': 'School of Animal Production',
                'abbreviation': 'ANP',
                'departments': [
                    {'name': 'Animal Production Technology', 'abbreviation': 'APT'},
                ],
            },
        ],
    },
    
    # FEDERAL COLLEGE OF FORESTRY, IBADAN
    {
        'name': 'Federal College of Forestry, Ibadan',
        'abbreviation': 'FCF',
        'state': 'OYO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Forestry',
                'abbreviation': 'FOR',
                'departments': [
                    {'name': 'Forestry Technology', 'abbreviation': 'FRT'},
                    {'name': 'Wildlife Management', 'abbreviation': 'WLM'},
                ],
            },
            {
                'name': 'School of Horticulture',
                'abbreviation': 'HOR',
                'departments': [
                    {'name': 'Horticultural Technology', 'abbreviation': 'HRT'},
                ],
            },
        ],
    },
]