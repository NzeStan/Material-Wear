# academic_directory/management/commands/state_data/gombe.py
"""
Universities in Gombe State.
Add more universities to this list as needed.
"""

UNIVERSITIES = [
    {
        'name': 'Federal University, Kashere',
        'abbreviation': 'FUKASHERE',
        'state': 'GOMBE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                ],
            },
            {
                'name': 'Faculty of Humanities and Social Sciences',
                'abbreviation': 'HSS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Education and Biology', 'abbreviation': 'EDB'},
                    {'name': 'Education and Chemistry', 'abbreviation': 'EDC'},
                    {'name': 'Education and Physics', 'abbreviation': 'EDP'},
                    {'name': 'Education and Mathematics', 'abbreviation': 'EDM'},
                    {'name': 'Education and Economics', 'abbreviation': 'EDE'},
                    {'name': 'Education and Social Studies', 'abbreviation': 'EDS'},
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
        ],
    },
    {
        'name': 'National Open University of Nigeria',
        'abbreviation': 'NOUN',
        'state': 'GOMBE',
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
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts and Social Science Education', 'abbreviation': 'ASE'},
                    {'name': 'Science Education', 'abbreviation': 'SCE'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                ],
            },
            {
                'name': 'Faculty of Health Sciences',
                'abbreviation': 'HSC',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
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
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                ],
            },
            {
                'name': 'Faculty of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
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
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                ],
            },
        ],
    },
    {
        'name': 'Federal Polytechnic, Kaltungo',
        'abbreviation': 'FEDPOLYKLT',
        'state': 'GOMBE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Engineering',
                'abbreviation': 'SEN',
                'departments': [
                    {'name': 'Electrical and Electronics Engineering Technology', 'abbreviation': 'EET'},
                    {'name': 'Computer Engineering Technology', 'abbreviation': 'CPE'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SST',
                'departments': [
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Leisure and Tourism Management', 'abbreviation': 'LTM'},
                ],
            },
            {
                'name': 'School of Management Studies',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of General Studies',
                'abbreviation': 'SGS',
                'departments': [
                    {'name': 'Crime Management and Control', 'abbreviation': 'CMC'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                ],
            },
        ],
    },
    {
        'name': 'Federal College of Education (Technical), Gombe',
        'abbreviation': 'FCETGOMBE',
        'state': 'GOMBE',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Education',
                'abbreviation': 'SED',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                ],
            },
            {
                'name': 'School of Business Education',
                'abbreviation': 'SBE',
                'departments': [
                    {'name': 'Business Education', 'abbreviation': 'BUE'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                ],
            },
            {
                'name': 'School of Vocational Education',
                'abbreviation': 'SVE',
                'departments': [
                    {'name': 'Agricultural Science Education', 'abbreviation': 'ASE'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEE'},
                    {'name': 'Technical Education', 'abbreviation': 'TED'},
                ],
            },
            {
                'name': 'School of Science Education',
                'abbreviation': 'SSE',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIE'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHE'},
                    {'name': 'Physics Education', 'abbreviation': 'PHE'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTE'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISE'},
                    {'name': 'Computer Science Education', 'abbreviation': 'CSE'},
                ],
            },
            {
                'name': 'School of Technical Education',
                'abbreviation': 'STE',
                'departments': [
                    {'name': 'Woodwork Education', 'abbreviation': 'WDE'},
                    {'name': 'Automobile Technology Education', 'abbreviation': 'ATE'},
                    {'name': 'Building Technology Education', 'abbreviation': 'BTE'},
                    {'name': 'Electrical and Electronics Education', 'abbreviation': 'EEE'},
                    {'name': 'Metalwork Technology Education', 'abbreviation': 'MTE'},
                ],
            },
            {
                'name': 'School of Primary and Early Child Care Education',
                'abbreviation': 'PEC',
                'departments': [
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                    {'name': 'Early Childhood Care Education', 'abbreviation': 'ECE'},
                ],
            },
            {
                'name': 'School of Arts and Social Sciences Secondary Education',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'EDE'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SSE'},
                    {'name': 'Economics Education', 'abbreviation': 'ECE'},
                ],
            },
            {
                'name': 'School of Languages Secondary Education',
                'abbreviation': 'SLG',
                'departments': [
                    {'name': 'Hausa Education', 'abbreviation': 'HAE'},
                    {'name': 'French Education', 'abbreviation': 'FRE'},
                    {'name': 'Islamic Studies Education', 'abbreviation': 'ISE'},
                ],
            },
            {
                'name': 'School of General Studies',
                'abbreviation': 'SGS',
                'departments': [
                    {'name': 'General Studies', 'abbreviation': 'GST'},
                ],
            },
        ],
    },
    {
        'name': 'Gombe State University',
        'abbreviation': 'GSU',
        'state': 'GOMBE',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                    {'name': 'English Language', 'abbreviation': 'ENG'},
                    {'name': 'Religious Studies', 'abbreviation': 'REL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Physics Education', 'abbreviation': 'PHE'},
                    {'name': 'Biology Education', 'abbreviation': 'BIE'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHE'},
                    {'name': 'Geography Education', 'abbreviation': 'GEE'},
                    {'name': 'Computer Science Education', 'abbreviation': 'CSE'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTE'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biological Sciences', 'abbreviation': 'BIO'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Geology', 'abbreviation': 'GEL'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Sharia Law', 'abbreviation': 'SHA'},
                    {'name': 'Public Law', 'abbreviation': 'PUL'},
                ],
            },
            {
                'name': 'Faculty of Pharmaceutical Sciences',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmacognosy and Drug Development', 'abbreviation': 'PDD'},
                    {'name': 'Pharmaceutics and Pharmaceutical Technology', 'abbreviation': 'PPT'},
                    {'name': 'Clinical Pharmacy and Pharmacy Practice', 'abbreviation': 'CPP'},
                    {'name': 'Pharmaceutics and Medicinal Chemistry', 'abbreviation': 'PMC'},
                    {'name': 'Pharmacology and Therapeutics', 'abbreviation': 'PCT'},
                    {'name': 'Pharmaceutical Microbiology', 'abbreviation': 'PMB'},
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
                'name': 'College of Medical Sciences',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Human Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Human Physiology', 'abbreviation': 'PSL'},
                    {'name': 'Medical Biochemistry', 'abbreviation': 'MBC'},
                    {'name': 'Chemical Pathology', 'abbreviation': 'CHP'},
                    {'name': 'Clinical Pharmacology and Therapeutics', 'abbreviation': 'CPT'},
                    {'name': 'Hematology and Blood Transfusion', 'abbreviation': 'HBT'},
                    {'name': 'Histopathology', 'abbreviation': 'HIS'},
                    {'name': 'Medical Microbiology and Immunology', 'abbreviation': 'MMI'},
                    {'name': 'Anaesthesia', 'abbreviation': 'ANE'},
                    {'name': 'E.N.T', 'abbreviation': 'ENT'},
                    {'name': 'Internal Medicine', 'abbreviation': 'INM'},
                    {'name': 'Community Medicine', 'abbreviation': 'COM'},
                    {'name': 'General Surgery', 'abbreviation': 'GSU'},
                    {'name': 'Paediatrics', 'abbreviation': 'PAE'},
                    {'name': 'Obstetrics and Gynaecology', 'abbreviation': 'OBG'},
                    {'name': 'Ophthalmology', 'abbreviation': 'OPH'},
                    {'name': 'Radiology', 'abbreviation': 'RAD'},
                ],
            },
        ],
    },
    {
        'name': 'Gombe State University of Science and Technology',
        'abbreviation': 'GSUST',
        'state': 'GOMBE',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Education and Biology', 'abbreviation': 'EDB'},
                    {'name': 'Education and Chemistry', 'abbreviation': 'EDC'},
                    {'name': 'Education and Physics', 'abbreviation': 'EDP'},
                    {'name': 'Education and Mathematics', 'abbreviation': 'EDM'},
                    {'name': 'Education and Computer Science', 'abbreviation': 'EDP'},
                    {'name': 'Education and Economics', 'abbreviation': 'EDE'},
                    {'name': 'Education and Social Studies', 'abbreviation': 'EDS'},
                    {'name': 'Education and English', 'abbreviation': 'EDL'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Information Systems', 'abbreviation': 'IFS'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
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
                    {'name': 'Pharmacy', 'abbreviation': 'PHR'},
                ],
            },
        ],
    },
    {
        'name': 'Gombe State Polytechnic',
        'abbreviation': 'GSPOLY',
        'state': 'GOMBE',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Engineering and Engineering Technology',
                'abbreviation': 'SEE',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
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
            {
                'name': 'School of Management Studies',
                'abbreviation': 'SMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Office Technology Management', 'abbreviation': 'OTM'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of General Studies',
                'abbreviation': 'SGS',
                'departments': [
                    {'name': 'General Studies', 'abbreviation': 'GST'},
                ],
            },
        ],
    },
    {
        'name': 'Gombe State College of Education',
        'abbreviation': 'COEBILLIRI',
        'state': 'GOMBE',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Hausa', 'abbreviation': 'HAU'},
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
        'name': 'Gombe State College of Legal Studies',
        'abbreviation': 'COENAFADA',
        'state': 'GOMBE',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Legal Studies',
                'abbreviation': 'SLS',
                'departments': [
                    {'name': 'Law', 'abbreviation': 'LAW'},
                    {'name': 'Sharia Law', 'abbreviation': 'SHA'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                ],
            },
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Hausa', 'abbreviation': 'HAU'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                ],
            },
            {
                'name': 'School of Business Studies',
                'abbreviation': 'SBS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
        ],
    },
    {
        'name': 'North-Eastern University',
        'abbreviation': 'NEU',
        'state': 'GOMBE',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Science and Computing',
                'abbreviation': 'SAC',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Information Technology', 'abbreviation': 'IFT'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYB'},
                    {'name': 'Software Engineering', 'abbreviation': 'SWE'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                    {'name': 'Chemical Sciences', 'abbreviation': 'CHS'},
                    {'name': 'Biotechnology', 'abbreviation': 'BTH'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Common Law', 'abbreviation': 'CLW'},
                    {'name': 'Common and Islamic Law', 'abbreviation': 'CIL'},
                    {'name': 'Public and Private Law', 'abbreviation': 'PPL'},
                ],
            },
            {
                'name': 'Faculty of Communications, Management and Social Sciences',
                'abbreviation': 'CMS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Procurement Management', 'abbreviation': 'PMT'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Economics and Development Studies', 'abbreviation': 'EDS'},
                    {'name': 'International Relations', 'abbreviation': 'INR'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Allied Health Sciences',
                'abbreviation': 'AHS',
                'departments': [
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Public Health', 'abbreviation': 'PUB'},
                ],
            },
        ],
    },
    {
        'name': 'Jewel University',
        'abbreviation': 'JEWEL',
        'state': 'GOMBE',
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
                    {'name': 'Banking and Finance', 'abbreviation': 'BFN'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Criminology and Security Studies', 'abbreviation': 'CSS'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Policy and Administrative Studies', 'abbreviation': 'PAS'},
                    {'name': 'Project Management', 'abbreviation': 'PMT'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building', 'abbreviation': 'BLD'},
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
        ],
    },
]