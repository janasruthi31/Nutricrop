# STEP 1 — DATASET AUDIT (TN_Fertilizer_Combined_Pack.zip)

## Tabular files (CSV and HTML-based .xls)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/fertilizer/tn_fertilizer_prices_reference.csv
- **rows**: 9
- **cols**: 8
- **columns**: ['fertilizer_name', 'standard_bag_kg', 'price_inr_per_bag', 'N_percent', 'P2O5_percent', 'K2O_percent', 'price_reference_date', 'source_note']
- **missing_cells**: 8
- **missing_by_col**: {'price_inr_per_bag': 4, 'price_reference_date': 4}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: True
- **suitable_for_yield_ml**: NO – reference/price/rule table (belongs to the separate fertilizer module)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/fertilizer/tnau_fertilizer_prices_2026.csv
- **rows**: 15
- **cols**: 6
- **columns**: ['fertilizer_name', 'grade', 'price_unit', 'price', 'source', 'source_url']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: True
- **suitable_for_yield_ml**: NO – reference/price/rule table (belongs to the separate fertilizer module)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/reports/remaining_data_status.csv
- **rows**: 8
- **cols**: 4
- **columns**: ['requirement', 'status', 'evidence', 'use']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/rules/tnau_official_crop_nutrient_recommendations.csv
- **rows**: 23
- **cols**: 9
- **columns**: ['crop', 'state', 'area_or_scope', 'condition_or_variety', 'N_kg_per_ha', 'P2O5_kg_per_ha', 'K2O_kg_per_ha', 'source', 'source_url']
- **missing_cells**: 18
- **missing_by_col**: {'N_kg_per_ha': 5, 'P2O5_kg_per_ha': 5, 'K2O_kg_per_ha': 5, 'source_url': 3}
- **duplicate_rows**: 0
- **state_coverage**: ['Tamil Nadu']
- **tamil_nadu_coverage**: all rows Tamil Nadu (state column)
- **district_coverage**: no district column
- **crop_coverage**: 13 crops
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: True
- **suitable_for_yield_ml**: NO – reference/price/rule table (belongs to the separate fertilizer module)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/rules/tnau_stcr_equations.csv
- **rows**: 6
- **cols**: 7
- **columns**: ['crop', 'soil_series', 'N_equation', 'P2O5_equation', 'K2O_equation', 'conditions', 'source_url']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: 2 crops
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: True
- **suitable_for_yield_ml**: NO – reference/price/rule table (belongs to the separate fertilizer module)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/soil/tamil_mannvalam_soil_classification_thresholds.csv
- **rows**: 18
- **cols**: 6
- **columns**: ['parameter', 'code', 'unit', 'status', 'threshold', 'source_note']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – soil snapshot, no yield/year dimension

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/soil/tn_district_soil_fertility_status_historical.csv
- **rows**: 17
- **cols**: 10
- **columns**: ['district', 'n_low_pct', 'n_medium_pct', 'n_high_pct', 'p_low_pct', 'p_medium_pct', 'p_high_pct', 'k_low_pct', 'k_medium_pct', 'k_high_pct']
- **missing_cells**: 9
- **missing_by_col**: {'n_high_pct': 7, 'p_high_pct': 1, 'k_high_pct': 1}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 17 districts
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – soil snapshot, no yield/year dimension

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/soil/tn_numeric_soil_study_4districts.csv
- **rows**: 4
- **cols**: 12
- **columns**: ['district', 'available_n_kg_ha', 'available_p_kg_ha', 'available_k_kg_ha', 'organic_carbon_pct', 'ec_millimhos_cm', 'ph', 'cu_ppm', 'mn_ppm', 'fe_ppm', 'boron_ppm', 's_ppm']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 4 districts
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – soil snapshot, no yield/year dimension

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/soil/tn_soil_fertility_village_master.csv
- **rows**: 80
- **cols**: 13
- **columns**: ['district', 'taluk', 'revenue_village', 'nitrogen_kg_ac', 'phosphorus_kg_ac', 'potassium_kg_ac', 'soil_series', 'source_type', 'source_year_note', 'source_url', 'nitrogen_kg_ha', 'phosphorus_kg_ha', 'potassium_kg_ha']
- **missing_cells**: 106
- **missing_by_col**: {'nitrogen_kg_ac': 15, 'phosphorus_kg_ac': 23, 'potassium_kg_ac': 15, 'nitrogen_kg_ha': 15, 'phosphorus_kg_ha': 23, 'potassium_kg_ha': 15}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 2 districts
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – soil snapshot, no yield/year dimension

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/sources/source_registry.csv
- **rows**: 7
- **cols**: 5
- **columns**: ['publisher', 'dataset', 'what_available', 'source_url', 'category']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/weather/tn_weather_power_11N_77E_2025.csv
- **rows**: 365
- **cols**: 6
- **columns**: ['YEAR', 'DOY', 'T2M', 'RH2M', 'PRECTOTCORR', 'WS10M']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: 2025–2025
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: True
- **humidity_available**: True
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – single grid point (11N,77E), year 2025 only; not district-level, no yield year overlap

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/yield/tn_district_crop_area_reports_long.csv
- **rows**: 17622
- **cols**: 6
- **columns**: ['district', 'crop', 'area', 'domain', 'season', 'source_file']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 37 districts
- **crop_coverage**: 379 crops
- **year_range**: no year column
- **season_coverage**: ['Agriculture', 'Horticulture']
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – area only (no yield/production); 3 seasons of 2024-25 only

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/yield/tn_state_crop_yield_reference_2023_24_2024_25.csv
- **rows**: 12
- **cols**: 7
- **columns**: ['crop', 'year', 'area_ha', 'production_tonnes', 'yield_kg_per_ha', 'source', 'source_url']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: 6 crops
- **year_range**: 2023-24–2024-25
- **season_coverage**: no season column
- **yield_available**: True
- **production_available**: True
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – state-level, 12 rows; used only as an independent validation of extracted State rows

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/datasets_seed/01_dataset_catalog.csv
- **rows**: 37
- **cols**: 14
- **columns**: ['id', 'dataset', 'priority', 'source_name', 'official_or_derived', 'url', 'download_access', 'years_covered', 'districts', 'crops', 'rows_known', 'format', 'ml_suitable', 'notes_and_gaps']
- **missing_cells**: 4
- **missing_by_col**: {'crops': 1, 'rows_known': 1, 'notes_and_gaps': 2}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 22 districts
- **crop_coverage**: 32 crops
- **year_range**: -–Yearly
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/datasets_seed/fertilizer_composition_verified.csv
- **rows**: 15
- **cols**: 10
- **columns**: ['fertilizer_name', 'grade', 'bag_size_kg', 'N_percent', 'P2O5_percent', 'K2O_percent', 'S_percent', 'source', 'source_url', 'verification_status']
- **missing_cells**: 14
- **missing_by_col**: {'S_percent': 14}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: True
- **suitable_for_yield_ml**: NO – reference/price/rule table (belongs to the separate fertilizer module)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/datasets_seed/fertilizer_prices_current_vs_historical.csv
- **rows**: 13
- **cols**: 10
- **columns**: ['fertilizer_name', 'grade', 'bag_size_kg', 'price_per_bag_inr', 'price_date', 'price_type', 'state', 'source', 'source_url', 'note']
- **missing_cells**: 10
- **missing_by_col**: {'grade': 2, 'bag_size_kg': 2, 'price_per_bag_inr': 2, 'note': 4}
- **duplicate_rows**: 0
- **state_coverage**: ['India', 'Tamil Nadu']
- **tamil_nadu_coverage**: mixed
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: True
- **suitable_for_yield_ml**: NO – reference/price/rule table (belongs to the separate fertilizer module)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/datasets_seed/tnau_stcr_blanket_recommendations.csv
- **rows**: 8
- **cols**: 16
- **columns**: ['crop', 'variety_or_duration', 'season', 'irrigated_rainfed', 'soil_series_or_tract', 'target_yield', 'N_kg_ha', 'P2O5_kg_ha', 'K2O_kg_ha', 'FYM', 'application_stage', 'STCR_equation', 'rec_type', 'source', 'source_url', 'status']
- **missing_cells**: 26
- **missing_by_col**: {'variety_or_duration': 1, 'season': 1, 'irrigated_rainfed': 1, 'soil_series_or_tract': 1, 'target_yield': 1, 'N_kg_ha': 2, 'P2O5_kg_ha': 3, 'K2O_kg_ha': 3, 'FYM': 5, 'application_stage': 3, 'STCR_equation': 5}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: 6 crops
- **year_range**: no year column
- **season_coverage**: ['Dry season', 'Not stated', 'Wet season', 'not specified']
- **yield_available**: True
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: True
- **suitable_for_yield_ml**: NO

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/fertilizer/source_registry.csv
- **rows**: 7
- **cols**: 5
- **columns**: ['source_name', 'url', 'geographic_level', 'status', 'notes']
- **missing_cells**: 1
- **missing_by_col**: {'notes': 1}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – reference/price/rule table (belongs to the separate fertilizer module)

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/soil/source_registry.csv
- **rows**: 2
- **cols**: 5
- **columns**: ['source_name', 'url', 'status', 'how_checked', 'notes']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – soil snapshot, no yield/year dimension

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/weather/source_registry.csv
- **rows**: 2
- **cols**: 5
- **columns**: ['source_name', 'url', 'status', 'how_checked', 'notes']
- **missing_cells**: 1
- **missing_by_col**: {'url': 1}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO

