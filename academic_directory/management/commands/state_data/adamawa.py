# academic_directory/management/commands/state_data/adamawa.py
"""Universities in Adamawa State. Add more universities to this list as needed."""

UNIVERSITIES = [
    {
        'name': 'Modibbo Adama University of Technology, Yola',
        'abbreviation': 'MAUTECH',
        'state': 'ADAMAWA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'College of Medical Sciences',
                'abbreviation': 'CMS',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MED'},
                ],
            },
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEC'},
                    {'name': 'Animal Science and Range Management', 'abbreviation': 'ASR'},
                    {'name': 'Crop Production and Horticulture', 'abbreviation': 'CPH'},
                    {'name': 'Crop Protection', 'abbreviation': 'CRP'},
                    {'name': 'Fisheries', 'abbreviation': 'FIS'},
                    {'name': 'Food Science and Technology', 'abbreviation': 'FST'},
                    {'name': 'Forestry and Wildlife Management', 'abbreviation': 'FWM'},
                    {'name': 'Soil Science', 'abbreviation': 'SSL'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural and Environmental Engineering', 'abbreviation': 'AEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building', 'abbreviation': 'BLD'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Industrial Design', 'abbreviation': 'IND'},
                    {'name': 'Survey and Geo-informatics', 'abbreviation': 'SGI'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Faculty of Life Sciences',
                'abbreviation': 'LSC',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Biotechnology', 'abbreviation': 'BTC'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Plant Science', 'abbreviation': 'PLS'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Physical Sciences',
                'abbreviation': 'PSC',
                'departments': [
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology', 'abbreviation': 'GLY'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics and Operational Research', 'abbreviation': 'SOR'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration', 'abbreviation': 'BUA'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Information Management Technology', 'abbreviation': 'IMT'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                ],
            },
            {
                'name': 'Faculty of Technology and Science Education',
                'abbreviation': 'TSE',
                'departments': [
                    {'name': 'Electrical Technology Education', 'abbreviation': 'ETE'},
                    {'name': 'Environmental and Life Science Education', 'abbreviation': 'ELE'},
                    {'name': 'Physical Science Education', 'abbreviation': 'PSE'},
                    {'name': 'Technical Education', 'abbreviation': 'TED'},
                    {'name': 'Technology Education', 'abbreviation': 'TED'},
                    {'name': 'Vocational Education', 'abbreviation': 'VCE'},
                ],
            },
        ],
    },
    {
        'name': 'American University of Nigeria, Yola',
        'abbreviation': 'AUN',
        'state': 'ADAMAWA',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Arts and Sciences',
                'abbreviation': 'SAS',
                'departments': [
                    {'name': 'Communications and Multimedia Design', 'abbreviation': 'CMD'},
                    {'name': 'Natural and Environmental Sciences', 'abbreviation': 'NES'},
                    {'name': 'Petroleum Chemistry', 'abbreviation': 'PCH'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Politics and International Studies', 'abbreviation': 'PIS'},
                    {'name': 'English Language and Literature', 'abbreviation': 'ELL'},
                ],
            },
            {
                'name': 'School of Business and Entrepreneurship',
                'abbreviation': 'SBE',
                'departments': [
                    {'name': 'Business Administration', 'abbreviation': 'BUA'},
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Entrepreneurship Management', 'abbreviation': 'ENT'},
                ],
            },
            {
                'name': 'School of Engineering',
                'abbreviation': 'SOE',
                'departments': [
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Telecommunication Engineering', 'abbreviation': 'TCE'},
                ],
            },
            {
                'name': 'School of Information Technology and Computing',
                'abbreviation': 'SITC',
                'departments': [
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Data Science and Analytics', 'abbreviation': 'DSA'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Information Systems', 'abbreviation': 'IFS'},
                    {'name': 'Telecommunications and Wireless Technologies', 'abbreviation': 'TWT'},
                ],
            },
            {
                'name': 'School of Law',
                'abbreviation': 'SOL',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'School of Basic Medical and Allied Health Sciences',
                'abbreviation': 'SBMAHS',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NSG'},
                    {'name': 'Public Health', 'abbreviation': 'PUH'},
                ],
            },
        ],
    },
    {
        'name': 'Adamawa State University, Mubi',
        'abbreviation': 'ADSU',
        'state': 'ADAMAWA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEC'},
                    {'name': 'Animal Production', 'abbreviation': 'ANP'},
                    {'name': 'Crop Science', 'abbreviation': 'CRS'},
                    {'name': 'Fisheries and Aquaculture', 'abbreviation': 'FIS'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Languages', 'abbreviation': 'LAN'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Humanities and Social Science Education', 'abbreviation': 'HSE'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Geology', 'abbreviation': 'GLY'},
                    {'name': 'Mathematical Sciences', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUA'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Public Administration', 'abbreviation': 'PUA'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
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
    {
        'name': 'Federal Polytechnic, Mubi',
        'abbreviation': 'FPM',
        'state': 'ADAMAWA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Agricultural Technology',
                'abbreviation': 'SAT',
                'departments': [
                    {'name': 'Agricultural and Bio-Environmental Engineering Technology', 'abbreviation': 'ABE'},
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGR'},
                    {'name': 'Animal Health and Production Technology', 'abbreviation': 'AHP'},
                ],
            },
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'SET',
                'departments': [
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CET'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'School of Environmental Design',
                'abbreviation': 'SED',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'ESM'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
                    {'name': 'Surveying and Geoinformatics', 'abbreviation': 'SGI'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Business and Management',
                'abbreviation': 'SBM',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Cooperative Economics and Management', 'abbreviation': 'CEM'},
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
        'name': 'Adamawa State Polytechnic, Yola',
        'abbreviation': 'ADSPOLY',
        'state': 'ADAMAWA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Agricultural Technology',
                'abbreviation': 'SAT',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGR'},
                    {'name': 'Animal Health and Production Technology', 'abbreviation': 'AHP'},
                    {'name': 'Fisheries', 'abbreviation': 'FIS'},
                    {'name': 'Forestry', 'abbreviation': 'FOR'},
                ],
            },
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'SET',
                'departments': [
                    {'name': 'Agricultural and Bio-Environmental Engineering Technology', 'abbreviation': 'ABE'},
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CET'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Mechatronics Engineering', 'abbreviation': 'MCE'},
                ],
            },
            {
                'name': 'School of Environmental Sciences',
                'abbreviation': 'SES',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Disaster Management', 'abbreviation': 'DSM'},
                    {'name': 'Surveying and Geoinformatics', 'abbreviation': 'SGI'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Social and Management Sciences',
                'abbreviation': 'SSMS',
                'departments': [
                    {'name': 'Cooperative Economics and Management', 'abbreviation': 'CEM'},
                    {'name': 'Crime Prevention, Management and Control', 'abbreviation': 'CPC'},
                    {'name': 'International Relations and Strategic Studies', 'abbreviation': 'IRS'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Public Administration', 'abbreviation': 'PUA'},
                    {'name': 'Social Development', 'abbreviation': 'SOD'},
                    {'name': 'Tourism and Leisure Management', 'abbreviation': 'TLM'},
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
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
]