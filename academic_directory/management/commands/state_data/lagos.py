# academic_directory/management/commands/state_data/lagos.py
"""Universities and Polytechnics in Lagos State."""

UNIVERSITIES = [
    # UNIVERSITY OF LAGOS
    {
        'name': 'University of Lagos',
        'abbreviation': 'UNILAG',
        'state': 'LAGOS',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ARTS',
                'departments': [
                    {'name': 'Creative Arts', 'abbreviation': 'CRA'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'European Languages', 'abbreviation': 'EUL'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'History and Strategic Studies', 'abbreviation': 'HSS'},
                    {'name': 'Linguistics, African and Asian Studies', 'abbreviation': 'LAA'},
                    {'name': 'Philosophy', 'abbreviation': 'PHI'},
                ],
            },
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Pharmacology', 'abbreviation': 'PHA'},
                    {'name': 'Physiology', 'abbreviation': 'PSL'},
                ],
            },
            {
                'name': 'Faculty of Clinical Sciences',
                'abbreviation': 'CLS',
                'departments': [
                    {'name': 'Anaesthesia', 'abbreviation': 'ANA'},
                    {'name': 'Haematology', 'abbreviation': 'HAE'},
                    {'name': 'Medicine', 'abbreviation': 'MED'},
                    {'name': 'Obstetrics and Gynaecology', 'abbreviation': 'OBG'},
                    {'name': 'Ophthalmology', 'abbreviation': 'OPH'},
                    {'name': 'Paediatrics', 'abbreviation': 'PAE'},
                    {'name': 'Psychiatry', 'abbreviation': 'PSY'},
                    {'name': 'Radiology', 'abbreviation': 'RAD'},
                    {'name': 'Surgery', 'abbreviation': 'SUR'},
                ],
            },
            {
                'name': 'Faculty of Dental Sciences',
                'abbreviation': 'DEN',
                'departments': [
                    {'name': 'Child Dental Health', 'abbreviation': 'CDH'},
                    {'name': 'Oral and Maxillofacial Surgery', 'abbreviation': 'OMS'},
                    {'name': 'Preventive Dentistry', 'abbreviation': 'PDN'},
                    {'name': 'Restorative Dentistry', 'abbreviation': 'RDN'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts and Social Sciences Education', 'abbreviation': 'ASE'},
                    {'name': 'Educational Administration and Planning', 'abbreviation': 'EAP'},
                    {'name': 'Human Kinetics and Health Education', 'abbreviation': 'HKH'},
                    {'name': 'Science and Technology Education', 'abbreviation': 'STE'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Chemical and Polymer Engineering', 'abbreviation': 'CPO'},
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Marine Engineering', 'abbreviation': 'MRE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Metallurgical and Materials Engineering', 'abbreviation': 'MME'},
                    {'name': 'Surveying and Geoinformatics', 'abbreviation': 'SRV'},
                    {'name': 'Systems Engineering', 'abbreviation': 'SYE'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Faculty of Law',
                'abbreviation': 'LAW',
                'departments': [
                    {'name': 'Commercial and Industrial Law', 'abbreviation': 'CIL'},
                    {'name': 'Jurisprudence and International Law', 'abbreviation': 'JIL'},
                    {'name': 'Private and Property Law', 'abbreviation': 'PPL'},
                    {'name': 'Public Law', 'abbreviation': 'PUL'},
                ],
            },
            {
                'name': 'Faculty of Management Sciences',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accounting', 'abbreviation': 'ACC'},
                    {'name': 'Actuarial Science and Insurance', 'abbreviation': 'ASI'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Finance', 'abbreviation': 'FIN'},
                    {'name': 'Industrial Relations and Personnel Management', 'abbreviation': 'IRP'},
                    {'name': 'Management and Organisational Behaviour', 'abbreviation': 'MOB'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                ],
            },
            {
                'name': 'Faculty of Pharmacy',
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
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Cell Biology and Genetics', 'abbreviation': 'CBG'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Marine Sciences', 'abbreviation': 'MRS'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SS',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Mass Communication', 'abbreviation': 'MSC'},
                    {'name': 'Political Science', 'abbreviation': 'POS'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
    
    # LAGOS STATE UNIVERSITY
    {
        'name': 'Lagos State University',
        'abbreviation': 'LASU',
        'state': 'LAGOS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Arabic', 'abbreviation': 'ARB'},
                    {'name': 'Chinese Studies', 'abbreviation': 'CHI'},
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                    {'name': 'History and International Studies', 'abbreviation': 'HIS'},
                    {'name': 'Language and Communication Arts', 'abbreviation': 'LCA'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                ],
            },
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Anatomy', 'abbreviation': 'ANA'},
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Nursing Science', 'abbreviation': 'NRS'},
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
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Curriculum Studies', 'abbreviation': 'CUR'},
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                    {'name': 'Health Education', 'abbreviation': 'HED'},
                    {'name': 'Physical Education', 'abbreviation': 'PED'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Social Science Education', 'abbreviation': 'SSE'},
                    {'name': 'Vocational and Technical Education', 'abbreviation': 'VTE'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Chemical and Polymer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Civil and Environmental Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'COE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Mechatronics Engineering', 'abbreviation': 'MEC'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
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
                    {'name': 'Private and Property Law', 'abbreviation': 'PPL'},
                    {'name': 'Public Law', 'abbreviation': 'PUL'},
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
                    {'name': 'Insurance', 'abbreviation': 'INS'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Transport Management', 'abbreviation': 'TRM'},
                ],
            },
            {
                'name': 'Faculty of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Fisheries', 'abbreviation': 'FIS'},
                    {'name': 'Geography and Planning', 'abbreviation': 'GAP'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Psychology', 'abbreviation': 'PSY'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                ],
            },
        ],
    },
    
    # LAGOS STATE UNIVERSITY OF SCIENCE AND TECHNOLOGY (formerly Lagos State Polytechnic)
    {
        'name': 'Lagos State University of Science and Technology',
        'abbreviation': 'LASUSTECH',
        'state': 'LAGOS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'College of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Extension', 'abbreviation': 'AEX'},
                    {'name': 'Animal Production', 'abbreviation': 'ANP'},
                    {'name': 'Crop Production', 'abbreviation': 'CRP'},
                    {'name': 'Fisheries Technology', 'abbreviation': 'FIS'},
                    {'name': 'Forestry Technology', 'abbreviation': 'FRT'},
                    {'name': 'Horticultural Technology', 'abbreviation': 'HRT'},
                ],
            },
            {
                'name': 'College of Applied Social Sciences',
                'abbreviation': 'ASS',
                'departments': [
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                    {'name': 'Music Technology', 'abbreviation': 'MUT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'College of Basic Sciences',
                'abbreviation': 'BAS',
                'departments': [
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTS'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics with Electronics', 'abbreviation': 'PHE'},
                ],
            },
            {
                'name': 'College of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical/Electronic Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Mechatronics Engineering', 'abbreviation': 'MTR'},
                ],
            },
            {
                'name': 'College of Environmental Design and Technology',
                'abbreviation': 'EDT',
                'departments': [
                    {'name': 'Architectural Technology', 'abbreviation': 'ARC'},
                    {'name': 'Arts and Design', 'abbreviation': 'ARD'},
                    {'name': 'Building Technology', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management and Valuation', 'abbreviation': 'EST'},
                    {'name': 'Quantity Surveying', 'abbreviation': 'QSV'},
                    {'name': 'Surveying and Geo-informatics', 'abbreviation': 'SGV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'College of Management Sciences',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Insurance', 'abbreviation': 'INS'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                    {'name': 'Taxation', 'abbreviation': 'TAX'},
                    {'name': 'Transport and Logistics Management', 'abbreviation': 'TLM'},
                ],
            },
        ],
    },
    
    # LAGOS STATE UNIVERSITY OF EDUCATION (formerly Adeniran Ogunsanya College of Education)
    {
        'name': 'Lagos State University of Education',
        'abbreviation': 'LASUED',
        'state': 'LAGOS',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Arts and Social Sciences Education',
                'abbreviation': 'FASSE',
                'departments': [
                    {'name': 'Arabic Education', 'abbreviation': 'ARB'},
                    {'name': 'Christian Religious Studies Education', 'abbreviation': 'CRS'},
                    {'name': 'Economics Education', 'abbreviation': 'ECO'},
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'French Education', 'abbreviation': 'FRN'},
                    {'name': 'Geography Education', 'abbreviation': 'GEO'},
                    {'name': 'History Education', 'abbreviation': 'HIS'},
                    {'name': 'Islamic Studies Education', 'abbreviation': 'ISL'},
                    {'name': 'Political Science Education', 'abbreviation': 'POL'},
                    {'name': 'Social Studies Education', 'abbreviation': 'SST'},
                    {'name': 'Yoruba Education', 'abbreviation': 'YOR'},
                ],
            },
            {
                'name': 'Faculty of Early Childhood and Primary Education',
                'abbreviation': 'FECPE',
                'departments': [
                    {'name': 'Early Childhood Care Education', 'abbreviation': 'ECE'},
                    {'name': 'Primary Education Studies', 'abbreviation': 'PES'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Educational Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Educational Management', 'abbreviation': 'EDM'},
                    {'name': 'Guidance and Counselling', 'abbreviation': 'GAC'},
                ],
            },
            {
                'name': 'Faculty of Sciences Education',
                'abbreviation': 'FSE',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science Education', 'abbreviation': 'CSC'},
                    {'name': 'Health Education', 'abbreviation': 'HED'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physical Education', 'abbreviation': 'PED'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                ],
            },
            {
                'name': 'Faculty of Vocational and Technical Education',
                'abbreviation': 'FVTE',
                'departments': [
                    {'name': 'Agricultural Education', 'abbreviation': 'AGR'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Home Economics Education', 'abbreviation': 'HEC'},
                    {'name': 'Technical Education', 'abbreviation': 'TED'},
                ],
            },
        ],
    },
    
    # YABA COLLEGE OF TECHNOLOGY
    {
        'name': 'Yaba College of Technology',
        'abbreviation': 'YABATECH',
        'state': 'LAGOS',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Art, Design and Printing',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Ceramics', 'abbreviation': 'CER'},
                    {'name': 'Fashion Design', 'abbreviation': 'FAS'},
                    {'name': 'Fine Art', 'abbreviation': 'FNA'},
                    {'name': 'General Art', 'abbreviation': 'GAT'},
                    {'name': 'Graphic Design', 'abbreviation': 'GRD'},
                    {'name': 'Printing Technology', 'abbreviation': 'PRT'},
                    {'name': 'Sculpture', 'abbreviation': 'SCL'},
                    {'name': 'Textile Design', 'abbreviation': 'TEX'},
                ],
            },
            {
                'name': 'School of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural and Bio-Environmental Engineering', 'abbreviation': 'ABE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Electrical Engineering', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Metallurgical Engineering', 'abbreviation': 'MTL'},
                    {'name': 'Polymer and Textile Engineering', 'abbreviation': 'PTE'},
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
                    {'name': 'Surveying and Geo-informatics', 'abbreviation': 'SGV'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'School of Management and Business Studies',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Business Administration and Management', 'abbreviation': 'BAM'},
                    {'name': 'Insurance', 'abbreviation': 'INS'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Office Technology and Management', 'abbreviation': 'OTM'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'School of Science',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Hospitality Management', 'abbreviation': 'HSM'},
                    {'name': 'Mathematics and Statistics', 'abbreviation': 'MTS'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Nutrition and Dietetics', 'abbreviation': 'NDT'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                ],
            },
            {
                'name': 'School of Technical Education',
                'abbreviation': 'TED',
                'departments': [
                    {'name': 'Civil Engineering Education', 'abbreviation': 'CVE'},
                    {'name': 'Electrical Engineering Education', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical Engineering Education', 'abbreviation': 'MEE'},
                ],
            },
        ],
    },
    
    # FEDERAL COLLEGE OF EDUCATION (TECHNICAL), AKOKA
    {
        'name': 'Federal College of Education (Technical), Akoka',
        'abbreviation': 'FCETAKOKA',
        'state': 'LAGOS',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'School of Business Education',
                'abbreviation': 'BUS',
                'departments': [
                    {'name': 'Accountancy Education', 'abbreviation': 'ACC'},
                    {'name': 'Business Education', 'abbreviation': 'BED'},
                    {'name': 'Marketing Education', 'abbreviation': 'MKT'},
                    {'name': 'Office Technology Education', 'abbreviation': 'OTE'},
                ],
            },
            {
                'name': 'School of Industrial and Technical Education',
                'abbreviation': 'ITE',
                'departments': [
                    {'name': 'Building Technology Education', 'abbreviation': 'BLD'},
                    {'name': 'Electrical/Electronics Education', 'abbreviation': 'ELE'},
                    {'name': 'Mechanical/Metalwork Education', 'abbreviation': 'MEC'},
                ],
            },
            {
                'name': 'School of Science Education',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biology Education', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry Education', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science Education', 'abbreviation': 'CSC'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
    
    # MICHAEL OTEDOLA COLLEGE OF PRIMARY EDUCATION (now part of LASUED)
    # Note: This is now merged into LASUED but included for completeness
    
    # PRIVATE UNIVERSITIES IN LAGOS STATE
    {
        'name': 'Pan-Atlantic University',
        'abbreviation': 'PAU',
        'state': 'LAGOS',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Lagos Business School',
                'abbreviation': 'LBS',
                'departments': [
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                ],
            },
            {
                'name': 'School of Media and Communication',
                'abbreviation': 'SMC',
                'departments': [
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                ],
            },
        ],
    },
    {
        'name': 'Caleb University',
        'abbreviation': 'CALEB',
        'state': 'LAGOS',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'Faculty of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                ],
            },
            {
                'name': 'Faculty of Basic Medical Sciences',
                'abbreviation': 'BMS',
                'departments': [
                    {'name': 'Nursing', 'abbreviation': 'NRS'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                ],
            },
        ],
    },
]