### 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/yield/source_registry.csv
- **rows**: 6
- **cols**: 5
- **columns**: ['source_name', 'url', 'status', 'how_checked', 'notes']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: no district column
- **crop_coverage**: no crop column
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: False
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO

### 01_Important_Data_Files/data/District_Wise_Report_-_Agriculture_-_Kharif_2025.xls
- **rows**: 38
- **cols**: 246
- **columns**: ['District', 'Rice (Paddy)', 'Maize', 'Sorghum', 'Urdbean(Black Gram)', 'Sugarcane', 'Tapioca', 'Fodder Sorghum', 'Horse Gram', 'Groundnut', 'Diploid Cotton (Paruththi)', 'Finger Millet (Ragi)', 'Pigeon Pea (Red Gram)', 'Cowpea', 'Cassava', 'Mungbean(Green Gram)', 'Sesame', 'Field Lab-Lab', 'Napier Grass', 'Fodder Maize - African Tall Maize', 'Pearl Millet', 'Moth Bean', 'Fodder cumbu', 'Avarekalu', 'Castor', 'Tetraploid Cotton', 'Cenchrus grass', 'Puddle', 'Kodo Millet', 'Chickpea (Bengal Gram)', 'Tobacco', 'Sunflower', 'Barnyard Millet', 'Proso Millet (Pani Varugu)', 'Foxtail Millet (Thenai)', 'Sesbania', 'Karuvel', 'Sunnhemp', 'Buffalo grass', 'Manilla tamarind', 'Hundi (For Fodder)', 'Little Millet', 'Fodder Moringa', 'Fodder Cowpea', 'Guinea Grass', 'Dhaincha', 'Sugar Beet', 'Soybean', 'Barley', 'Brinjal', 'Sugar Candy', 'Sweet Potato', 'Karuvelam', 'Pea', 'Elephant grass', 'Bottle Gourd', 'Paragrass', 'Jute', 'Subabul', 'Cabbage', 'Kikuyu grass', 'Broccoli', 'Tuber', 'Grain Amaranth', 'Guarseed; Cluster Bean', 'Wheat', 'Mesta', 'Carrot', 'Ash Gourd', 'Kodo', 'Lentil', 'Cucumber', 'Brussels Sprout', 'Pillipesara', 'Bitter Gourd', 'Onion', 'Cluster Bean', 'Alfalfa', 'Khesari', 'Cauliflower', 'Dinanath Grass', 'Banana', 'Stylo Hamata', 'Portia tree', 'Beetroot', 'Buckwheat', 'Bhatt', 'Hedge Lucerne', 'Velvel', 'Okra', 'Setaria grass', 'Indian Coral Tree', 'North Indian rosewood or shisham', 'Indigo', 'Neem', 'Fodder Oats', 'Linseed', 'Makhana; Prickly Waterlily', 'Eucalyptus', 'Karan Rai', 'Teak', 'Tomato', 'Kudaivel', 'Celery', 'Casurina', 'Vegetable Amaranth', 'Bakla', 'Rapeseed', 'Sword Bean', 'Glyricidia', 'Quinoa', 'Indian Siris/ East Indian Walnut', 'Nigerseed', 'Potato', 'Radish', 'Camelina', 'Mango', 'Spinach', 'Oat', 'Safflower', 'Turmeric', 'Hariyali', 'Jatropha', 'Korai/Sonhaan', 'Pumpkin', 'Gobhi Sarson', 'Popat', 'Stylo', 'Ridge Gourd', 'Pointed Gourd', 'Coconut', 'Jackfruit', 'Yam Bean', 'Canna', 'Chilli', 'Snake Gourd', 'Shisham', 'Spiny Amaranth', 'Gilky', 'Moringa', 'Barseem', 'Congosignal', 'Chinese Mellow', 'Glory Lily', 'Mulberry', 'Acid Lime', 'Garlic', 'Lettuce', 'Broomgrass', 'Jasmine', 'Ivy Gourd', 'Coriander', 'Intellect Tree', 'Pinenut', 'Cashew', 'Chrysanthemum', 'Elephant Foot Yam', 'Oak Tree', 'Nerium', 'Ambrette Seed; Muskmallow', 'Lemon Grass', 'Poppy', 'Turnips', 'Bougainvillea', 'Indian Ebony', 'Bauhinia', 'Oil Palm', 'Curry Leaf', 'Red Vine Spinach', 'Daisy', 'Noni', 'Gladioulus', 'Rose', 'Vegetable Cowpea', 'Wild jack', 'Arecanut', 'Watermelon', 'Soapnut', 'Mangrove', 'Guava', 'Lemon', 'Walnut', 'Vetiver', 'Hella', 'Taro', 'Florida', 'Indian Gooseberry', 'Bottle Tree', 'Marigold', 'Gulmohar', 'Rayan', 'Spiny Gourd / Akakara/ Bodakakara', 'Tamarind', 'Chamba', 'Coleus', 'Senna', 'White Musli', 'Orchid', 'Acacia', 'Spinach Beet', 'Tuberose', 'False Daisy', 'Harsingar', 'Menthol Mint', 'Anthurium', 'Indian Jujube', 'Arabian Jasmine', 'Lily', 'Hibiscus', 'Madhukamini/Kunti', 'Pulasan', 'Raintree', 'Litchi', 'Roshagrass', 'Sandalwood', 'Mahogany', 'Custard Apple', 'Spinach Dock', 'Armandi', 'Palas', 'Pimparani', 'Silver Oak', 'Rubber', 'Deodar', 'Peepal', 'Seema Ruba/ Paradise Tree / Lakshmitaru', 'Arjun Tree', 'Mahua', 'Gliricidia', 'Mosami', 'Henbane', 'Kohlrabi', 'Gerbera', 'Silk cotton', 'Indian Banyan Tree', 'Coffee', 'Giloy', 'Jasmine-Kakada', 'Davana', 'Beans', 'Chew', 'Pipali; Long Pepper', 'Papaya', 'Palmyra', 'Kadamb', 'Total']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 38 districts
- **crop_coverage**: crops as columns
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – crop AREA by district for one season (no yield, no production, single season-year)
- **note**: file is an HTML table saved with .xls extension; crops are columns, values are area

