# academic_directory/management/commands/state_data/kogi.py
"""Universities and Polytechnics in Kogi State."""

UNIVERSITIES = [
    # FEDERAL UNIVERSITY, LOKOJA
    {
        'name': 'Federal University, Lokoja',
        'abbreviation': 'FULOKOJA',
        'state': 'KOGI',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Archaeology and Museum Studies', 'abbreviation': 'ARC'},
                    {'name': 'English and Literary Studies', 'abbreviation': 'ENG'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics', 'abbreviation': 'LIN'},
                    {'name': 'Performing Arts', 'abbreviation': 'PFA'},
                    {'name': 'Philosophy and Religious Studies', 'abbreviation': 'PRS'},
                    {'name': 'Music', 'abbreviation': 'MUS'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Biotechnology', 'abbreviation': 'BTC'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Plant Science', 'abbreviation': 'PLS'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts and Social Science Education', 'abbreviation': 'ASE'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                ],
            },
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical/Electronics Engineering', 'abbreviation': 'ELE'},
                ],
            },
            {
                'name': 'College of Health Sciences',
                'abbreviation': 'CHS',
                'departments': [
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                ],
            },
        ],
    },
    
    # PRINCE ABUBAKAR AUDU UNIVERSITY (formerly Kogi State University), ANYIGBA
    {
        'name': 'Prince Abubakar Audu University',
        'abbreviation': 'PAAU',
        'state': 'KOGI',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEE'},
                    {'name': 'Crop Production', 'abbreviation': 'CRP'},
                    {'name': 'Animal Production', 'abbreviation': 'ANP'},
                    {'name': 'Fisheries and Aquaculture', 'abbreviation': 'FIS'},
                    {'name': 'Soil and Environmental Management', 'abbreviation': 'SEM'},
                    {'name': 'Food Science and Technology', 'abbreviation': 'FST'},
                    {'name': 'Home Science', 'abbreviation': 'HSC'},
                ],
            },
            {
                'name': 'Faculty of Arts and Humanities',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'English and Literary Studies', 'abbreviation': 'ENG'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Common Law', 'abbreviation': 'CML'},
                    {'name': 'Islamic Law', 'abbreviation': 'ISL'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Geography and Planning', 'abbreviation': 'GEP'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Christian Religious Studies Education', 'abbreviation': 'CRS'},
                    {'name': 'Islamic Education', 'abbreviation': 'ISL'},
                    {'name': 'Library and Information Sciences', 'abbreviation': 'LIS'},
                    {'name': 'Human Kinetics and Health Education', 'abbreviation': 'HKH'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SST'},
                    {'name': 'Economics Education', 'abbreviation': 'ECO'},
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'Geography Education', 'abbreviation': 'GEO'},
                ],
            },
        ],
    },
    
    # FEDERAL POLYTECHNIC, IDAH
    {
        'name': 'Federal Polytechnic, Idah',
        'abbreviation': 'FEDPOLYIDAH',
        'state': 'KOGI',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Business Studies',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CVE'},
                    {'name': 'Electrical/Electronics Engineering Technology', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering Technology', 'abbreviation': 'MEE'},
                    {'name': 'Foundry Engineering Technology', 'abbreviation': 'FEN'},
                    {'name': 'Metallurgical Engineering Technology', 'abbreviation': 'MTL'},
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
                    {'name': 'Surveying and Geo-Informatics', 'abbreviation': 'SGV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Technology',
                'abbreviation': 'TEC',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Hospitality Management', 'abbreviation': 'HSM'},
                    {'name': 'Leisure and Tourism Management', 'abbreviation': 'LTM'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
        ],
    },
    
    # KOGI STATE POLYTECHNIC, LOKOJA
    {
        'name': 'Kogi State Polytechnic',
        'abbreviation': 'KOGIPOLY',
        'state': 'KOGI',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Agricultural Technology',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGT'},
                ],
            },
            {
                'name': 'School of Management Studies',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                ],
            },
            {
                'name': 'School of Art and Industrial Design',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Art and Design', 'abbreviation': 'ARD'},
                ],
            },
            {
                'name': 'School of Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                ],
            },
            {
                'name': 'School of Environmental Technology',
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
                'name': 'School of Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'School of General Studies',
                'abbreviation': 'GST',
                'departments': [
                    {'name': 'General Studies', 'abbreviation': 'GNS'},
                ],
            },
        ],
    },
    
    # KOGI STATE COLLEGE OF EDUCATION, ANKPA
    {
        'name': 'Kogi State College of Education, Ankpa',
        'abbreviation': 'COEANKPA',
        'state': 'KOGI',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Christian Religious Studies/History', 'abbreviation': 'CRH'},
                    {'name': 'Arabic/Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'English/Social Studies', 'abbreviation': 'ESS'},
                ],
            },
            {
                'name': 'School of Languages',
                'abbreviation': 'LAN',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'Hausa', 'abbreviation': 'HAU'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Chemistry/Physics', 'abbreviation': 'CHP'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Computer Education/Physics', 'abbreviation': 'CEP'},
                ],
            },
            {
                'name': 'School of Early Childhood Care and Primary Education',
                'abbreviation': 'ECPE',
                'departments': [
                    {'name': 'Early Childhood Care Education', 'abbreviation': 'ECE'},
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                ],
            },
            {
                'name': 'School of General Education',
                'abbreviation': 'GEN',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                ],
            },
        ],
    },
]