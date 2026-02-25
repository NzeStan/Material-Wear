# academic_directory/management/commands/state_data/fct.py
"""
Universities in Federal Capital Territory (Abuja).
Add more universities to this list as needed.
"""

UNIVERSITIES = [
    {
        'name': 'University of Abuja',
        'abbreviation': 'UNIABUJA',
        'state': 'FCT',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                ],
            },
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
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
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
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts and Social Science Education', 'abbreviation': 'ASE'},
                    {'name': 'Science Education', 'abbreviation': 'SCE'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English and Literary Studies', 'abbreviation': 'ELS'},
                    {'name': 'History and Diplomatic Studies', 'abbreviation': 'HDS'},
                    {'name': 'Linguistics and Nigerian Languages', 'abbreviation': 'LIN'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                    {'name': 'Religious Studies', 'abbreviation': 'REL'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                ],
            },
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEE'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                    {'name': 'Crop Science', 'abbreviation': 'CRP'},
                    {'name': 'Soil Science', 'abbreviation': 'SSL'},
                ],
            },
            {
                'name': 'Faculty of Veterinary Medicine',
                'abbreviation': 'VET',
                'departments': [
                    {'name': 'Veterinary Medicine', 'abbreviation': 'VET'},
                ],
            },
            {
                'name': 'College of Medicine',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                    {'name': 'Medical Biochemistry', 'abbreviation': 'MBC'},
                ],
            },
        ],
    },
    {
        'name': 'National Open University of Nigeria',
        'abbreviation': 'NOUN',
        'state': 'FCT',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Agricultural Sciences',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics and Extension', 'abbreviation': 'AEE'},
                    {'name': 'Animal Science and Fisheries', 'abbreviation': 'ANS'},
                    {'name': 'Crop and Soil Science', 'abbreviation': 'CSS'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Linguistics, Foreign and Nigerian Languages', 'abbreviation': 'LIN'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                    {'name': 'Religious Studies', 'abbreviation': 'REL'},
                ],
            },
            {
                'name': 'Faculty of Computing',
                'abbreviation': 'COM',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Artificial Intelligence', 'abbreviation': 'AI'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts and Social Science Education', 'abbreviation': 'ASE'},
                    {'name': 'Science Education', 'abbreviation': 'SCE'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Human Kinetics and Health Education', 'abbreviation': 'HKE'},
                ],
            },
            {
                'name': 'Faculty of Health Sciences',
                'abbreviation': 'HSC',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
                    {'name': 'Environmental Health Science', 'abbreviation': 'EHS'},
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
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Entrepreneurship', 'abbreviation': 'ENT'},
                    {'name': 'Cooperative and Rural Development', 'abbreviation': 'CRD'},
                ],
            },
            {
                'name': 'Faculty of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Environmental Science and Resource Management', 'abbreviation': 'ESR'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Mathematics and Computer Science', 'abbreviation': 'MCS'},
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SSC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Broadcast Journalism', 'abbreviation': 'BCJ'},
                    {'name': 'Film Production', 'abbreviation': 'FIP'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Tourism Studies', 'abbreviation': 'TOU'},
                    {'name': 'Peace Studies and Conflict Resolution', 'abbreviation': 'PCR'},
                    {'name': 'Criminology and Security Studies', 'abbreviation': 'CSS'},
                    {'name': 'Development Studies', 'abbreviation': 'DST'},
                ],
            },
        ],
    },
    {
        'name': 'Bola Ahmed Tinubu Federal Polytechnic',
        'abbreviation': 'BATPOLY',
        'state': 'FCT',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'SEN',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'School of Environmental Studies',
                'abbreviation': 'SES',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management and Valuation', 'abbreviation': 'EMV'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
                    {'name': 'Surveying and Geo-Informatics', 'abbreviation': 'SGI'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Applied Sciences',
                'abbreviation': 'SAS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Food Technology', 'abbreviation': 'FOT'},
                    {'name': 'Hospitality Management', 'abbreviation': 'HOM'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'School of Business Studies',
                'abbreviation': 'SBS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Information and Communication Technology',
                'abbreviation': 'ICT',
                'departments': [
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                ],
            },
        ],
    },
    {
        'name': 'Federal College of Education, Zuba',
        'abbreviation': 'FCEZUBA',
        'state': 'FCT',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'Hausa', 'abbreviation': 'HAU'},
                    {'name': 'Igbo', 'abbreviation': 'IGB'},
                    {'name': 'Yoruba', 'abbreviation': 'YOR'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Social Studies', 'abbreviation': 'SOS'},
                    {'name': 'Civic Education', 'abbreviation': 'CIV'},
                ],
            },
            {
                'name': 'School of Education',
                'abbreviation': 'SED',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                    {'name': 'Early Childhood Care Education', 'abbreviation': 'ECE'},
                    {'name': 'Special Education', 'abbreviation': 'SPE'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                ],
            },
            {
                'name': 'School of Languages',
                'abbreviation': 'SLG',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'Arabic', 'abbreviation': 'ARA'},
                ],
            },
            {
                'name': 'School of Science',
                'abbreviation': 'SSC',
                'departments': [
                    {'name': 'Agricultural Science', 'abbreviation': 'AGS'},
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Integrated Science', 'abbreviation': 'INT'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Physical and Health Education', 'abbreviation': 'PHE'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'SVT',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGE'},
                    {'name': 'Business Education', 'abbreviation': 'BUE'},
                    {'name': 'Fine and Applied Arts', 'abbreviation': 'FAA'},
                    {'name': 'Home Economics', 'abbreviation': 'HEC'},
                    {'name': 'Industrial Technical Education', 'abbreviation': 'ITE'},
                ],
            },
        ],
    },
    {
        'name': 'FCT College of Education, Zuba',
        'abbreviation': 'FCTCOE',
        'state': 'FCT',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'Hausa', 'abbreviation': 'HAU'},
                    {'name': 'Igbo', 'abbreviation': 'IGB'},
                    {'name': 'Yoruba', 'abbreviation': 'YOR'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Social Studies', 'abbreviation': 'SOS'},
                    {'name': 'Civic Education', 'abbreviation': 'CIV'},
                ],
            },
            {
                'name': 'School of Education',
                'abbreviation': 'SED',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                    {'name': 'Early Childhood Care Education', 'abbreviation': 'ECE'},
                    {'name': 'Special Education', 'abbreviation': 'SPE'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                ],
            },
            {
                'name': 'School of Languages',
                'abbreviation': 'SLG',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'Arabic', 'abbreviation': 'ARA'},
                ],
            },
            {
                'name': 'School of Science',
                'abbreviation': 'SSC',
                'departments': [
                    {'name': 'Agricultural Science', 'abbreviation': 'AGS'},
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Integrated Science', 'abbreviation': 'INT'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Physical and Health Education', 'abbreviation': 'PHE'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'SVT',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGE'},
                    {'name': 'Business Education', 'abbreviation': 'BUE'},
                    {'name': 'Fine and Applied Arts', 'abbreviation': 'FAA'},
                    {'name': 'Home Economics', 'abbreviation': 'HEC'},
                    {'name': 'Industrial Technical Education', 'abbreviation': 'ITE'},
                ],
            },
        ],
    },
    {
        'name': 'African University of Science and Technology',
        'abbreviation': 'AUST',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Science and Science Education',
                'abbreviation': 'SSE',
                'departments': [
                    {'name': 'Pure and Applied Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Theoretical Physics', 'abbreviation': 'PHY'},
                    {'name': 'Materials Science and Engineering', 'abbreviation': 'MSE'},
                    {'name': 'Petroleum Engineering', 'abbreviation': 'PET'},
                ],
            },
            {
                'name': 'Faculty of Computing and Information Technology',
                'abbreviation': 'CIT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Management Information Technology', 'abbreviation': 'MIT'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'Faculty of Administration, Business and Management Sciences',
                'abbreviation': 'ABM',
                'departments': [
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                ],
            },
        ],
    },
    {
        'name': 'Baze University',
        'abbreviation': 'BAZE',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'Faculty of Computing and Applied Sciences',
                'abbreviation': 'CAS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Data Science', 'abbreviation': 'DAS'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Parasitology', 'abbreviation': 'PAR'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'ESM'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
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
                'name': 'Faculty of Management and Social Sciences',
                'abbreviation': 'MSS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'International Relations and Diplomacy', 'abbreviation': 'IRD'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Intelligence and Global Security', 'abbreviation': 'IGS'},
                    {'name': 'Security, Leadership and Society', 'abbreviation': 'SLS'},
                ],
            },
            {
                'name': 'Faculty of Medical and Health Sciences',
                'abbreviation': 'MHS',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Radiography', 'abbreviation': 'RAD'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
                ],
            },
        ],
    },
    {
        'name': 'Bingham University',
        'abbreviation': 'BINGHAM',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'College of Medicine and Allied Health Sciences',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Radiography', 'abbreviation': 'RAD'},
                    {'name': 'Optometry', 'abbreviation': 'OPT'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
                ],
            },
            {
                'name': 'Faculty of Pharmaceutical Sciences',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                ],
            },
            {
                'name': 'Faculty of Administration',
                'abbreviation': 'ADM',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Entrepreneurship', 'abbreviation': 'ENT'},
                    {'name': 'Procurement Management', 'abbreviation': 'PMT'},
                    {'name': 'Supply Chain Management', 'abbreviation': 'SCM'},
                ],
            },
            {
                'name': 'Faculty of Architecture',
                'abbreviation': 'ARC',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Landscape Architecture', 'abbreviation': 'LAR'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English and Literary Studies', 'abbreviation': 'ELS'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                    {'name': 'Religious Studies', 'abbreviation': 'REL'},
                    {'name': 'Theology', 'abbreviation': 'THL'},
                ],
            },
            {
                'name': 'Faculty of Communication and Media Studies',
                'abbreviation': 'CMS',
                'departments': [
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Film and Multimedia Studies', 'abbreviation': 'FMS'},
                    {'name': 'Journalism and Media Studies', 'abbreviation': 'JMS'},
                    {'name': 'Public Relations', 'abbreviation': 'PUR'},
                ],
            },
            {
                'name': 'Faculty of Computing',
                'abbreviation': 'COM',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Data Science', 'abbreviation': 'DAS'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Psychology', 'abbreviation': 'EPY'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Environmental Management', 'abbreviation': 'ENM'},
                    {'name': 'Estate Management', 'abbreviation': 'ESM'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
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
                'name': 'Faculty of Science and Technology',
                'abbreviation': 'SCT',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                    {'name': 'Industrial Mathematics', 'abbreviation': 'IMT'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Industrial Physics', 'abbreviation': 'IPH'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SSC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                ],
            },
        ],
    },
    {
        'name': 'Nile University of Nigeria',
        'abbreviation': 'NILE',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Petroleum and Gas Engineering', 'abbreviation': 'PGE'},
                ],
            },
            {
                'name': 'Faculty of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Political Science and International Relations', 'abbreviation': 'PIR'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Criminology and Security Studies', 'abbreviation': 'CSS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                ],
            },
            {
                'name': 'Faculty of Computing Studies',
                'abbreviation': 'COM',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                ],
            },
            {
                'name': 'Faculty of Health Sciences',
                'abbreviation': 'HSC',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
                    {'name': 'Physiotherapy', 'abbreviation': 'PTP'},
                    {'name': 'Radiography', 'abbreviation': 'RAD'},
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
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Entrepreneurship', 'abbreviation': 'ENT'},
                ],
            },
            {
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'NAS',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                ],
            },
        ],
    },
    {
        'name': 'Veritas University',
        'abbreviation': 'VERITAS',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'College of Medicine and Medical Sciences',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                    {'name': 'Medical Laboratory Sciences', 'abbreviation': 'MLS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                ],
            },
            {
                'name': 'Faculty of Pharmaceutical Sciences',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronic Engineering', 'abbreviation': 'EEE'},
                ],
            },
            {
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'NAS',
                'departments': [
                    {'name': 'Applied Mathematics', 'abbreviation': 'AMT'},
                    {'name': 'Applied Microbiology', 'abbreviation': 'AMC'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                    {'name': 'Physics with Electronics', 'abbreviation': 'PWE'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Entrepreneurial Studies', 'abbreviation': 'ENT'},
                    {'name': 'Marketing and Advertising', 'abbreviation': 'MAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English and Literary Studies', 'abbreviation': 'ELS'},
                    {'name': 'History and International Relations', 'abbreviation': 'HIR'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                    {'name': 'Religious Studies', 'abbreviation': 'REL'},
                    {'name': 'Sacred Philosophy', 'abbreviation': 'SAP'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SSC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Peace and Conflict Studies', 'abbreviation': 'PCS'},
                    {'name': 'Political Science and Diplomacy', 'abbreviation': 'PSD'},
                ],
            },
            {
                'name': 'College of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIE'},
                    {'name': 'Business Education', 'abbreviation': 'BUE'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHE'},
                    {'name': 'Computer Science Education', 'abbreviation': 'CSE'},
                    {'name': 'Economics Education', 'abbreviation': 'ECE'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'English Education', 'abbreviation': 'EDE'},
                    {'name': 'Guidance and Counseling', 'abbreviation': 'GAC'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Physics Education', 'abbreviation': 'PHE'},
                    {'name': 'Religious Education', 'abbreviation': 'REE'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SSE'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                    {'name': 'Public and International Law', 'abbreviation': 'PIL'},
                ],
            },
            {
                'name': 'Ecclesiastical Faculty of Theology',
                'abbreviation': 'THE',
                'departments': [
                    {'name': 'Sacred Theology', 'abbreviation': 'STH'},
                    {'name': 'Theology', 'abbreviation': 'THL'},
                ],
            },
        ],
    },
    {
        'name': 'Philomath University',
        'abbreviation': 'PHILOMATH',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                ],
            },
            {
                'name': 'Faculty of Natural and Environmental Science',
                'abbreviation': 'NES',
                'departments': [
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Environmental Science', 'abbreviation': 'ENV'},
                ],
            },
            {
                'name': 'Faculty of Computing',
                'abbreviation': 'COM',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                ],
            },
            {
                'name': 'Faculty of Communication and Media Studies',
                'abbreviation': 'CMS',
                'departments': [
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Journalism', 'abbreviation': 'JRN'},
                    {'name': 'Public Relations', 'abbreviation': 'PUR'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Entrepreneurship', 'abbreviation': 'ENT'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SSC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                ],
            },
        ],
    },
    {
        'name': 'Cosmopolitan University',
        'abbreviation': 'COSMOPOLITAN',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Science and Technology',
                'abbreviation': 'SCT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                ],
            },
            {
                'name': 'Faculty of Management and Social Sciences',
                'abbreviation': 'MSS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
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
        'name': 'Canadian University of Nigeria',
        'abbreviation': 'CUN',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Science and Technology',
                'abbreviation': 'SCT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Data Science', 'abbreviation': 'DAS'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                ],
            },
            {
                'name': 'Faculty of Management and Social Sciences',
                'abbreviation': 'MSS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
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
        'name': 'Prime University',
        'abbreviation': 'PRIME',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Science and Computing',
                'abbreviation': 'SAC',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Data Science', 'abbreviation': 'DAS'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                ],
            },
            {
                'name': 'Faculty of Social and Management Sciences',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Allied Medical Sciences',
                'abbreviation': 'AMS',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
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
        'name': 'Miva Open University',
        'abbreviation': 'MIVA',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Computing',
                'abbreviation': 'COM',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Data Science', 'abbreviation': 'DAS'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                ],
            },
            {
                'name': 'School of Management and Social Sciences',
                'abbreviation': 'MSS',
                'departments': [
                    {'name': 'Business Management', 'abbreviation': 'BAM'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Public Policy and Administration', 'abbreviation': 'PPA'},
                    {'name': 'Entrepreneurship', 'abbreviation': 'ENT'},
                    {'name': 'Criminology and Security Studies', 'abbreviation': 'CSS'},
                ],
            },
            {
                'name': 'School of Communication and Media',
                'abbreviation': 'SCM',
                'departments': [
                    {'name': 'Mass Communication and Media Studies', 'abbreviation': 'MSC'},
                ],
            },
            {
                'name': 'School of Allied Health Sciences',
                'abbreviation': 'AHS',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
                ],
            },
        ],
    },
    {
        'name': 'European University of Nigeria',
        'abbreviation': 'EUN',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Medical and Health Sciences',
                'abbreviation': 'MHS',
                'departments': [
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                    {'name': 'Human Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Human Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Medical Physiology', 'abbreviation': 'PSL'},
                    {'name': 'Medicinal Chemistry', 'abbreviation': 'MCH'},
                    {'name': 'Medical Physics', 'abbreviation': 'MPH'},
                ],
            },
            {
                'name': 'Faculty of Science and Technology',
                'abbreviation': 'SCT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                ],
            },
        ],
    },
    {
        'name': 'Amaj University',
        'abbreviation': 'AMAJ',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Science and Technology',
                'abbreviation': 'SCT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                ],
            },
            {
                'name': 'Faculty of Management and Social Sciences',
                'abbreviation': 'MSS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
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
        'name': 'Al-Muhibbah Open University',
        'abbreviation': 'AMOU',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Computing and Information Technology',
                'abbreviation': 'CIT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Data Science and Analytics', 'abbreviation': 'DSA'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                ],
            },
            {
                'name': 'School of Business and Management',
                'abbreviation': 'SBM',
                'departments': [
                    {'name': 'Accounting and Finance', 'abbreviation': 'ACF'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Entrepreneurship', 'abbreviation': 'ENT'},
                    {'name': 'Project Management', 'abbreviation': 'PMT'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'International Studies', 'abbreviation': 'INS'},
                ],
            },
            {
                'name': 'School of Health Sciences',
                'abbreviation': 'SHS',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
                    {'name': 'Health Care and Hospital Management', 'abbreviation': 'HHM'},
                ],
            },
        ],
    },
    {
        'name': 'African School of Economics',
        'abbreviation': 'ASE',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Business and Economics',
                'abbreviation': 'BUE',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Econometrics', 'abbreviation': 'ECT'},
                    {'name': 'Marketing and Management', 'abbreviation': 'MAM'},
                ],
            },
            {
                'name': 'Faculty of Science and Technology',
                'abbreviation': 'SCT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SSC',
                'departments': [
                    {'name': 'Criminology and Security Studies', 'abbreviation': 'CSS'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                ],
            },
        ],
    },
    {
        'name': 'Dorben Polytechnic',
        'abbreviation': 'DORBEN',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'SEN',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'School of Environmental Studies',
                'abbreviation': 'SES',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management and Valuation', 'abbreviation': 'EMV'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
                    {'name': 'Surveying and Geo-Informatics', 'abbreviation': 'SGI'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Applied Sciences',
                'abbreviation': 'SAS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Food Technology', 'abbreviation': 'FOT'},
                    {'name': 'Hospitality Management', 'abbreviation': 'HOM'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'School of Business Studies',
                'abbreviation': 'SBS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Information and Communication Technology',
                'abbreviation': 'ICT',
                'departments': [
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                ],
            },
        ],
    },
    {
        'name': 'Citi Polytechnic',
        'abbreviation': 'CITIPOLY',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'SEN',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                ],
            },
            {
                'name': 'School of Environmental Studies',
                'abbreviation': 'SES',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management and Valuation', 'abbreviation': 'EMV'},
                ],
            },
            {
                'name': 'School of Applied Sciences',
                'abbreviation': 'SAS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'School of Business Studies',
                'abbreviation': 'SBS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
        ],
    },
    {
        'name': 'LeadTech School of Management and Technology',
        'abbreviation': 'LEADTECH',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Management',
                'abbreviation': 'SMG',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Technology',
                'abbreviation': 'STE',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'School of Environmental Studies',
                'abbreviation': 'SES',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QTS'},
                ],
            },
        ],
    },
    {
        'name': 'Flyingdove Institute of Technology',
        'abbreviation': 'FLYINGDOVE',
        'state': 'FCT',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'SEN',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                ],
            },
            {
                'name': 'School of Applied Sciences',
                'abbreviation': 'SAS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'School of Business Studies',
                'abbreviation': 'SBS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                ],
            },
        ],
    },
]