### 01_Important_Data_Files/data/District_Wise_Report_-_Agriculture_-_Rabi_2024.xls
- **rows**: 38
- **cols**: 246
- **columns**: ['District', 'Rice (Paddy)', 'Maize', 'Sorghum', 'Urdbean(Black Gram)', 'Sugarcane', 'Tapioca', 'Fodder Sorghum', 'Horse Gram', 'Groundnut', 'Diploid Cotton (Paruththi)', 'Finger Millet (Ragi)', 'Pigeon Pea (Red Gram)', 'Cowpea', 'Cassava', 'Mungbean(Green Gram)', 'Sesame', 'Field Lab-Lab', 'Napier Grass', 'Fodder Maize - African Tall Maize', 'Pearl Millet', 'Moth Bean', 'Fodder cumbu', 'Avarekalu', 'Castor', 'Tetraploid Cotton', 'Cenchrus grass', 'Puddle', 'Kodo Millet', 'Chickpea (Bengal Gram)', 'Tobacco', 'Sunflower', 'Barnyard Millet', 'Proso Millet (Pani Varugu)', 'Foxtail Millet (Thenai)', 'Sesbania', 'Karuvel', 'Sunnhemp', 'Buffalo grass', 'Manilla tamarind', 'Hundi (For Fodder)', 'Little Millet', 'Fodder Moringa', 'Fodder Cowpea', 'Guinea Grass', 'Dhaincha', 'Sugar Beet', 'Soybean', 'Barley', 'Brinjal', 'Sugar Candy', 'Sweet Potato', 'Karuvelam', 'Pea', 'Elephant grass', 'Bottle Gourd', 'Paragrass', 'Jute', 'Subabul', 'Cabbage', 'Kikuyu grass', 'Broccoli', 'Tuber', 'Grain Amaranth', 'Guarseed; Cluster Bean', 'Wheat', 'Mesta', 'Carrot', 'Ash Gourd', 'Kodo', 'Lentil', 'Cucumber', 'Brussels Sprout', 'Pillipesara', 'Bitter Gourd', 'Onion', 'Cluster Bean', 'Alfalfa', 'Khesari', 'Cauliflower', 'Dinanath Grass', 'Banana', 'Stylo Hamata', 'Portia tree', 'Beetroot', 'Buckwheat', 'Bhatt', 'Hedge Lucerne', 'Velvel', 'Okra', 'Setaria grass', 'Indian Coral Tree', 'North Indian rosewood or shisham', 'Indigo', 'Neem', 'Fodder Oats', 'Linseed', 'Makhana; Prickly Waterlily', 'Eucalyptus', 'Karan Rai', 'Teak', 'Tomato', 'Kudaivel', 'Celery', 'Casurina', 'Vegetable Amaranth', 'Bakla', 'Rapeseed', 'Sword Bean', 'Glyricidia', 'Quinoa', 'Indian Siris/ East Indian Walnut', 'Nigerseed', 'Potato', 'Radish', 'Camelina', 'Mango', 'Spinach', 'Oat', 'Safflower', 'Turmeric', 'Hariyali', 'Jatropha', 'Korai/Sonhaan', 'Pumpkin', 'Gobhi Sarson', 'Popat', 'Stylo', 'Ridge Gourd', 'Pointed Gourd', 'Coconut', 'Jackfruit', 'Yam Bean', 'Canna', 'Chilli', 'Snake Gourd', 'Shisham', 'Spiny Amaranth', 'Gilky', 'Moringa', 'Barseem', 'Congosignal', 'Chinese Mellow', 'Glory Lily', 'Mulberry', 'Acid Lime', 'Garlic', 'Lettuce', 'Broomgrass', 'Jasmine', 'Ivy Gourd', 'Coriander', 'Intellect Tree', 'Pinenut', 'Cashew', 'Chrysanthemum', 'Elephant Foot Yam', 'Oak Tree', 'Nerium', 'Ambrette Seed; Muskmallow', 'Lemon Grass', 'Poppy', 'Turnips', 'Bougainvillea', 'Indian Ebony', 'Bauhinia', 'Oil Palm', 'Curry Leaf', 'Red Vine Spinach', 'Daisy', 'Noni', 'Gladioulus', 'Rose', 'Vegetable Cowpea', 'Wild jack', 'Arecanut', 'Watermelon', 'Soapnut', 'Mangrove', 'Guava', 'Lemon', 'Walnut', 'Vetiver', 'Hella', 'Taro', 'Florida', 'Indian Gooseberry', 'Bottle Tree', 'Marigold', 'Gulmohar', 'Rayan', 'Spiny Gourd / Akakara/ Bodakakara', 'Tamarind', 'Chamba', 'Coleus', 'Senna', 'White Musli', 'Orchid', 'Acacia', 'Spinach Beet', 'Tuberose', 'False Daisy', 'Harsingar', 'Menthol Mint', 'Anthurium', 'Indian Jujube', 'Arabian Jasmine', 'Lily', 'Hibiscus', 'Madhukamini/Kunti', 'Pulasan', 'Raintree', 'Litchi', 'Roshagrass', 'Sandalwood', 'Mahogany', 'Custard Apple', 'Spinach Dock', 'Armandi', 'Palas', 'Pimparani', 'Silver Oak', 'Rubber', 'Deodar', 'Peepal', 'Seema Ruba/ Paradise Tree / Lakshmitaru', 'Arjun Tree', 'Mahua', 'Gliricidia', 'Mosami', 'Henbane', 'Kohlrabi', 'Gerbera', 'Silk cotton', 'Indian Banyan Tree', 'Coffee', 'Giloy', 'Jasmine-Kakada', 'Davana', 'Beans', 'Chew', 'Pipali; Long Pepper', 'Papaya', 'Palmyra', 'Kadamb', 'Total']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 38 districts
- **crop_coverage**: crops as columns
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – crop AREA by district for one season (no yield, no production, single season-year)
- **note**: file is an HTML table saved with .xls extension; crops are columns, values are area

