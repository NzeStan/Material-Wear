# academic_directory/management/commands/state_data/borno.py
"""Universities in Borno State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'University of Maiduguri',
        'abbreviation': 'UNIMAID',
        'state': 'BORNO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEC'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Crop Science', 'abbreviation': 'CRP'},
                    {'name': 'Fisheries', 'abbreviation': 'FIS'},
                    {'name': 'Forestry and Wildlife', 'abbreviation': 'FWL'},
                    {'name': 'Soil Science', 'abbreviation': 'SSL'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arabic and Islamic Studies', 'abbreviation': 'AIS'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Fine Arts', 'abbreviation': 'FIA'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Kanuri', 'abbreviation': 'KAN'},
                    {'name': 'Linguistics', 'abbreviation': 'LIN'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                ],
            },
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Physiology', 'abbreviation': 'PHL'},
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
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGE'},
                    {'name': 'Business Education', 'abbreviation': 'BUE'},
                    {'name': 'Education and Biology', 'abbreviation': 'EDB'},
                    {'name': 'Education and Chemistry', 'abbreviation': 'EDC'},
                    {'name': 'Education and Computer Science', 'abbreviation': 'EDCS'},
                    {'name': 'Education and Economics', 'abbreviation': 'EDE'},
                    {'name': 'Education and English Language', 'abbreviation': 'EDEL'},
                    {'name': 'Education and Geography', 'abbreviation': 'EDG'},
                    {'name': 'Education and Integrated Science', 'abbreviation': 'EDIS'},
                    {'name': 'Education and Mathematics', 'abbreviation': 'EDM'},
                    {'name': 'Education and Physics', 'abbreviation': 'EDP'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Physical and Health Education', 'abbreviation': 'PHE'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SSE'},
                    {'name': 'Technical Education', 'abbreviation': 'TED'},
                    {'name': 'Vocational Education', 'abbreviation': 'VCE'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PET'},
                ],
            },
            {
                'name': 'Faculty of Environmental Science',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building', 'abbreviation': 'BLD'},
                    {'name': 'Environmental Management', 'abbreviation': 'ENM'},
                    {'name': 'Estate Management', 'abbreviation': 'ESM'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
                    {'name': 'Surveying and Geoinformatics', 'abbreviation': 'SGI'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
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
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUA'},
                    {'name': 'Business Management', 'abbreviation': 'BUM'},
                    {'name': 'Entrepreneurship', 'abbreviation': 'ENT'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PUA'},
                ],
            },
            {
                'name': 'Faculty of Pharmacy',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmacy', 'abbreviation': 'PHM'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology', 'abbreviation': 'GLY'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology and Anthropology', 'abbreviation': 'SOA'},
                ],
            },
            {
                'name': 'Faculty of Veterinary Medicine',
                'abbreviation': 'VET',
                'departments': [
                    {'name': 'Veterinary Medicine', 'abbreviation': 'VME'},
                ],
            },
            {
                'name': 'College of Medical Sciences',
                'abbreviation': 'CMS',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NSG'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Radiography', 'abbreviation': 'RAD'},
                    {'name': 'Physiotherapy', 'abbreviation': 'PTP'},
                    {'name': 'Medical Rehabilitation', 'abbreviation': 'MRE'},
                ],
            },
            {
                'name': 'Faculty of Allied Medical Sciences',
                'abbreviation': 'AMS',
                'departments': [
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NSG'},
                    {'name': 'Radiography', 'abbreviation': 'RAD'},
                    {'name': 'Physiotherapy', 'abbreviation': 'PTP'},
                    {'name': 'Medical Rehabilitation', 'abbreviation': 'MRE'},
                ],
            },
        ],
    },
    {
        'name': 'Borno State University, Maiduguri',
        'abbreviation': 'BOSU',
        'state': 'BORNO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agriculture', 'abbreviation': 'AGR'},
                ],
            },
            {
                'name': 'Faculty of Arts and Education',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arts and Social Science Education', 'abbreviation': 'ASE'},
                    {'name': 'Education and Biology', 'abbreviation': 'EDB'},
                    {'name': 'Education and Chemistry', 'abbreviation': 'EDC'},
                    {'name': 'Education and Computer Science', 'abbreviation': 'EDCS'},
                    {'name': 'Education and Economics', 'abbreviation': 'EDE'},
                    {'name': 'Education and English Language', 'abbreviation': 'EDEL'},
                    {'name': 'Education and Islamic Studies', 'abbreviation': 'EDIS'},
                    {'name': 'Education and Mathematics', 'abbreviation': 'EDM'},
                    {'name': 'Education and Physics', 'abbreviation': 'EDP'},
                    {'name': 'English Language', 'abbreviation': 'ENG'},
                    {'name': 'English and Literary Studies', 'abbreviation': 'ELS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISC'},
                    {'name': 'Literature in English', 'abbreviation': 'LIE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Animal and Environmental Biology', 'abbreviation': 'AEB'},
                    {'name': 'Biotechnology', 'abbreviation': 'BTC'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Plant Science and Biotechnology', 'abbreviation': 'PSB'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUA'},
                    {'name': 'Criminology and Security Studies', 'abbreviation': 'CSS'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Peace Studies and Conflict Resolution', 'abbreviation': 'PCR'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Public Administration', 'abbreviation': 'PUA'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
            {
                'name': 'College of Medical and Health Sciences',
                'abbreviation': 'CMHS',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NSG'},
                    {'name': 'Physiotherapy', 'abbreviation': 'PTP'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                ],
            },
        ],
    },
    {
        'name': 'Federal Polytechnic, Monguno',
        'abbreviation': 'FEDPOLYMONGUNO',
        'state': 'BORNO',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Business and Management',
                'abbreviation': 'SBM',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                ],
            },
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'SET',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronic Engineering', 'abbreviation': 'EEE'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SST',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
        ],
    },
    {
        'name': 'Ramat Polytechnic, Maiduguri',
        'abbreviation': 'RAMATPOLY',
        'state': 'BORNO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Business and Management',
                'abbreviation': 'SBM',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PUA'},
                ],
            },
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'SET',
                'departments': [
                    {'name': 'Agricultural Engineering Technology', 'abbreviation': 'AET'},
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CET'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronic Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering Technology', 'abbreviation': 'MET'},
                ],
            },
            {
                'name': 'School of Environmental Design',
                'abbreviation': 'SED',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management and Valuation', 'abbreviation': 'ESM'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
                    {'name': 'Surveying and Geo-Informatics', 'abbreviation': 'SGI'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SST',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Food Technology', 'abbreviation': 'FST'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
        ],
    },
    {
        'name': 'Mohamet Lawan College of Agriculture, Maiduguri',
        'abbreviation': 'MOLCA',
        'state': 'BORNO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Agricultural Technology',
                'abbreviation': 'SAT',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGR'},
                    {'name': 'Animal Health and Production Technology', 'abbreviation': 'AHP'},
                ],
            },
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'SET',
                'departments': [
                    {'name': 'Agricultural and Bio-Environmental Engineering Technology', 'abbreviation': 'ABE'},
                ],
            },
            {
                'name': 'School of Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SST',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
        ],
    },
    {
        'name': 'College of Education, Waka-Biu',
        'abbreviation': 'COEWAKA',
        'state': 'BORNO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARA'},
                    {'name': 'English Language', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISC'},
                    {'name': 'Social Studies', 'abbreviation': 'SST'},
                ],
            },
            {
                'name': 'School of Education',
                'abbreviation': 'SED',
                'departments': [
                    {'name': 'Early Childhood Education', 'abbreviation': 'ECC'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                ],
            },
            {
                'name': 'School of Science and Vocational Education',
                'abbreviation': 'SSVE',
                'departments': [
                    {'name': 'Agricultural Science Education', 'abbreviation': 'ASE'},
                    {'name': 'Biology Education', 'abbreviation': 'BIE'},
                    {'name': 'Business Education', 'abbreviation': 'BUE'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHE'},
                    {'name': 'Computer Education', 'abbreviation': 'CSE'},
                    {'name': 'Home Economics', 'abbreviation': 'HEC'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISE'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTE'},
                    {'name': 'Physical and Health Education', 'abbreviation': 'PHE'},
                    {'name': 'Physics Education', 'abbreviation': 'PYE'},
                ],
            },
        ],
    },
    {
        'name': 'College of Business and Management Studies, Konduga',
        'abbreviation': 'CBMSKONDUGA',
        'state': 'BORNO',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Business and Management',
                'abbreviation': 'SBM',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PUA'},
                ],
            },
        ],
    },
]