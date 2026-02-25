# academic_directory/management/commands/state_data/rivers.py
"""Universities and Polytechnics in Rivers State."""

UNIVERSITIES = [
    # UNIVERSITY OF PORT HARCOURT
    {
        'name': 'University of Port Harcourt',
        'abbreviation': 'UNIPORT',
        'state': 'RIVERS',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical and Petroleum Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'COE'},
                    {'name': 'Marine Engineering', 'abbreviation': 'MRE'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PEE'},
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
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Marine Biology', 'abbreviation': 'MBL'},
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
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Geography and Environmental Management', 'abbreviation': 'GEM'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics and Nigerian Languages', 'abbreviation': 'LNL'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'Performing Arts', 'abbreviation': 'PEA'},
                    {'name': 'Fine Arts', 'abbreviation': 'FAA'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                ],
            },
            {
                'name': 'Faculty of Business and Social Sciences',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Management', 'abbreviation': 'MGT'},
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
                'name': 'Faculty of Pharmaceutical Sciences',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmacy', 'abbreviation': 'PHA'},
                ],
            },
            {
                'name': 'Faculty of Dentistry',
                'abbreviation': 'DEN',
                'departments': [
                    {'name': 'Dentistry', 'abbreviation': 'DEN'},
                ],
            },
            {
                'name': 'College of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Pharmacology', 'abbreviation': 'PHT'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Psychology and Curriculum Studies', 'abbreviation': 'EPC'},
                    {'name': 'Adult and Non-Formal Education', 'abbreviation': 'ANF'},
                    {'name': 'Vocational and Technical Education', 'abbreviation': 'VTE'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GCS'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Human Kinetics and Health Education', 'abbreviation': 'HKE'},
                ],
            },
        ],
    },
    
    # RIVERS STATE UNIVERSITY
    {
        'name': 'Rivers State University',
        'abbreviation': 'RSU',
        'state': 'RIVERS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Crop Science', 'abbreviation': 'CPS'},
                    {'name': 'Fisheries', 'abbreviation': 'FIS'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Marine Engineering', 'abbreviation': 'MRE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PEE'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts Education', 'abbreviation': 'AED'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Technical Education', 'abbreviation': 'TED'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Human Kinetics and Health Education', 'abbreviation': 'HKE'},
                ],
            },
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                    {'name': 'Linguistics', 'abbreviation': 'LIN'},
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
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
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
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
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
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                ],
            },
            {
                'name': 'Faculty of Technical and Science Education',
                'abbreviation': 'TSE',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AED'},
                    {'name': 'Health Education', 'abbreviation': 'HED'},
                    {'name': 'Home Economics', 'abbreviation': 'HEC'},
                    {'name': 'Industrial Technology Education', 'abbreviation': 'ITE'},
                ],
            },
        ],
    },
    
    # IGNATIUS AJURU UNIVERSITY OF EDUCATION
    {
        'name': 'Ignatius Ajuru University of Education',
        'abbreviation': 'IAUE',
        'state': 'RIVERS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English Studies', 'abbreviation': 'ENG'},
                    {'name': 'Foreign Languages', 'abbreviation': 'FOL'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Religious and Cultural Studies', 'abbreviation': 'RCS'},
                    {'name': 'Music', 'abbreviation': 'MUS'},
                    {'name': 'Fine and Applied Arts', 'abbreviation': 'FAA'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Adult Education', 'abbreviation': 'ADE'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Early Childhood Education', 'abbreviation': 'ECE'},
                    {'name': 'Primary Education', 'abbreviation': 'PED'},
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
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Integrated Science', 'abbreviation': 'ISC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Home Economics', 'abbreviation': 'HEC'},
                    {'name': 'Technology Education', 'abbreviation': 'TED'},
                ],
            },
        ],
    },
    
    # PAMO UNIVERSITY OF MEDICAL SCIENCES
    {
        'name': 'Pamo University of Medical Sciences',
        'abbreviation': 'PUMS',
        'state': 'RIVERS',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Medicine',
                'abbreviation': 'MED',
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
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                ],
            },
            {
                'name': 'Faculty of Nursing',
                'abbreviation': 'NUR',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                ],
            },
        ],
    },
    
    # CAPTAIN ELECHI AMADI POLYTECHNIC
    {
        'name': 'Captain Elechi Amadi Polytechnic',
        'abbreviation': 'CEAP',
        'state': 'RIVERS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
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
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Office Technology Management', 'abbreviation': 'OTM'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
        ],
    },
    
    # PORT HARCOURT POLYTECHNIC
    {
        'name': 'Port Harcourt Polytechnic',
        'abbreviation': 'PORTPOLY',
        'state': 'RIVERS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGT'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PEE'},
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
                ],
            },
        ],
    },
]