### 01_Important_Data_Files/data/District_Wise_Report_-_Agriculture_-_Summer_2025.xls
- **rows**: 38
- **cols**: 246
- **columns**: ['District', 'Rice (Paddy)', 'Maize', 'Sorghum', 'Urdbean(Black Gram)', 'Sugarcane', 'Tapioca', 'Fodder Sorghum', 'Horse Gram', 'Groundnut', 'Diploid Cotton (Paruththi)', 'Finger Millet (Ragi)', 'Pigeon Pea (Red Gram)', 'Cowpea', 'Cassava', 'Mungbean(Green Gram)', 'Sesame', 'Field Lab-Lab', 'Napier Grass', 'Fodder Maize - African Tall Maize', 'Pearl Millet', 'Moth Bean', 'Fodder cumbu', 'Avarekalu', 'Castor', 'Tetraploid Cotton', 'Cenchrus grass', 'Puddle', 'Kodo Millet', 'Chickpea (Bengal Gram)', 'Tobacco', 'Sunflower', 'Barnyard Millet', 'Proso Millet (Pani Varugu)', 'Foxtail Millet (Thenai)', 'Sesbania', 'Karuvel', 'Sunnhemp', 'Buffalo grass', 'Manilla tamarind', 'Hundi (For Fodder)', 'Little Millet', 'Fodder Moringa', 'Fodder Cowpea', 'Guinea Grass', 'Dhaincha', 'Sugar Beet', 'Soybean', 'Barley', 'Brinjal', 'Sugar Candy', 'Sweet Potato', 'Karuvelam', 'Pea', 'Elephant grass', 'Bottle Gourd', 'Paragrass', 'Jute', 'Subabul', 'Cabbage', 'Kikuyu grass', 'Broccoli', 'Tuber', 'Grain Amaranth', 'Guarseed; Cluster Bean', 'Wheat', 'Mesta', 'Carrot', 'Ash Gourd', 'Kodo', 'Lentil', 'Cucumber', 'Brussels Sprout', 'Pillipesara', 'Bitter Gourd', 'Onion', 'Cluster Bean', 'Alfalfa', 'Khesari', 'Cauliflower', 'Dinanath Grass', 'Banana', 'Stylo Hamata', 'Portia tree', 'Beetroot', 'Buckwheat', 'Bhatt', 'Hedge Lucerne', 'Velvel', 'Okra', 'Setaria grass', 'Indian Coral Tree', 'North Indian rosewood or shisham', 'Indigo', 'Neem', 'Fodder Oats', 'Linseed', 'Makhana; Prickly Waterlily', 'Eucalyptus', 'Karan Rai', 'Teak', 'Tomato', 'Kudaivel', 'Celery', 'Casurina', 'Vegetable Amaranth', 'Bakla', 'Rapeseed', 'Sword Bean', 'Glyricidia', 'Quinoa', 'Indian Siris/ East Indian Walnut', 'Nigerseed', 'Potato', 'Radish', 'Camelina', 'Mango', 'Spinach', 'Oat', 'Safflower', 'Turmeric', 'Hariyali', 'Jatropha', 'Korai/Sonhaan', 'Pumpkin', 'Gobhi Sarson', 'Popat', 'Stylo', 'Ridge Gourd', 'Pointed Gourd', 'Coconut', 'Jackfruit', 'Yam Bean', 'Canna', 'Chilli', 'Snake Gourd', 'Shisham', 'Spiny Amaranth', 'Gilky', 'Moringa', 'Barseem', 'Congosignal', 'Chinese Mellow', 'Glory Lily', 'Mulberry', 'Acid Lime', 'Garlic', 'Lettuce', 'Broomgrass', 'Jasmine', 'Ivy Gourd', 'Coriander', 'Intellect Tree', 'Pinenut', 'Cashew', 'Chrysanthemum', 'Elephant Foot Yam', 'Oak Tree', 'Nerium', 'Ambrette Seed; Muskmallow', 'Lemon Grass', 'Poppy', 'Turnips', 'Bougainvillea', 'Indian Ebony', 'Bauhinia', 'Oil Palm', 'Curry Leaf', 'Red Vine Spinach', 'Daisy', 'Noni', 'Gladioulus', 'Rose', 'Vegetable Cowpea', 'Wild jack', 'Arecanut', 'Watermelon', 'Soapnut', 'Mangrove', 'Guava', 'Lemon', 'Walnut', 'Vetiver', 'Hella', 'Taro', 'Florida', 'Indian Gooseberry', 'Bottle Tree', 'Marigold', 'Gulmohar', 'Rayan', 'Spiny Gourd / Akakara/ Bodakakara', 'Tamarind', 'Chamba', 'Coleus', 'Senna', 'White Musli', 'Orchid', 'Acacia', 'Spinach Beet', 'Tuberose', 'False Daisy', 'Harsingar', 'Menthol Mint', 'Anthurium', 'Indian Jujube', 'Arabian Jasmine', 'Lily', 'Hibiscus', 'Madhukamini/Kunti', 'Pulasan', 'Raintree', 'Litchi', 'Roshagrass', 'Sandalwood', 'Mahogany', 'Custard Apple', 'Spinach Dock', 'Armandi', 'Palas', 'Pimparani', 'Silver Oak', 'Rubber', 'Deodar', 'Peepal', 'Seema Ruba/ Paradise Tree / Lakshmitaru', 'Arjun Tree', 'Mahua', 'Gliricidia', 'Mosami', 'Henbane', 'Kohlrabi', 'Gerbera', 'Silk cotton', 'Indian Banyan Tree', 'Coffee', 'Giloy', 'Jasmine-Kakada', 'Davana', 'Beans', 'Chew', 'Pipali; Long Pepper', 'Papaya', 'Palmyra', 'Kadamb', 'Total']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 38 districts
- **crop_coverage**: crops as columns
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – crop AREA by district for one season (no yield, no production, single season-year)
- **note**: file is an HTML table saved with .xls extension; crops are columns, values are area

