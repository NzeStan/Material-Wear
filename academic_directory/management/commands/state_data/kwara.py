# academic_directory/management/commands/state_data/kwara.py
"""Universities and Polytechnics in Kwara State."""

UNIVERSITIES = [
    # UNIVERSITY OF ILORIN
    {
        'name': 'University of Ilorin',
        'abbreviation': 'UNILORIN',
        'state': 'KWARA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Production', 'abbreviation': 'ANP'},
                    {'name': 'Crop Production', 'abbreviation': 'CRP'},
                    {'name': 'Forestry and Wildlife', 'abbreviation': 'FWL'},
                    {'name': 'Home Economics and Food Science', 'abbreviation': 'HEF'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'Christian Religious Studies', 'abbreviation': 'CRS'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                    {'name': 'Linguistics and Nigerian Languages', 'abbreviation': 'LNL'},
                    {'name': 'Performing Arts', 'abbreviation': 'PFA'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                ],
            },
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Physiology', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Clinical Sciences',
                'abbreviation': 'CLS',
                'departments': [
                    {'name': 'Anaesthesia', 'abbreviation': 'ANA'},
                    {'name': 'Chemical Pathology', 'abbreviation': 'CHP'},
                    {'name': 'Haematology', 'abbreviation': 'HAE'},
                    {'name': 'Medicine', 'abbreviation': 'MED'},
                    {'name': 'Medical Microbiology', 'abbreviation': 'MMB'},
                    {'name': 'Ophthalmology', 'abbreviation': 'OPH'},
                    {'name': 'Paediatrics', 'abbreviation': 'PAE'},
                    {'name': 'Pathology', 'abbreviation': 'PAT'},
                    {'name': 'Pharmacology', 'abbreviation': 'PHA'},
                    {'name': 'Radiology', 'abbreviation': 'RAD'},
                    {'name': 'Surgery', 'abbreviation': 'SUR'},
                ],
            },
            {
                'name': 'Faculty of Communication and Information Sciences',
                'abbreviation': 'CIS',
                'departments': [
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Telecommunication Science', 'abbreviation': 'TCM'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Adult and Primary Education', 'abbreviation': 'APE'},
                    {'name': 'Arts Education', 'abbreviation': 'AED'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Educational Technology', 'abbreviation': 'EDT'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Health Promotion and Environmental Health', 'abbreviation': 'HPE'},
                    {'name': 'Human Kinetics Education', 'abbreviation': 'HKE'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Social Sciences Education', 'abbreviation': 'SSE'},
                ],
            },
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural and Biosystems Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Biomedical Engineering', 'abbreviation': 'BME'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Materials and Metallurgical Engineering', 'abbreviation': 'MME'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Water Resources and Environmental Engineering', 'abbreviation': 'WRE'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                    {'name': 'Geography and Environmental Management', 'abbreviation': 'GEM'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Business Law', 'abbreviation': 'BUL'},
                    {'name': 'International Law', 'abbreviation': 'INL'},
                    {'name': 'Jurisprudence and Legal Theory', 'abbreviation': 'JLT'},
                    {'name': 'Private Law', 'abbreviation': 'PRL'},
                    {'name': 'Public Law', 'abbreviation': 'PUL'},
                ],
            },
            {
                'name': 'Faculty of Life Sciences',
                'abbreviation': 'LFS',
                'departments': [
                    {'name': 'Cell Biology and Genetics', 'abbreviation': 'CBG'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Plant Biology', 'abbreviation': 'PLB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Industrial Relations and Personnel Management', 'abbreviation': 'IRP'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
            {
                'name': 'Faculty of Pharmaceutical Sciences',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Clinical Pharmacy', 'abbreviation': 'CPH'},
                    {'name': 'Pharmaceutics', 'abbreviation': 'PHA'},
                    {'name': 'Pharmaceutical Chemistry', 'abbreviation': 'PCH'},
                    {'name': 'Pharmacognosy', 'abbreviation': 'PHG'},
                    {'name': 'Pharmacology', 'abbreviation': 'PHL'},
                ],
            },
            {
                'name': 'Faculty of Physical Sciences',
                'abbreviation': 'PHS',
                'departments': [
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology and Mineral Sciences', 'abbreviation': 'GEO'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Business and Entrepreneurship', 'abbreviation': 'BEN'},
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
            {
                'name': 'Faculty of Veterinary Medicine',
                'abbreviation': 'VET',
                'departments': [
                    {'name': 'Veterinary Anatomy', 'abbreviation': 'VAN'},
                    {'name': 'Veterinary Medicine', 'abbreviation': 'VMD'},
                    {'name': 'Veterinary Microbiology', 'abbreviation': 'VMB'},
                    {'name': 'Veterinary Pathology', 'abbreviation': 'VPT'},
                    {'name': 'Veterinary Pharmacology', 'abbreviation': 'VPM'},
                    {'name': 'Veterinary Physiology', 'abbreviation': 'VPH'},
                    {'name': 'Veterinary Public Health', 'abbreviation': 'VPH'},
                    {'name': 'Veterinary Surgery', 'abbreviation': 'VSU'},
                ],
            },
        ],
    },
    
    # KWARA STATE UNIVERSITY, MALETE
    {
        'name': 'Kwara State University',
        'abbreviation': 'KWASU',
        'state': 'KWARA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Production', 'abbreviation': 'ANP'},
                    {'name': 'Crop Production', 'abbreviation': 'CRP'},
                    {'name': 'Fisheries and Aquaculture', 'abbreviation': 'FIS'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics', 'abbreviation': 'LIN'},
                    {'name': 'Theatre and Film Studies', 'abbreviation': 'TFS'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts Education', 'abbreviation': 'AED'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Social Science Education', 'abbreviation': 'SSE'},
                ],
            },
            {
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Computer Engineering', 'abbreviation': 'ECE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Faculty of Information and Communication Technology',
                'abbreviation': 'ICT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Cyber Security', 'abbreviation': 'CYS'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
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
                'name': 'Faculty of Life Sciences',
                'abbreviation': 'LFS',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Plant Biology', 'abbreviation': 'PLB'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
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
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Physical Sciences',
                'abbreviation': 'PHS',
                'departments': [
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Industrial Chemistry', 'abbreviation': 'ICH'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
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
        ],
    },
    
    # KWARA STATE POLYTECHNIC, ILORIN
    {
        'name': 'Kwara State Polytechnic, Ilorin',
        'abbreviation': 'KWARAPOLY',
        'state': 'KWARA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Institute of Applied Sciences',
                'abbreviation': 'IAS',
                'departments': [
                    {'name': 'Agricultural Technology', 'abbreviation': 'AGT'},
                    {'name': 'Hospitality Management', 'abbreviation': 'HSM'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                ],
            },
            {
                'name': 'Institute of Environmental Studies',
                'abbreviation': 'IES',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management and Valuation', 'abbreviation': 'EST'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Surveying and Geo-informatics', 'abbreviation': 'SGV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Institute of Finance and Management Studies',
                'abbreviation': 'IFMS',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Procurement and Supply Chain Management', 'abbreviation': 'PSC'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Institute of Information and Communication Technology',
                'abbreviation': 'IICT',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Networking and Cloud Computing', 'abbreviation': 'NCC'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                    {'name': 'Software and Web Development', 'abbreviation': 'SWD'},
                ],
            },
            {
                'name': 'Institute of Technology',
                'abbreviation': 'IOT',
                'departments': [
                    {'name': 'Agricultural and Bio-Environmental Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Civil Engineering Technology', 'abbreviation': 'CVE'},
                    {'name': 'Electrical/Electronics Engineering Technology', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering Technology', 'abbreviation': 'MEE'},
                    {'name': 'Metallurgical Engineering Technology', 'abbreviation': 'MTL'},
                    {'name': 'Mining Engineering Technology', 'abbreviation': 'MNG'},
                ],
            },
            {
                'name': 'Centre for Open, Distance, Flexible and e-Learning',
                'abbreviation': 'ODFEL',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                ],
            },
        ],
    },
    
    # KWARA STATE COLLEGE OF EDUCATION, ILORIN
    {
        'name': 'Kwara State College of Education, Ilorin',
        'abbreviation': 'KWCOEILORIN',
        'state': 'KWARA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'French Education', 'abbreviation': 'FRN'},
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
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                    {'name': 'Technical Education', 'abbreviation': 'TED'},
                ],
            },
        ],
    },
    
    # KWARA STATE COLLEGE OF EDUCATION, ORO
    {
        'name': 'Kwara State College of Education, Oro',
        'abbreviation': 'KWCOEORO',
        'state': 'KWARA',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'French Education', 'abbreviation': 'FRN'},
                    {'name': 'History Education', 'abbreviation': 'HIS'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SST'},
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
                'name': 'School of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                ],
            },
            {
                'name': 'School of Languages',
                'abbreviation': 'LAN',
                'departments': [
                    {'name': 'Arabic Education', 'abbreviation': 'ARB'},
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'French Education', 'abbreviation': 'FRN'},
                    {'name': 'Yoruba Education', 'abbreviation': 'YOR'},
                ],
            },
            {
                'name': 'School of Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'School of Vocational Education',
                'abbreviation': 'VOC',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                ],
            },
        ],
    },
    
    # FEDERAL COLLEGE OF EDUCATION (TECHNICAL), ORO (now Federal University of Education, Oro)
    {
        'name': 'Federal University of Education, Oro',
        'abbreviation': 'FUOORO',
        'state': 'KWARA',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
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
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                    {'name': 'Computer Science Education', 'abbreviation': 'CSC'},
                ],
            },
            {
                'name': 'School of Vocational and Technical Education',
                'abbreviation': 'VTE',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                ],
            },
        ],
    },
    
    # PRIVATE UNIVERSITIES IN KWARA STATE
    {
        'name': 'Al-Hikmah University',
        'abbreviation': 'AL-HIKMAH',
        'state': 'KWARA',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
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
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                ],
            },
        ],
    },
    {
        'name': 'Landmark University',
        'abbreviation': 'LMU',
        'state': 'KWARA',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'College of Agricultural Sciences',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Animal Science', 'abbreviation': 'ANS'},
                ],
            },
            {
                'name': 'College of Business and Social Sciences',
                'abbreviation': 'CBS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                ],
            },
            {
                'name': 'College of Pure and Applied Sciences',
                'abbreviation': 'PAS',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                ],
            },
        ],
    },
    {
        'name': 'Summit University',
        'abbreviation': 'SU',
        'state': 'KWARA',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Arts and Humanities',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'Islamic Studies', 'abbreviation': 'ISL'},
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
                'name': 'Faculty of Natural and Applied Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                ],
            },
        ],
    },
    {
        'name': 'Crown Hill University',
        'abbreviation': 'CHU',
        'state': 'KWARA',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Humanities',
                'abbreviation': 'HUM',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
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
        ],
    },
    {
        'name': 'Thomas Adewumi University',
        'abbreviation': 'TAU',
        'state': 'KWARA',
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
                'name': 'Faculty of Engineering and Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                ],
            },
        ],
    },
]