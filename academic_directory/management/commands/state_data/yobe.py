# academic_directory/management/commands/state_data/yobe.py
"""Universities and Polytechnics in Yobe State."""

UNIVERSITIES = [
    # FEDERAL UNIVERSITY, GASHUA
    {
        'name': 'Federal University, Gashua',
        'abbreviation': 'FUGASHUA',
        'state': 'YOBE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Environmental Science', 'abbreviation': 'ENV'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
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
                    {'name': 'Business Administration', 'abbreviation': 'BUS'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                ],
            },
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEE'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Crop Science', 'abbreviation': 'CPS'},
                    {'name': 'Soil Science', 'abbreviation': 'SLS'},
                ],
            },
        ],
    },
    
    # YOBE STATE UNIVERSITY, DAMATURU
    {
        'name': 'Yobe State University',
        'abbreviation': 'YSU',
        'state': 'YOBE',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Arts, Social and Management Sciences',
                'abbreviation': 'ASMS',
                'departments': [
                    {'name': 'Arabic Studies', 'abbreviation': 'ARB'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                    {'name': 'Hausa', 'abbreviation': 'HAS'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BUS'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTS'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Sharia Law', 'abbreviation': 'SHL'},
                    {'name': 'Civil Law', 'abbreviation': 'CIL'},
                ],
            },
            {
                'name': 'College of Medical Sciences',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MED'},
                ],
            },
        ],
    },
    
    # FEDERAL POLYTECHNIC, DAMATURU
    {
        'name': 'Federal Polytechnic, Damaturu',
        'abbreviation': 'FEDPODAM',
        'state': 'YOBE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Electrical/Electronics Engineering Technology', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering Technology', 'abbreviation': 'MEC'},
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
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
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
                'name': 'School of General Studies',
                'abbreviation': 'GST',
                'departments': [
                    {'name': 'Languages', 'abbreviation': 'LAN'},
                    {'name': 'Social Sciences', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
    
    # FEDERAL COLLEGE OF EDUCATION (TECHNICAL), POTISKUM
    {
        'name': 'Federal College of Education (Technical), Potiskum',
        'abbreviation': 'FCET POTISKUM',
        'state': 'YOBE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Technical Education',
                'abbreviation': 'TED',
                'departments': [
                    {'name': 'Electrical/Electronic Technology Education', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Technology Education', 'abbreviation': 'MEC'},
                    {'name': 'Building Technology Education', 'abbreviation': 'BLD'},
                    {'name': 'Woodwork Technology Education', 'abbreviation': 'WOD'},
                ],
            },
            {
                'name': 'School of Science Education',
                'abbreviation': 'SED',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Computer Science Education', 'abbreviation': 'CSC'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                ],
            },
            {
                'name': 'School of Vocational Education',
                'abbreviation': 'VED',
                'departments': [
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                ],
            },
            {
                'name': 'School of Arts and Social Sciences Education',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'Hausa Education', 'abbreviation': 'HAS'},
                    {'name': 'Islamic Studies Education', 'abbreviation': 'ISL'},
                    {'name': 'History Education', 'abbreviation': 'HIS'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SST'},
                ],
            },
        ],
    },
    
    # UMAR SULEIMAN COLLEGE OF EDUCATION, GASHUA (treated as university per your instruction)
    {
        'name': 'Umar Suleiman College of Education, Gashua',
        'abbreviation': 'USCOEGA',
        'state': 'YOBE',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'Hausa Education', 'abbreviation': 'HAS'},
                    {'name': 'Arabic Education', 'abbreviation': 'ARB'},
                    {'name': 'Islamic Studies Education', 'abbreviation': 'ISL'},
                    {'name': 'History Education', 'abbreviation': 'HIS'},
                    {'name': 'Geography Education', 'abbreviation': 'GEO'},
                    {'name': 'Economics Education', 'abbreviation': 'ECO'},
                    {'name': 'Political Science Education', 'abbreviation': 'POL'},
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
                    {'name': 'Computer Science Education', 'abbreviation': 'CSC'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                ],
            },
            {
                'name': 'School of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Early Childhood Care Education', 'abbreviation': 'ECE'},
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                ],
            },
        ],
    },
]