### 01_Important_Data_Files/data/District_Wise_Report_-_Horticultural_-_Kharif_2025.xls
- **rows**: 38
- **cols**: 326
- **columns**: ['District', 'Coconut', 'Mango', 'Banana', 'Cashew', 'Tea', 'Rubber', 'Onion', 'Chilli', 'Turmeric', 'Arecanut', 'Moringa', 'Coffee', 'Tamarind', 'Tomato', 'Palmyra', 'Guava', 'Brinjal', 'Carrot', 'Okra', 'Jackfruit', 'Black Pepper', 'Watermelon', 'Lemon', 'Acid Lime', 'Mulberry', 'Indian Gooseberry', 'Sapota', 'Cluster Bean', 'Elephant Foot Yam', 'Coriander', 'Grapes', 'Papaya', 'Menthol Mint', 'Cabbage', 'Small Cardamom', 'Pumpkin', 'Korai/Sonhaan', 'Chow Chow', 'Curry Leaf', 'Bitter Gourd', 'Potato', 'Cloves', 'Oil Palm', 'Bottle Gourd', 'Beetroot', 'Cucumber', 'Garlic', 'Betelvine', 'Radish', 'Sword Bean', 'Green chillies', 'Vegetable Amaranth', 'Tuber', 'Large Cardamon', 'Cauliflower', 'Snake Gourd', 'Ridge Gourd', 'Ivy Gourd', 'Beans', 'Avocado', 'Cocoa', 'Pineapple', 'Ash Gourd', 'Japanese Plum', 'Taro', 'Bamboo', 'Jamun', 'Red Sandalwood', 'Pipali; Long Pepper', 'Agaththi', 'Sweet Orange', 'Sugar Candy', 'Vetiver', 'Yam Bean', 'Bhedus', 'Date Palm', 'Pomegranate', 'Sandalwood', 'Spinach', 'Custard Apple', 'Lemon Grass', 'Indian Basil', 'Senna', 'Greater Yam', 'Almond', 'Pear', 'Broccoli', 'Vegtable Cowpea', 'Spiny Amaranth', 'Dragon Fruit', 'Periwinkle', 'Fenugreek', 'Colocasia', 'Ginger', 'Rose Geranium', 'Melia', 'Tapioca', 'Indian Jujube', 'Fig', 'Indian Mustard', 'Lettuce', 'Kohlrabi', 'Iceberg', 'Prune', 'Popat', 'Turnips', 'Peach', 'Muskmelon', 'Brussels Sprout', 'Teak', 'Jamarosa; Palmarosa', 'Jasmine', 'Spiny Gourd / Akakara/ Bodakakara', 'Chinese cabbage', 'Davana', 'Red Vine Spinach', 'Asparagus', 'Pinenut', 'Roshagrass', 'Pulasan', 'Khasi Kateri; Yellow- Barried Nightshade', 'Noni', 'Neem', 'Javacitronilla', 'Eucalyptus', 'Green Chillies', 'Sorghum', 'White Musli', 'Casurina', 'Liquorice', 'Water Chestnut', 'Indian Trumpet Tree', 'Rice (Paddy)', 'Manila Tamarind', 'Canna', 'Caraway', 'Chamomile', 'Mangosteen', 'Chinese potato', 'Maruvu/ Marjoram', 'Maize', 'Celery', 'Apple', 'Black Berry', 'Pointed Gourd', 'Cassava', 'Capsicum', 'Gilky', 'Kiwifruit; Chinese Gooseberry; Woody Vine', 'Giant Swamp Taro', 'Silver Oak', 'Bay Leaves', 'Chinese Mellow', 'Chew', 'Rose', 'Sal Tree', 'Ashwagandha', 'Tuberose', 'Damask Rose', 'Ajwain', 'Spinach Beet', 'Greenpeas', 'Mandarin', 'Blueberry', 'Cumin', 'Land Amulki', 'Apricot', 'Mangrove', 'Spinach Dock', 'Passion Fruit; Purple Granadilla', 'Indian Tree Spurge', 'Hibiscus', 'Jatamaansee', 'Chrysanthemum', 'Shatavari', 'Chironji', 'Black Stone Flower', 'Strawberry', 'Beheda', 'Aloe Vera', 'Athalaikai', 'Cherry', 'Orchid', 'Manila Tamarind.1', 'Glory Lily', 'Arabian Jasmine', 'Saffron', 'Rosemary', 'Marigold', 'Stevia', 'Chirata', 'Panineer Chamba', 'Oak Tree', 'Zuchinni', 'Esfand', 'Calla Lily', 'Atees', 'Coleus', 'Avarekalu', 'Seabuchthorn', 'Haritaki', 'Iron Wood', 'Henbane', 'Vegetable Cowpea', 'Kalmegh', 'Cinnamon', 'Sugarcane', 'Parsley', 'Gherkins', 'Kolumichai, Kaffir lime', 'Nutmeg', 'Kokum', 'Intellect Tree', 'Finger Millet (Ragi)', 'Mahogany', 'Fennel', 'Sweet Potato', 'chinese potato', 'Vanilla', 'Nagkeshar', 'Karvand', 'Foxtail Millet (Thenai)', 'Pea', 'Fodder Moringa', 'Elephant Apple', "Bullock'S Heart", 'Grain Amaranth', 'Dill', 'Shevri', 'Little Millet', 'Acacia', 'Chamba', 'Jafra / Annatto', 'Cowpea', 'Marvel', 'Pomelo', 'Napier Grass', 'Sine', 'Groundnut', 'Karanj', 'Mullai', 'Crossandra', 'Mesta', 'Nigella', 'Pearl Millet', 'Hundi (For Fodder)', 'Macau', 'Sunnhemp', 'Peruvian Lily', 'Sindhi Tree', 'Isabgol', 'Kadamb', 'Sesame', 'Pigeon Pea (Red Gram)', 'Nigerseed', 'Guinea Grass', 'Hella', 'Ashoka', 'Urdbean(Black Gram)', 'False Daisy', 'Gudmar', 'Fodder Sorghum', 'Fodder Cowpea', 'Poppy', 'Kewda', 'Manilla tamarind', 'Barnyard Millet', 'Seema Ruba/ Paradise Tree / Lakshmitaru', 'Castor', 'Gliricidia', 'Ambrette Seed; Muskmallow', 'Nerium', 'Horse Gram', 'Paragrass', 'Cenchrus grass', 'Diploid Cotton (Paruththi)', 'Wheat', 'Stonewall', 'Arjun Tree', 'Rauvolfia; Serpentine', 'Field Lab-Lab', 'Kodo', 'Jasmine-Kakada', 'Anantamul', 'Butch', 'Indian Banyan Tree', 'Litchi', 'Bauhinia', 'Sesbania', 'Proso Millet (Pani Varugu)', 'Mungbean(Green Gram)', 'Tobacco', 'Chir Pine', 'Daisy', 'Florida', 'Tetraploid Cotton', 'Wood Apple', 'Carnation', 'Guarseed; Cluster Bean', 'Indigo', 'Brahmi', 'Anthurium', 'Bottle Tree', 'Indian Coral Tree', 'Wild jack', 'Gulmohar', 'Peepal', 'Mosami', 'Soybean', 'Giloy', 'Heena', 'Barley', 'Poplar', 'Alfalfa', 'Willow', 'Puddle', 'Dhaincha', 'Stylo', 'Subabul', 'Hingani', 'Buckwheat', 'Jathi Malli (PITCHI)', 'Dinanath Grass', 'Patchouli', 'Total']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 38 districts
- **crop_coverage**: crops as columns
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – crop AREA by district for one season (no yield, no production, single season-year)
- **note**: file is an HTML table saved with .xls extension; crops are columns, values are area

