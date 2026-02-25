# academic_directory/management/commands/state_data/plateau.py
"""Universities and Polytechnics in Plateau State."""

UNIVERSITIES = [
    # UNIVERSITY OF JOS
    {
        'name': 'University of Jos',
        'abbreviation': 'UNIJOS',
        'state': 'PLATEAU',
        'type': 'FEDERAL',
        'faculties': [
            {
                'name': 'Faculty of Agriculture',
                'abbreviation': 'AGR',
                'departments': [
                    {'name': 'Agricultural Economics', 'abbreviation': 'AEC'},
                    {'name': 'Animal Production', 'abbreviation': 'APR'},
                    {'name': 'Crop Production', 'abbreviation': 'CPR'},
                    {'name': 'Soil Science', 'abbreviation': 'SLS'},
                ],
            },
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Linguistics and Nigerian Languages', 'abbreviation': 'LNL'},
                    {'name': 'Religious Studies', 'abbreviation': 'RLS'},
                    {'name': 'Theatre Arts', 'abbreviation': 'THA'},
                    {'name': 'Philosophy', 'abbreviation': 'PHL'},
                    {'name': 'French', 'abbreviation': 'FRN'},
                ],
            },
            {
                'name': 'Faculty of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Arts Education', 'abbreviation': 'AED'},
                    {'name': 'Education Foundations', 'abbreviation': 'EDF'},
                    {'name': 'Educational Psychology', 'abbreviation': 'EPS'},
                    {'name': 'Science Education', 'abbreviation': 'SED'},
                    {'name': 'Social Science Education', 'abbreviation': 'SSE'},
                    {'name': 'Special Education', 'abbreviation': 'SPE'},
                    {'name': 'Library and Information Science', 'abbreviation': 'LIS'},
                    {'name': 'Physical and Health Education', 'abbreviation': 'PHE'},
                ],
            },
            {
                'name': 'Faculty of Engineering',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Civil Engineering', 'abbreviation': 'CVE'},
                    {'name': 'Electrical and Electronics Engineering', 'abbreviation': 'EEE'},
                    {'name': 'Mechanical Engineering', 'abbreviation': 'MEE'},
                    {'name': 'Chemical Engineering', 'abbreviation': 'CHE'},
                    {'name': 'Computer Engineering', 'abbreviation': 'CPE'},
                    {'name': 'Mining Engineering', 'abbreviation': 'MNE'},
                ],
            },
            {
                'name': 'Faculty of Environmental Sciences',
                'abbreviation': 'ENV',
                'departments': [
                    {'name': 'Architecture', 'abbreviation': 'ARC'},
                    {'name': 'Building', 'abbreviation': 'BLD'},
                    {'name': 'Estate Management', 'abbreviation': 'EST'},
                    {'name': 'Geography', 'abbreviation': 'GEO'},
                    {'name': 'Urban and Regional Planning', 'abbreviation': 'URP'},
                ],
            },
            {
                'name': 'Faculty of Health Sciences',
                'abbreviation': 'HSC',
                'departments': [
                    {'name': 'Medical Laboratory Science', 'abbreviation': 'MLS'},
                    {'name': 'Nursing Sciences', 'abbreviation': 'NRS'},
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
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                    {'name': 'Marketing', 'abbreviation': 'MKT'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                ],
            },
            {
                'name': 'Faculty of Medical Sciences',
                'abbreviation': 'MED',
                'departments': [
                    {'name': 'Medicine and Surgery', 'abbreviation': 'MBS'},
                ],
            },
            {
                'name': 'Faculty of Natural Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Biochemistry', 'abbreviation': 'BCH'},
                    {'name': 'Botany', 'abbreviation': 'BOT'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Geology', 'abbreviation': 'GEO'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Microbiology', 'abbreviation': 'MCB'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                    {'name': 'Zoology', 'abbreviation': 'ZOO'},
                ],
            },
            {
                'name': 'Faculty of Pharmaceutical Sciences',
                'abbreviation': 'PHA',
                'departments': [
                    {'name': 'Pharmaceutics', 'abbreviation': 'PHA'},
                    {'name': 'Pharmacology', 'abbreviation': 'PHM'},
                    {'name': 'Pharmacognosy', 'abbreviation': 'PHG'},
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
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
                ],
            },
            {
                'name': 'Faculty of Veterinary Medicine',
                'abbreviation': 'VET',
                'departments': [
                    {'name': 'Veterinary Medicine', 'abbreviation': 'VMD'},
                    {'name': 'Veterinary Surgery', 'abbreviation': 'VSU'},
                    {'name': 'Veterinary Pathology', 'abbreviation': 'VPT'},
                ],
            },
        ],
    },
    
    # UNIVERSITY OF MAKURDI (Note: Main campus in Benue, but UNIJOS is the primary Plateau institution)
    # Added as a placeholder for completeness
    {
        'name': 'Plateau State University',
        'abbreviation': 'PLASU',
        'state': 'PLATEAU',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'Faculty of Arts',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'English', 'abbreviation': 'ENG'},
                    {'name': 'History', 'abbreviation': 'HIS'},
                    {'name': 'Christian Religious Studies', 'abbreviation': 'CRS'},
                    {'name': 'Theatre and Media Arts', 'abbreviation': 'TMA'},
                ],
            },
            {
                'name': 'Faculty of Social Sciences',
                'abbreviation': 'SOC',
                'departments': [
                    {'name': 'Economics', 'abbreviation': 'ECO'},
                    {'name': 'Political Science', 'abbreviation': 'POL'},
                    {'name': 'Sociology', 'abbreviation': 'SOC'},
                    {'name': 'Mass Communication', 'abbreviation': 'MAC'},
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
            {
                'name': 'Faculty of Natural Sciences',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Mathematics', 'abbreviation': 'MTH'},
                    {'name': 'Biology', 'abbreviation': 'BIO'},
                    {'name': 'Chemistry', 'abbreviation': 'CHM'},
                    {'name': 'Physics', 'abbreviation': 'PHY'},
                ],
            },
        ],
    },
    
    # PLATEAU STATE POLYTECHNIC
    {
        'name': 'Plateau State Polytechnic',
        'abbreviation': 'PLAPOLY',
        'state': 'PLATEAU',
        'type': 'STATE',
        'faculties': [
            {
                'name': 'School of Engineering Technology',
                'abbreviation': 'ENG',
                'departments': [
                    {'name': 'Agricultural Engineering', 'abbreviation': 'AGE'},
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
                'name': 'School of Management Studies',
                'abbreviation': 'MGT',
                'departments': [
                    {'name': 'Accountancy', 'abbreviation': 'ACC'},
                    {'name': 'Business Administration', 'abbreviation': 'BAD'},
                    {'name': 'Public Administration', 'abbreviation': 'PAD'},
                    {'name': 'Banking and Finance', 'abbreviation': 'BNF'},
                ],
            },
            {
                'name': 'School of Science and Technology',
                'abbreviation': 'SCI',
                'departments': [
                    {'name': 'Computer Science', 'abbreviation': 'CSC'},
                    {'name': 'Statistics', 'abbreviation': 'STA'},
                    {'name': 'Food Technology', 'abbreviation': 'FDT'},
                    {'name': 'Science Laboratory Technology', 'abbreviation': 'SLT'},
                ],
            },
        ],
    },
    
    # FEDERAL COLLEGE OF EDUCATION, PANKSHIN
    {
        'name': 'Federal College of Education, Pankshin',
        'abbreviation': 'FCEPANKSHIN',
        'state': 'PLATEAU',
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
                    {'name': 'Physics Education', 'abbreviation': 'PHY'},
                    {'name': 'Mathematics Education', 'abbreviation': 'MTH'},
                    {'name': 'Integrated Science Education', 'abbreviation': 'ISC'},
                ],
            },
            {
                'name': 'School of Languages',
                'abbreviation': 'LAN',
                'departments': [
                    {'name': 'English Education', 'abbreviation': 'ENG'},
                    {'name': 'French Education', 'abbreviation': 'FRN'},
                    {'name': 'Nigerian Languages Education', 'abbreviation': 'NIL'},
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
        ],
    },
    
    # COLLEGE OF EDUCATION, GINDIRI (treated as university per your instruction)
    {
        'name': 'College of Education, Gindiri',
        'abbreviation': 'COEGINDIRI',
        'state': 'PLATEAU',
        'type': 'PRIVATE',
        'faculties': [
            {
                'name': 'School of Education',
                'abbreviation': 'EDU',
                'departments': [
                    {'name': 'Early Childhood Education', 'abbreviation': 'ECE'},
                    {'name': 'Primary Education', 'abbreviation': 'PED'},
                ],
            },
            {
                'name': 'School of Arts and Social Sciences',
                'abbreviation': 'ART',
                'departments': [
                    {'name': 'Christian Religious Studies Education', 'abbreviation': 'CRS'},
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
                ],
            },
        ],
    },
]