### 01_Important_Data_Files/data/District_Wise_Report_-_Horticultural_-_Rabi_2024.xls
- **rows**: 38
- **cols**: 326
- **columns**: ['District', 'Coconut', 'Mango', 'Banana', 'Cashew', 'Tea', 'Rubber', 'Onion', 'Chilli', 'Turmeric', 'Arecanut', 'Moringa', 'Coffee', 'Tamarind', 'Tomato', 'Palmyra', 'Guava', 'Brinjal', 'Carrot', 'Okra', 'Jackfruit', 'Black Pepper', 'Watermelon', 'Lemon', 'Acid Lime', 'Mulberry', 'Indian Gooseberry', 'Sapota', 'Cluster Bean', 'Elephant Foot Yam', 'Coriander', 'Grapes', 'Papaya', 'Menthol Mint', 'Cabbage', 'Small Cardamom', 'Pumpkin', 'Korai/Sonhaan', 'Chow Chow', 'Curry Leaf', 'Bitter Gourd', 'Potato', 'Cloves', 'Oil Palm', 'Bottle Gourd', 'Beetroot', 'Cucumber', 'Garlic', 'Betelvine', 'Radish', 'Sword Bean', 'Green chillies', 'Vegetable Amaranth', 'Tuber', 'Large Cardamon', 'Cauliflower', 'Snake Gourd', 'Ridge Gourd', 'Ivy Gourd', 'Beans', 'Avocado', 'Cocoa', 'Pineapple', 'Ash Gourd', 'Japanese Plum', 'Taro', 'Bamboo', 'Jamun', 'Red Sandalwood', 'Pipali; Long Pepper', 'Agaththi', 'Sweet Orange', 'Sugar Candy', 'Vetiver', 'Yam Bean', 'Bhedus', 'Date Palm', 'Pomegranate', 'Sandalwood', 'Spinach', 'Custard Apple', 'Lemon Grass', 'Indian Basil', 'Senna', 'Greater Yam', 'Almond', 'Pear', 'Broccoli', 'Vegtable Cowpea', 'Spiny Amaranth', 'Dragon Fruit', 'Periwinkle', 'Fenugreek', 'Colocasia', 'Ginger', 'Rose Geranium', 'Melia', 'Tapioca', 'Indian Jujube', 'Fig', 'Indian Mustard', 'Lettuce', 'Kohlrabi', 'Iceberg', 'Prune', 'Popat', 'Turnips', 'Peach', 'Muskmelon', 'Brussels Sprout', 'Teak', 'Jamarosa; Palmarosa', 'Jasmine', 'Spiny Gourd / Akakara/ Bodakakara', 'Chinese cabbage', 'Davana', 'Red Vine Spinach', 'Asparagus', 'Pinenut', 'Roshagrass', 'Pulasan', 'Khasi Kateri; Yellow- Barried Nightshade', 'Noni', 'Neem', 'Javacitronilla', 'Eucalyptus', 'Green Chillies', 'Sorghum', 'White Musli', 'Casurina', 'Liquorice', 'Water Chestnut', 'Indian Trumpet Tree', 'Rice (Paddy)', 'Manila Tamarind', 'Canna', 'Caraway', 'Chamomile', 'Mangosteen', 'Chinese potato', 'Maruvu/ Marjoram', 'Maize', 'Celery', 'Apple', 'Black Berry', 'Pointed Gourd', 'Cassava', 'Capsicum', 'Gilky', 'Kiwifruit; Chinese Gooseberry; Woody Vine', 'Giant Swamp Taro', 'Silver Oak', 'Bay Leaves', 'Chinese Mellow', 'Chew', 'Rose', 'Sal Tree', 'Ashwagandha', 'Tuberose', 'Damask Rose', 'Ajwain', 'Spinach Beet', 'Greenpeas', 'Mandarin', 'Blueberry', 'Cumin', 'Land Amulki', 'Apricot', 'Mangrove', 'Spinach Dock', 'Passion Fruit; Purple Granadilla', 'Indian Tree Spurge', 'Hibiscus', 'Jatamaansee', 'Chrysanthemum', 'Shatavari', 'Chironji', 'Black Stone Flower', 'Strawberry', 'Beheda', 'Aloe Vera', 'Athalaikai', 'Cherry', 'Orchid', 'Manila Tamarind.1', 'Glory Lily', 'Arabian Jasmine', 'Saffron', 'Rosemary', 'Marigold', 'Stevia', 'Chirata', 'Panineer Chamba', 'Oak Tree', 'Zuchinni', 'Esfand', 'Calla Lily', 'Atees', 'Coleus', 'Avarekalu', 'Seabuchthorn', 'Haritaki', 'Iron Wood', 'Henbane', 'Vegetable Cowpea', 'Kalmegh', 'Cinnamon', 'Sugarcane', 'Parsley', 'Gherkins', 'Kolumichai, Kaffir lime', 'Nutmeg', 'Kokum', 'Intellect Tree', 'Finger Millet (Ragi)', 'Mahogany', 'Fennel', 'Sweet Potato', 'chinese potato', 'Vanilla', 'Nagkeshar', 'Karvand', 'Foxtail Millet (Thenai)', 'Pea', 'Fodder Moringa', 'Elephant Apple', "Bullock'S Heart", 'Grain Amaranth', 'Dill', 'Shevri', 'Little Millet', 'Acacia', 'Chamba', 'Jafra / Annatto', 'Cowpea', 'Marvel', 'Pomelo', 'Napier Grass', 'Sine', 'Groundnut', 'Karanj', 'Mullai', 'Crossandra', 'Mesta', 'Nigella', 'Pearl Millet', 'Hundi (For Fodder)', 'Macau', 'Sunnhemp', 'Peruvian Lily', 'Sindhi Tree', 'Isabgol', 'Kadamb', 'Sesame', 'Pigeon Pea (Red Gram)', 'Nigerseed', 'Guinea Grass', 'Hella', 'Ashoka', 'Urdbean(Black Gram)', 'False Daisy', 'Gudmar', 'Fodder Sorghum', 'Fodder Cowpea', 'Poppy', 'Kewda', 'Manilla tamarind', 'Barnyard Millet', 'Seema Ruba/ Paradise Tree / Lakshmitaru', 'Castor', 'Gliricidia', 'Ambrette Seed; Muskmallow', 'Nerium', 'Horse Gram', 'Paragrass', 'Cenchrus grass', 'Diploid Cotton (Paruththi)', 'Wheat', 'Stonewall', 'Arjun Tree', 'Rauvolfia; Serpentine', 'Field Lab-Lab', 'Kodo', 'Jasmine-Kakada', 'Anantamul', 'Butch', 'Indian Banyan Tree', 'Litchi', 'Bauhinia', 'Sesbania', 'Proso Millet (Pani Varugu)', 'Mungbean(Green Gram)', 'Tobacco', 'Chir Pine', 'Daisy', 'Florida', 'Tetraploid Cotton', 'Wood Apple', 'Carnation', 'Guarseed; Cluster Bean', 'Indigo', 'Brahmi', 'Anthurium', 'Bottle Tree', 'Indian Coral Tree', 'Wild jack', 'Gulmohar', 'Peepal', 'Mosami', 'Soybean', 'Giloy', 'Heena', 'Barley', 'Poplar', 'Alfalfa', 'Willow', 'Puddle', 'Dhaincha', 'Stylo', 'Subabul', 'Hingani', 'Buckwheat', 'Jathi Malli (PITCHI)', 'Dinanath Grass', 'Patchouli', 'Total']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 38 districts
- **crop_coverage**: crops as columns
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – crop AREA by district for one season (no yield, no production, single season-year)
- **note**: file is an HTML table saved with .xls extension; crops are columns, values are area

### 01_Important_Data_Files/data/District_Wise_Report_-_Horticultural_-_Summer_2025.xls
- **rows**: 38
- **cols**: 326
- **columns**: ['District', 'Coconut', 'Mango', 'Banana', 'Cashew', 'Tea', 'Rubber', 'Onion', 'Chilli', 'Turmeric', 'Arecanut', 'Moringa', 'Coffee', 'Tamarind', 'Tomato', 'Palmyra', 'Guava', 'Brinjal', 'Carrot', 'Okra', 'Jackfruit', 'Black Pepper', 'Watermelon', 'Lemon', 'Acid Lime', 'Mulberry', 'Indian Gooseberry', 'Sapota', 'Cluster Bean', 'Elephant Foot Yam', 'Coriander', 'Grapes', 'Papaya', 'Menthol Mint', 'Cabbage', 'Small Cardamom', 'Pumpkin', 'Korai/Sonhaan', 'Chow Chow', 'Curry Leaf', 'Bitter Gourd', 'Potato', 'Cloves', 'Oil Palm', 'Bottle Gourd', 'Beetroot', 'Cucumber', 'Garlic', 'Betelvine', 'Radish', 'Sword Bean', 'Green chillies', 'Vegetable Amaranth', 'Tuber', 'Large Cardamon', 'Cauliflower', 'Snake Gourd', 'Ridge Gourd', 'Ivy Gourd', 'Beans', 'Avocado', 'Cocoa', 'Pineapple', 'Ash Gourd', 'Japanese Plum', 'Taro', 'Bamboo', 'Jamun', 'Red Sandalwood', 'Pipali; Long Pepper', 'Agaththi', 'Sweet Orange', 'Sugar Candy', 'Vetiver', 'Yam Bean', 'Bhedus', 'Date Palm', 'Pomegranate', 'Sandalwood', 'Spinach', 'Custard Apple', 'Lemon Grass', 'Indian Basil', 'Senna', 'Greater Yam', 'Almond', 'Pear', 'Broccoli', 'Vegtable Cowpea', 'Spiny Amaranth', 'Dragon Fruit', 'Periwinkle', 'Fenugreek', 'Colocasia', 'Ginger', 'Rose Geranium', 'Melia', 'Tapioca', 'Indian Jujube', 'Fig', 'Indian Mustard', 'Lettuce', 'Kohlrabi', 'Iceberg', 'Prune', 'Popat', 'Turnips', 'Peach', 'Muskmelon', 'Brussels Sprout', 'Teak', 'Jamarosa; Palmarosa', 'Jasmine', 'Spiny Gourd / Akakara/ Bodakakara', 'Chinese cabbage', 'Davana', 'Red Vine Spinach', 'Asparagus', 'Pinenut', 'Roshagrass', 'Pulasan', 'Khasi Kateri; Yellow- Barried Nightshade', 'Noni', 'Neem', 'Javacitronilla', 'Eucalyptus', 'Green Chillies', 'Sorghum', 'White Musli', 'Casurina', 'Liquorice', 'Water Chestnut', 'Indian Trumpet Tree', 'Rice (Paddy)', 'Manila Tamarind', 'Canna', 'Caraway', 'Chamomile', 'Mangosteen', 'Chinese potato', 'Maruvu/ Marjoram', 'Maize', 'Celery', 'Apple', 'Black Berry', 'Pointed Gourd', 'Cassava', 'Capsicum', 'Gilky', 'Kiwifruit; Chinese Gooseberry; Woody Vine', 'Giant Swamp Taro', 'Silver Oak', 'Bay Leaves', 'Chinese Mellow', 'Chew', 'Rose', 'Sal Tree', 'Ashwagandha', 'Tuberose', 'Damask Rose', 'Ajwain', 'Spinach Beet', 'Greenpeas', 'Mandarin', 'Blueberry', 'Cumin', 'Land Amulki', 'Apricot', 'Mangrove', 'Spinach Dock', 'Passion Fruit; Purple Granadilla', 'Indian Tree Spurge', 'Hibiscus', 'Jatamaansee', 'Chrysanthemum', 'Shatavari', 'Chironji', 'Black Stone Flower', 'Strawberry', 'Beheda', 'Aloe Vera', 'Athalaikai', 'Cherry', 'Orchid', 'Manila Tamarind.1', 'Glory Lily', 'Arabian Jasmine', 'Saffron', 'Rosemary', 'Marigold', 'Stevia', 'Chirata', 'Panineer Chamba', 'Oak Tree', 'Zuchinni', 'Esfand', 'Calla Lily', 'Atees', 'Coleus', 'Avarekalu', 'Seabuchthorn', 'Haritaki', 'Iron Wood', 'Henbane', 'Vegetable Cowpea', 'Kalmegh', 'Cinnamon', 'Sugarcane', 'Parsley', 'Gherkins', 'Kolumichai, Kaffir lime', 'Nutmeg', 'Kokum', 'Intellect Tree', 'Finger Millet (Ragi)', 'Mahogany', 'Fennel', 'Sweet Potato', 'chinese potato', 'Vanilla', 'Nagkeshar', 'Karvand', 'Foxtail Millet (Thenai)', 'Pea', 'Fodder Moringa', 'Elephant Apple', "Bullock'S Heart", 'Grain Amaranth', 'Dill', 'Shevri', 'Little Millet', 'Acacia', 'Chamba', 'Jafra / Annatto', 'Cowpea', 'Marvel', 'Pomelo', 'Napier Grass', 'Sine', 'Groundnut', 'Karanj', 'Mullai', 'Crossandra', 'Mesta', 'Nigella', 'Pearl Millet', 'Hundi (For Fodder)', 'Macau', 'Sunnhemp', 'Peruvian Lily', 'Sindhi Tree', 'Isabgol', 'Kadamb', 'Sesame', 'Pigeon Pea (Red Gram)', 'Nigerseed', 'Guinea Grass', 'Hella', 'Ashoka', 'Urdbean(Black Gram)', 'False Daisy', 'Gudmar', 'Fodder Sorghum', 'Fodder Cowpea', 'Poppy', 'Kewda', 'Manilla tamarind', 'Barnyard Millet', 'Seema Ruba/ Paradise Tree / Lakshmitaru', 'Castor', 'Gliricidia', 'Ambrette Seed; Muskmallow', 'Nerium', 'Horse Gram', 'Paragrass', 'Cenchrus grass', 'Diploid Cotton (Paruththi)', 'Wheat', 'Stonewall', 'Arjun Tree', 'Rauvolfia; Serpentine', 'Field Lab-Lab', 'Kodo', 'Jasmine-Kakada', 'Anantamul', 'Butch', 'Indian Banyan Tree', 'Litchi', 'Bauhinia', 'Sesbania', 'Proso Millet (Pani Varugu)', 'Mungbean(Green Gram)', 'Tobacco', 'Chir Pine', 'Daisy', 'Florida', 'Tetraploid Cotton', 'Wood Apple', 'Carnation', 'Guarseed; Cluster Bean', 'Indigo', 'Brahmi', 'Anthurium', 'Bottle Tree', 'Indian Coral Tree', 'Wild jack', 'Gulmohar', 'Peepal', 'Mosami', 'Soybean', 'Giloy', 'Heena', 'Barley', 'Poplar', 'Alfalfa', 'Willow', 'Puddle', 'Dhaincha', 'Stylo', 'Subabul', 'Hingani', 'Buckwheat', 'Jathi Malli (PITCHI)', 'Dinanath Grass', 'Patchouli', 'Total']
- **missing_cells**: 0
- **missing_by_col**: {}
- **duplicate_rows**: 0
- **state_coverage**: no state column
- **tamil_nadu_coverage**: Tamil Nadu-specific by source (no state column)
- **district_coverage**: 38 districts
- **crop_coverage**: crops as columns
- **year_range**: no year column
- **season_coverage**: no season column
- **yield_available**: False
- **production_available**: False
- **rainfall_available**: True
- **temperature_available**: False
- **humidity_available**: False
- **fertilizer_available**: False
- **suitable_for_yield_ml**: NO – crop AREA by district for one season (no yield, no production, single season-year)
- **note**: file is an HTML table saved with .xls extension; crops are columns, values are area

## Non-tabular files (not auto-parsed; PDFs inspected selectively)

**PDF** (18 files)
- 01_Important_Data_Files/data/02_02.pdf
- 01_Important_Data_Files/data/02_04.pdf
- 01_Important_Data_Files/data/02_05.pdf
- 01_Important_Data_Files/data/02_06.pdf
- 01_Important_Data_Files/data/02_07.pdf
- 01_Important_Data_Files/data/02_08.pdf
- 01_Important_Data_Files/data/2.pdf
- 01_Important_Data_Files/data/MicronutrientMaps.pdf
- 01_Important_Data_Files/data/S&C 2014-15 -1-compressed.pdf
- 01_Important_Data_Files/data/S&C 2015-16_2-compressed.pdf
- 01_Important_Data_Files/data/S&C 201819.pdf
- 01_Important_Data_Files/data/SCR  201718 .pdf
- 01_Important_Data_Files/data/SCR 2016-17.pdf
- 01_Important_Data_Files/data/SCR 2020-21.pdf
- 01_Important_Data_Files/data/SCR 2021-22.pdf
- 01_Important_Data_Files/data/SCR2022-23.pdf
- 01_Important_Data_Files/data/SCR2024-25.pdf
- 01_Important_Data_Files/data/SRC2023-24.pdf

**HTM** (1 files)
- 01_Important_Data_Files/data/rainfall_statistics_3.htm

**MD** (8 files)
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/README.md
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/collected_data/README_collected_data.md
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/02_DATA_COLLECTION_PLAN.md
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/README_plan_and_catalog.md
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/references.md
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/FINAL_DATA_COLLECTION_REPORT.md
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/fertilizer/fertilizer_type_data_gap_report.md
- COMBINED_PACK_ASSESSMENT.md

**TXT** (1 files)
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/yield/source_urls.txt

**PY** (7 files)
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/scripts/build_crop_weather_join.py
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/scripts/check_urls.py
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/scripts/download_imd_grid.py
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/plan_and_catalog/scripts/download_nasa_power.py
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/scripts/filter_datagov_tn.py
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/scripts/weather_nasa_power.py
- 02_Complete_Pack/TN_Fertilizer_Complete_Pack/remaining_data_kit/scripts/yield_pipeline.py

**JSON** (0 files)

